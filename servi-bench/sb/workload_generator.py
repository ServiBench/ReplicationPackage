from pathlib import Path
import os
import numpy as np
import pandas as pd
from stochastic.processes.continuous import FractionalBrownianMotion
import stochastic


class WorkloadGenerator:

    workload_type_to_file_map = {
        'bursty': 'bursty.csv',
        'steady': 'steady.csv',
        'jump': 'jump.csv',
        'spikes': 'spikes.csv'
    }

    def __init__(self, workload_type, scale_factor=1, scale_type='linear', workload_trace=None,
                 seconds_to_skip=3 * 60):
        self.workload_type = workload_type
        self.workload_trace_file = None
        self.seconds_to_skip = seconds_to_skip
        # Seed random number generator for stochastic library
        self.rng_seed = int(os.getenv('SB_WORKLOADGEN_SEED', 42))
        stochastic.random.seed(self.rng_seed)
        # Special workload types single or any (positive) number
        if workload_type == 'single' or (str(workload_type).isnumeric() and int(workload_type) > 0):
            pass
        # Default workload traces supported by sb
        elif workload_type in WorkloadGenerator.workload_type_to_file_map:
            self.workload_trace_file = Path(__file__).parent.parent / 'data' / 'workload_traces' / '20min_20rps' / WorkloadGenerator.workload_type_to_file_map[workload_type]  # noqa E501
        # Custom csv file with per minute invocation rates
        elif workload_trace and WorkloadGenerator.is_existing_csv_file(workload_trace):
            self.workload_trace_file = Path(workload_trace)
        else:
            msg = 'Unknown workload type passed to workload generator: ' + str(workload_type)
            raise Exception(msg)
        self.scale_factor = scale_factor
        self.scale_type = scale_type

    def is_existing_csv_file(path) -> bool:
        p = Path(path)
        return p.suffix == '.csv' and p.is_file()

    def generate_trace(self) -> dict:
        """Returns a k6 options dictionary: https://k6.io/docs/using-k6/options"""
        if self.workload_type == 'single':
            return self.default_options()
        elif str(self.workload_type).isnumeric():
            iterations = int(self.workload_type)
            return self.default_options(iterations)
        else:
            per_second_rates = self.upscale_trace(self.workload_trace_file, self.scale_factor, self.scale_type)  # noqa E501
            # Skip the first 3 minutes to fix bootstrapping issue if trace is long enough.
            if len(per_second_rates) > self.seconds_to_skip:
                # Every trace starts from 0 rps at t=0 and then oscillates the first few minutes
                # causing unnatural spikes.
                # Skipping the first 3 minutes discards this unnatural warmup phase.
                per_second_rates_skip_start = per_second_rates[self.seconds_to_skip:]
                return self.encode_for_k6(per_second_rates_skip_start)
            else:
                return self.encode_for_k6(per_second_rates)

    def default_options(self, iterations=1) -> dict:
        options = {
            'vus': 1,
            'iterations': iterations
        }
        return options

    def upscale_trace(self, per_minute_rates_file_path, scale_factor=1, scale_type='linear'):
        per_minute_rates_arr = pd.read_csv(per_minute_rates_file_path)['InvocationsPerMinute'].values  # noqa E501

        bm = FractionalBrownianMotion(hurst=0.8, t=10)
        magnitude_multiplier = 100  # Need to increase magnitude or values become too small
        samples = bm.sample(60 * len(per_minute_rates_arr)) * magnitude_multiplier
        all_bm_samples = samples + np.abs(np.floor(samples.min()))

        per_second_rates = np.array([])
        for i in range(len(per_minute_rates_arr)):
            current_rate_minute = per_minute_rates_arr[i]
            bm_samples = all_bm_samples[i * 60:(i + 1) * 60]

            # Scale random samples by actual request rate per minute
            total_units = bm_samples.sum()
            requests_per_unit = current_rate_minute / total_units
            upscaled_samples = bm_samples * requests_per_unit

            per_second_rates = np.append(per_second_rates, upscaled_samples)

        scaled_per_second_rates = None
        if scale_type == 'linear':
            scaled_per_second_rates = per_second_rates * scale_factor
        elif scale_type == 'compound':
            # Use compounding to scale
            compounding_fractions = per_second_rates / per_second_rates.sum()
            max_fraction = np.quantile(compounding_fractions, 0.95)
            # Find exponent required to scale the maximum requests per second by the scale_factor
            exponent = np.log(scale_factor) / np.log(1 + max_fraction)
            scaled_per_second_rates = per_second_rates * np.power(1 + compounding_fractions, exponent)  # noqa E501
            # Clip extremes
            clip_threshold = np.quantile(scaled_per_second_rates, 0.95)
            scaled_per_second_rates[scaled_per_second_rates > clip_threshold] = clip_threshold
        else:
            raise Exception(f'Unknown scaling type: {scale_type}')

        return np.round(scaled_per_second_rates)

    def encode_for_k6(self, per_second_rates) -> dict:
        # Run length encoding merges contiguous seconds with the same request rate
        n = len(per_second_rates)
        element_does_not_match_prev = per_second_rates[1:] != per_second_rates[:-1]
        positions_where_element_does_not_match = np.append(np.where(element_does_not_match_prev), n - 1)  # noqa E501
        run_lengths = np.diff(np.append(-1, positions_where_element_does_not_match))
        key_elements = per_second_rates[positions_where_element_does_not_match]
        pre_allocated_vus = int(np.ceil(np.max(per_second_rates) / 10))
        start_rate = 0
        if len(key_elements) > 0:
            start_rate = int(key_elements[0])

        stage_list = []
        for i in range(len(key_elements)):
            duration_in_seconds = int(run_lengths[i])
            target = int(key_elements[i])
            # Split longer stages than 1s to model sharp transitions
            # instead of linearly ramping up/down.
            # Skip splitting for first stage and use startRate instead.
            if duration_in_seconds > 1 and i > 0:
                stage_list.append({
                    'target': target,
                    'duration': '1s'
                })
                stage_list.append({
                    'target': target,
                    'duration': str(duration_in_seconds - 1) + 's'
                })
            else:
                stage_list.append({
                    'target': target,
                    'duration': str(duration_in_seconds) + 's'
                })

        # reference for this object:
        # https://k6.io/docs/using-k6/scenarios/executors/ramping-arrival-rate
        config_object = {
            'scenarios': {
                'benchmark_scenario': {
                    'executor': 'ramping-arrival-rate',
                    'startRate': start_rate,
                    'timeUnit': '1s',
                    'preAllocatedVUs': pre_allocated_vus,
                    'stages': stage_list
                }
            }
        }

        return config_object
