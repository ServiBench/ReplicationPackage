"""Provides a library of importing and pre-processing utilities to analyze datasets from sb experiments.
Usage: from sb_importer import *
Configuration:
* data_path: path to the location of the dataset
* lg_name: directory of the the dataset (used to distinguish data from multiple sources)
"""

# %% Imports
from pathlib import Path, PurePath
from dateutil.parser import parse
from datetime import timedelta
import yaml
import json
import logging
import sys
import math
import pandas as pd
import numpy as np
from functools import reduce
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw
import ast
import fnmatch

from plotnine import *

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# %% Configure data source
data_path = Path.home() / 'Datasets/serverless-study/data'
lg_name = 'lg12'
plots_root_path = data_path.parent / 'plots' / lg_name
workload_rates_dir = data_path / 'workload_traces'
apps_path = data_path / lg_name / 'ec2-user'
# Mapping of app shortname to path in alphabetical order
apps = {
    'event_processing': 'faas-migration/Event-Processing/Lambda/event_processing_benchmark.py',
    'hello_retail': 'hello-retail/hello_retail_benchmark.py',
    'image_processing': 'aws-serverless-workshops/ImageProcessing/image_processing_benchmark.py',
    'matrix_multiplication': 'faas-migration/MatrixMultiplication/Lambda/matrix_multiplication_benchmark.py',
    'model_training': 'serverless-faas-workbench/aws/cpu-memory/model_training/model_training_benchmark.py',
    'realworld_backend': 'realworld-dynamodb-lambda/realworld_benchmark.py',
    'thumbnail_generator': 'faas-migration/ThumbnailGenerator/Lambda/thumbnail_benchmark.py',
    'todo_api': 'faas-migration-go/aws/todo_api_benchmark.py',
    'video_processing': 'serverless-faas-workbench/aws/cpu-memory/video_processing/video_processing_benchmark.py',
    'apigw_node': 'serverless-patterns/apigw-lambda-cdk/src/apigw_node_benchmark.py'
}
# Manual order of apps based on dominate time category
app_order = [
    # blank
    'apigw_node',
    # compute
    'matrix_multiplication',
    'model_training',
    'video_processing',
    # external service
    'image_processing',
    'realworld_backend',
    'hello_retail',
    'event_processing',
    'todo_api',
    # trigger
    'thumbnail_generator',
]
# Latency breakdown time categories in specific order
categories = [
    'computation',
    'external_service',
    'orchestration',
    'trigger',
    'queing',
    'overhead',
    'runtime_initialization',
    'container_initialization',
    # 'unclassified'
]

# %% Apps iteration helper

def plots_path(app_name=None) -> Path:
    plots_path = plots_root_path
    if app_name:
        plots_path = plots_root_path / app_name
    plots_path.mkdir(exist_ok=True, parents=True)
    return plots_path

def find_execution_paths(apps_path, app_source):
    """Returns a list of paths to logs directories of a given app.
    * apps_path: path where all applications reside
    * app_source: path to the *_benchmark.py file of an app.
    """
    app_logs_path = apps_path / Path(app_source).parent / 'logs'
    # Skip apps without any executions
    if not app_logs_path.is_dir():
        logging.debug(f"No logs directory for app {app_source}.")
        return []
    # Execution log directories are in the datetime format 2021-04-30_01-09-33
    execution_paths = [x for x in app_logs_path.iterdir() if x.is_dir()]
    return execution_paths

def get_workload_label(app_config) -> str:
    """Returns a human-readable label of the kind of workload used."""
    workload_type = app_config.get('workload_type', None)
    workload_trace = app_config.get('workload_trace', None)
    if workload_type and workload_type != 'custom':
        return workload_type
    elif workload_trace:
        return PurePath(workload_trace).name
    else:
        return ''


# %% Helpers from sb: event_log.py

def decode_event(event_string):
    event = event_string.split(',')
    event_time = parse(event[0])
    event_name = event[1]
    event_type = event[2]
    return (event_time, event_name, event_type)

def event_duration(events, name):
    """Returns the duration of the last event with the given name
    or None if no matching start and end timestamps exist.
    Example: event_duration('invoke')."""
    # scan events backwards for matching end and start times
    end_time = None
    start_time = None
    for event_string in reversed(events):
        event_time, event_name, event_type = decode_event(event_string)
        if event_name == name:
            if event_type == 'end':
                end_time = event_time
            elif event_type == 'start':
                start_time = event_time
                # found matching end-start pair
                if end_time:
                    return end_time - start_time
                # start_time without matching end_time:
                # either in progress or aborted
                # else:
                #     return None
    return None

# %% Read import methods

def read_sb_app_config(execution):
    """Returns a dictionary with the parsed sb config from sb_config.yml"""
    config_path = execution / 'sb_config.yml'
    sb_config = {}
    app_config = {}
    app_name = ''
    if config_path.is_file():
        with open(config_path) as f:
            sb_config = yaml.load(f, Loader=yaml.FullLoader)
        app_name = list(sb_config.keys())[0]
        # Workaround for cases where sb is the first key
        if app_name == 'sb':
            app_name = list(sb_config.keys())[1]
        app_config = sb_config[app_name]
    else:
        logging.warning(f"Config file missing at {config_path}.")
        return dict()
    return app_config, app_name

def read_trace_breakdown(execution) -> pd.DataFrame:
    """Returns a pandas dataframe with the parsed trace_breakdown.csv"""
    trace_breakdown_path = execution / 'trace_breakdown.csv'
    converters = {
        # Parsing list of strings though json
        'longest_path_names': lambda x: ast.literal_eval(x)
    }
    trace_breakdown = pd.read_csv(trace_breakdown_path, converters=converters)

    # See categories in sb code under aws_trace_analyzer.py:CSV_FIELDS
    timedelta_columns = [
        'duration',
        'orchestration',
        'trigger',
        'container_initialization',
        'runtime_initialization',
        'computation',
        'queing',
        'overhead',
        'external_service',
        'unclassified'
    ]
    # Parse timedelta and datetime fields
    trace_breakdown[timedelta_columns] = trace_breakdown[timedelta_columns].apply(pd.to_timedelta)
    trace_breakdown['start_time_ts'] = pd.to_datetime(trace_breakdown['start_time'], unit='s')
    # start_time in epoc time (millisecond precision with 3 digits after the period dot)
    start = trace_breakdown['start_time'].min()
    # Identify start and end times
    trace_breakdown['relative_time'] = trace_breakdown['start_time'] - start
    trace_breakdown = trace_breakdown.sort_values(by=['relative_time'])
    return trace_breakdown

def read_invalid_traces(execution) -> pd.DataFrame:
    invalid_traces_path = execution / 'invalid_traces.csv'
    invalid_traces = pd.read_csv(invalid_traces_path)
    return invalid_traces

def remove_starting_zero_ips(df, ips_col) -> pd.DataFrame:
    """Remove 0 ips targets at the start because we assume that t=0 seconds matches with the first request"""
    if df is None:
        return None
    offset_seconds = next((i for i, ips in enumerate(df[ips_col]) if ips != 0), 0)
    if offset_seconds > 0:
        logging.debug(f"Remove {offset_seconds} seconds with target rate of 0 ips.")
        df.drop(df.index[:offset_seconds], inplace=True)
        df = df.reset_index(drop=True)
        df['relative_time'] = df.index
    return df

def read_workload_options(execution) -> pd.DataFrame:
    """Returns a pandas frame with per-second invocation rates
    parsed from k6 workload options."""
    workload_options_path = execution / 'workload_options.json'
    with open(workload_options_path) as json_file:
        workload_options = json.load(json_file)
        ips_col = 'workload_options_ips'
        parsed = parse_workload_options_ips(workload_options, ips_col)
        return remove_starting_zero_ips(parsed, ips_col)

def parse_workload_options_ips(workload_options, ips_col = 'workload_options_ips') -> pd.DataFrame:
    """Returns a data frame with invocations per second (workload_options_ips)
    parsed from k6 workload options. Removes any leading 0 ips.
    Caveat: limited support for needed scenarios:
    * mainly supporting ramping-arrival-time
    * time units seconds (s), minutes (m), and partially milliseconds (ms)
    """
    # No scenarios
    if not 'scenarios' in workload_options:
        return None
    # Unsupported scenarios. By convention, sb generates a `benchmark_scenario`
    # but custom experiment plans can use other scenarios we don't support here.
    if not 'benchmark_scenario' in workload_options['scenarios']:
        return None
    stages = workload_options['scenarios']['benchmark_scenario']['stages']
    workload_df = pd.DataFrame.from_dict(stages, orient='columns')
    # Expand target-duration pairs into invocations per second
    rows = []
    time_in_seconds = 0
    for duration, target in zip(workload_df['duration'], workload_df['target']):
        if len(duration.split('ms')) > 1:
            ms_split = duration.split('ms')
            num_milliseconds = int(ms_split[0])
            # NOTE: Only support 1ms|999ms splits by taking the value for 1ms!
            if num_milliseconds == 1:
                rows.append([time_in_seconds, target])
                time_in_seconds += 1
        elif len(duration.split('s')) > 1:
            s_split = duration.split('s')
            num_seconds = int(s_split[0])
            for _ in range(num_seconds):
                rows.append([time_in_seconds, target])
                time_in_seconds += 1
        elif len(duration.split('m')) > 1:
            min_split = duration.split('m')
            num_minutes = int(min_split[0])
            for _ in range(num_minutes * 60):
                rows.append([time_in_seconds, target])
                time_in_seconds += 1
        else:
            raise NotImplementedError('Workload options parsing only supports durations in seconds (s), minutes (m), and partially milliseconds (ms) by taking the first 1ms.')
    # Create df from row list
    cols = ['relative_time', ips_col]
    df = pd.DataFrame(rows, columns=cols)
    parsed_workload_options = df[cols]
    return parsed_workload_options

def read_workload_rates(app_config) -> pd.DataFrame or None:
    workload_type = app_config.get('workload_type', None)
    workload_trace = app_config.get('workload_trace', None)
    workload_rates_path = None
    # Detect workload trace path suffix from the last to path parts
    # Example: /home/ec2-user/20min_20rps/steady.csv => 20min_20rps/steady.csv
    # NOTE: Can be null when using an inline config via experiment plan
    if workload_trace and workload_trace != 'null':
        workload_trace_path = Path(workload_trace)
        workload_rates_path = workload_rates_dir / workload_trace_path.parent.name / workload_trace_path.name
    # NOTE: workload_type can be numeric when used with simple iterations (e.g., sb invoke 4)
    elif workload_type and workload_type != 'custom' and type(workload_type) != int:
        workload_rates_path = workload_rates_dir / '20min_20rps' / f"{workload_type}.csv"
    # Abort if no path could be detected (e.g., fully custom workload)
    if not workload_rates_path:
        return None

    workload_rates_sec = parse_workload_rates_ips(workload_rates_path)
    ips_col = 'workload_rates_ips'
    workload_rates_sec = remove_starting_zero_ips(workload_rates_sec, ips_col)
    return workload_rates_sec

def parse_workload_rates_ips(workload_rates_path, ips_col = 'workload_rates_ips') -> pd.DataFrame:
    workload_rates_min = pd.read_csv(workload_rates_path)
    workload_rates_min[ips_col] = workload_rates_min['InvocationsPerMinute'] / 60
    workload_rates_sec = workload_rates_min.append([workload_rates_min] * 59).sort_index()
    workload_rates_sec['relative_time'] = workload_rates_sec.reset_index().index
    return workload_rates_sec

def read_k6_metrics(execution) -> pd.DataFrame:
    k6_metrics_path = execution / 'k6_metrics.csv'
    # NOTE: can lead to mixed type warning
    # sys:1: DtypeWarning: Columns (4) have mixed types.Specify dtype option on import or set low_memory=False.
    k6_metrics = pd.read_csv(k6_metrics_path)
    return k6_metrics

def read_k6_invocations(execution) -> pd.DataFrame:
    k6_metrics = read_k6_metrics(execution)
    k6_invocations = k6_metrics[k6_metrics.metric_name.eq('http_req_duration')].copy()
    # Parse trace_id from extra_tags (assumes single extra tag with XRay header)
    k6_invocations['trace_id'] = k6_invocations['extra_tags'].map(lambda tags: tags.replace('xray_header=Root=', ''))
    # timestamp in epoc time (second precison)
    start = k6_invocations['timestamp'].min()
    k6_invocations['relative_time'] = k6_invocations['timestamp'] - start
    return k6_invocations

def get_distance(df, variable_x, variable_y):
    """Returns the approximate DTW using fastdtw
    or None if any variable is missing in the df.
    * Github: https://github.com/slaypni/fastdtw
    * Reference: Stan Salvador, and Philip Chan. "FastDTW: Toward accurate dynamic time warping in linear time and space." Intelligent Data Analysis 11.5 (2007): 561-580.
    """
    x = df[df['variable'] == variable_x]['invocations_per_second']
    y = df[df['variable'] == variable_y]['invocations_per_second']
    # Remove potential NaN at the end due to a few missing data points
    x = x[~np.isnan(x)]
    y = y[~np.isnan(y)]
    # Return None instead of distance 0 if variable is missing
    if len(x) == 0 or len(y) == 0:
        return None
    distance, _ = fastdtw(x, y, dist=euclidean)
    return distance

def get_logs_path(execution) -> Path:
    # TODO: parametrize hard-coded apps_path
    # Alternative implementation based on app_path would be more flexible:
    # app_path = faas-migration/ThumbnailGenerator/Lambda/thumbnail_generator.py
    # execution = /Users/anonymous/Documents/Datasets/serverless-study/data/lg7/ec2-user/faas-migration/ThumbnailGenerator/Lambda/logs/2021-08-30_09-34-20
    # => faas-migration/ThumbnailGenerator/Lambda/logs/2021-08-30_09-34-20
    # execution =  /Users/anonymous/Documents/Datasets/serverless-study/data/lg7/ec2-user/faas-migration/ThumbnailGenerator/logs/2021-08-30_09-34-20
    # => faas-migration/ThumbnailGenerator/logs/2021-08-30_09-34-20
    try:
        # NOTE: apps_path is defined in sb_importer.py and dependent on lg_name
        return execution.relative_to(apps_path)
    except ValueError:
        logging.warning(f"Could not find relative path. Check apps_path={apps_path}.")
        return ''

def generate_summary(execution, app_config, app_name, workload_rates, workload_options, k6_invocations, trace_breakdown, invalid_traces) -> pd.DataFrame:
    summary = {}
    # Experiment and app
    summary['label'] = app_config.get('label', '')
    summary['app_name'] = app_name
    summary['app_path'] = apps.get(app_name, '')
    summary['logs_path'] = get_logs_path(execution)
    # Experiment timing from sb event log
    sb_event_log = app_config.get('sb_event_log', [])
    summary['prepare_duration'] = event_duration(sb_event_log, 'prepare')
    summary['invoke_duration'] = event_duration(sb_event_log, 'invoke')
    # Deployment and provider
    summary['region'] = app_config.get('region', '')
    summary['provider'] = app_config.get('provider', '')
    summary['workload_type'] = app_config.get('workload_type', '')
    summary['workload_trace'] = app_config.get('workload_trace', '')
    summary['scale_type'] = app_config.get('scale_type', '')
    summary['scale_factor'] = app_config.get('scale_factor', '')
    # Number of requests, traces, and error rates
    summary['k6_invocations_start_time'] = k6_invocations['timestamp'].min()  # s-precision
    summary['trace_breakdown_start_time'] = trace_breakdown['start_time'].min()  # ms-precision
    summary['sent_requests'] = len(k6_invocations)
    summary['valid_traces'] = len(trace_breakdown)
    summary['invalid_traces'] = len(invalid_traces)
    summary['received_requests'] = summary['valid_traces'] + summary['invalid_traces']
    invalid_rate = 0 if summary['received_requests'] == 0 else round(summary['invalid_traces'] / summary['received_requests'], 2)
    summary['invalid_rate'] = invalid_rate
    summary['missing_requests'] = summary['sent_requests'] - summary['received_requests']
    missing_rate = 0 if summary['sent_requests'] == 0 else round(summary['missing_requests'] / summary['sent_requests'], 2)
    summary['missing_rate'] = missing_rate
    # trace_breakdown: errors, faults, throttles
    summary['client_errors'] = len(trace_breakdown[trace_breakdown['errors']>0])
    summary['throttles'] = len(trace_breakdown[trace_breakdown['throttles']>0])
    summary['server_faults'] = len(trace_breakdown[trace_breakdown['faults']>0])
    summary['success_traces'] = len(trace_breakdown[(trace_breakdown['errors']==0) & (trace_breakdown['throttles']==0) & (trace_breakdown['faults']==0)])
    summary['error_traces'] = summary['valid_traces'] - summary['success_traces']
    error_rate = 100 if summary['valid_traces'] == 0 else round(summary['error_traces'] / summary['valid_traces'], 2)
    summary['error_rate'] = error_rate
    # Compute relevant summary stats
    summary['trace_duration_p50_ms'] = 0 if trace_breakdown['duration'].empty else round(trace_breakdown['duration'].median().total_seconds() * 1000, 3)
    summary['trace_duration_mean_ms'] = 0 if trace_breakdown['duration'].empty else round(trace_breakdown['duration'].mean().total_seconds() * 1000, 3)
    summary['http_req_duration_p50_ms'] = round(k6_invocations['metric_value'].median(), 3)
    summary['http_req_duration_mean_ms'] = round(k6_invocations['metric_value'].mean(), 3)

    # Compute the longest relative experiment time among all data frames
    data_frames = [workload_rates, workload_options, k6_invocations, trace_breakdown]
    relative_time_max = [d['relative_time'].max() for d in data_frames if d is not None]
    summary['relative_time_duration_seconds'] = round(max(relative_time_max), 2)
    # Compute effective invocation rate
    summary['target_invocations_per_second'] = app_config.get('load_level', '')
    summary['actual_invocations_per_second'] = 0 if summary['relative_time_duration_seconds'] == 0 else round(summary['sent_requests'] / summary['relative_time_duration_seconds'], 2)
    # Estimate concurrency
    summary['http_concurrency'] = round(summary['actual_invocations_per_second'] * summary['http_req_duration_mean_ms'] / 1000, 2)
    summary['trace_concurrency'] = round(summary['actual_invocations_per_second'] * summary['trace_duration_mean_ms'] / 1000, 2)
    # Invocation rate validation (i.e., compare ips of different stages)
    k6_invocations_grouped = group_by_relative_time(k6_invocations, 'k6_invocations_ips')
    if not trace_breakdown.empty:
        trace_breakdown_grouped = group_by_relative_time(trace_breakdown, 'trace_breakdown_ips')
        # Merge ips data frames
        ips_dfs = [workload_rates, workload_options, k6_invocations_grouped, trace_breakdown_grouped]
        df_long = merge_by_relative_time(ips_dfs)
        summary['rates_to_options_dtw'] = get_distance(df_long, 'workload_rates_ips', 'workload_options_ips')
        summary['options_to_k6_dtw'] = get_distance(df_long, 'workload_options_ips', 'k6_invocations_ips')
        summary['k6_to_traces_dtw'] = get_distance(df_long, 'k6_invocations_ips', 'trace_breakdown_ips')
    summary_df = pd.DataFrame(summary, index=[0])
    return summary_df

def save_summary(summary_df, execution):
    summary_path = execution / 'summary.csv'
    summary_df.to_csv(summary_path, index=False)

def group_by_relative_time(df, name='invocations_per_second') -> pd.DataFrame:
    """Groups a data frame (e.g., trace)breakdown, k6_invocations) into 1s bins by relative time."""
    end = math.ceil(df['relative_time'].max())
    start_end_range = np.arange(0, end, 1)
    labels = np.arange(0, end-1, 1)  # one fewer than the number of bin edges
    relative_time_bins = pd.cut(df['relative_time'], start_end_range, labels=labels, include_lowest=True)
    df_grouped = df.groupby(relative_time_bins)['relative_time'].count()
    df_grouped = df_grouped.reset_index(level=0, drop=True).reset_index()
    df_grouped.rename(columns={"relative_time": name, "index": "relative_time"}, inplace=True)
    return df_grouped

def group_by_duration_and_relative_time(trace_breakdown) -> pd.DataFrame:
    """Groups trace_breakdown by duration per 1s bins"""
    # Identify rounded start time
    start_time = trace_breakdown['start_time_ts'].min().floor('1s')
    # Group by time frequency using pd.Grouper (e.g., per second)
    time_grouping = pd.Grouper(key='start_time_ts', freq='1s')
    # Percentiles
    # trace_breakdown_grouped = trace_breakdown.groupby(['duration', time_grouping])['duration'].quantile([0.5, 0.95]).reset_index()
    # trace_breakdown_grouped = trace_breakdown_grouped.rename(columns={'level_2': 'percentiles'})
    # Average
    trace_breakdown_grouped = trace_breakdown.groupby(['duration', time_grouping])['duration'].mean(numeric_only=False).reset_index(level=0, drop=True).reset_index()
    trace_breakdown_grouped['relative_time'] = (trace_breakdown_grouped['start_time_ts'] - start_time).apply(timedelta.total_seconds)
    return trace_breakdown_grouped

def group_by_cold_starts_and_relative_time(trace_breakdown, name='counts') -> pd.DataFrame:
    """Groups trace_breakdown by num_cold_starts per 1s bins."""
    # Identify rounded start time
    start_time = trace_breakdown['start_time_ts'].min().floor('1s')
    # Group by time frequency using pd.Grouper (e.g., per second)
    time_grouping = pd.Grouper(key='start_time_ts', freq='1s')
    trace_breakdown_grouped = trace_breakdown.groupby(['num_cold_starts', time_grouping]).size().reset_index(name=name)
    trace_breakdown_grouped['relative_time'] = trace_breakdown_grouped['start_time_ts'] - start_time

    # Attempt to manually group by creating and assigning labels for the range 0.0 to x seconds
    # This approach creates a valid graph but using discrete data creates a label for each second, however, we need labels from a continuous scale
    # end = trace_breakdown['relative_time'].max()
    # start_end_range = np.arange(0, end, 1)
    # labels = np.arange(0, end-1, 1)  # one fewer than the number of bin edges
    # relative_time_bins = pd.cut(trace_breakdown['relative_time'], start_end_range, labels=labels, include_lowest=True)
    # trace_breakdown_grouped = trace_breakdown.groupby(['num_cold_starts', relative_time_bins]).size().reset_index(name='counts')
    # return trace_breakdown_grouped
    return trace_breakdown_grouped

def group_by_time_category_and_relative_time(trace_breakdown_long, name='latency') -> pd.DataFrame:
    """Groups unpivoted trace_breakdown by time breakdown categories (e.g., computation time) per 1s bins."""
    # Identify rounded start time
    start_time = trace_breakdown_long['start_time_ts'].min().floor('1s')
    # Group by time frequency using pd.Grouper (e.g., per second)
    time_grouping = pd.Grouper(key='start_time_ts', freq='1s')
    trace_breakdown_grouped = trace_breakdown_long.groupby(['variable', time_grouping]).mean(numeric_only=False).reset_index()
    trace_breakdown_grouped['relative_time'] = trace_breakdown_grouped['start_time_ts'] - start_time
    return trace_breakdown_grouped

def unpivot_trace_breakdown_to_time_category(trace_breakdown) -> pd.DataFrame:
    # Identify percentiles
    trace_breakdown['p95'] = trace_breakdown['duration'] > trace_breakdown['duration'].quantile(0.95)
    trace_breakdown['p99'] = trace_breakdown['duration'] > trace_breakdown['duration'].quantile(0.99)
    # Unpivot from wide to long
    long = pd.melt(trace_breakdown, id_vars=['trace_id', 'start_time', 'start_time_ts', 'num_cold_starts', 'p95', 'p99'], value_vars=categories)
    long['latency'] = long['value'].fillna(pd.Timedelta(seconds=0))
    return long

def max_diff(numbers_list):
    """Returns the largest numerical difference between any two elements.
    Example: max_diff([88,89,90])==2"""
    min_val = min(numbers_list)
    max_val = max(numbers_list)
    return max_val - min_val

def merge_by_relative_time(data_frames, value_vars=None) -> pd.DataFrame:
    """Merges multiple data frames by relative time assuming that the first request is at t=0 seconds.
    Automatically discards data frames passed as None and matches value_var column names based on the number of data frames.
    data_frames: ordered list of data frames for workload_rates (optional), workload_options (optional), k6_invocations_grouped, trace_breakdown_grouped
    value_vars (optional): custom variable names for pd.melt
    """
    # Remove None values from data frames
    filtered_data_frames = [df for df in data_frames if df is not None]
    # Derive list of columns based on the number of available data frames assuming a fixed order
    num_dfs = len(filtered_data_frames)
    default_value_vars = ['workload_rates_ips', 'workload_options_ips', 'k6_invocations_ips', 'trace_breakdown_ips']
    # Parameter takes precedence if available, otherwise derive from default by taking last N elements
    filtered_value_vars = value_vars or default_value_vars[-num_dfs:]
    # Compare length of data frames
    data_frame_lengths = [len(d) for d in filtered_data_frames]
    # Allow a few seconds difference before logging warning
    max_diff_margin = 5
    if max_diff(data_frame_lengths) > max_diff_margin:
        logging.warning(
            f"The length of relative_time from the different sources differs: {data_frame_lengths}. "
            "Check for errors that might cause 0 ips at the beginning of the experiment because we assume "
            "that the first request defines t=0 seconds."
        )
    df_merged = reduce(lambda  left,right: pd.merge(left,right,on=['relative_time'], how='outer'), filtered_data_frames)
    df_long = pd.melt(df_merged, id_vars='relative_time', value_vars=filtered_value_vars, var_name='variable', value_name='invocations_per_second')
    return df_long

def merge_traces_by_id(trace_breakdown, invalid_traces) -> pd.DataFrame:
    received_traces = pd.concat([trace_breakdown, invalid_traces], ignore_index=True)
    return received_traces

def filter_and_reorder_categories(ordered_categories, df, column):
    """Filters a df by a list of ordered_categories and re-orders them for a given column."""
    # Filter
    df = df[df[column].isin(ordered_categories)]
    # Reorder
    df[column] = df[column].astype('category')
    categories_used_ordered = get_categories_used_ordered(ordered_categories, df[column])
    df[column] = df[column].cat.reorder_categories(categories_used_ordered)
    return df

def get_categories_used_ordered(ordered_categories, used_categories) -> list:
    """Returns an ordered list of categories that appear in used_categories.
    * ordered_categories: manually defined ordered list
    * used_categories: a list or set of categories actually used in the data frame
    """
    used_set = set(ordered_categories).intersection(set(used_categories))
    # Sets don't preserve the order, therefore we need to re-construct a list based on the ordered categories.
    return [cat for cat in ordered_categories if cat in used_set]


def add_coldstart_status(all_apps):
    """Introduce coldstart_status (warm, cold, partial) per app_request_type.
    The maximal number of coldstarts differ by each request type.
    """
    grouped_cols = all_apps.groupby(['app_request_type']).agg(
        max_cold_starts=('num_cold_starts', max)
    )
    all_apps = pd.merge(all_apps, grouped_cols, on=['app_request_type'], how='inner')
    conditions = [
        (all_apps['num_cold_starts'] == 0),
        (all_apps['num_cold_starts'] == all_apps['max_cold_starts']),
        (all_apps['num_cold_starts'] > 0) & (all_apps['num_cold_starts'] < all_apps['max_cold_starts'])
    ]
    values = ['warm', 'cold', 'partial']
    all_apps['coldstart_status'] = np.select(conditions, values)
    return all_apps


def fuzzy_match(actual_path, path_pattern) -> bool:
    """Returns true if the path_pattern matches the actual_path.
    Fuzzy matching support `*` as wildcard for dynamic path names.
    Removes initialization segments to ignore cold starts.
    Example: fuzzy_match(['API', 'fun-123'], ['API', 'fun-*']) == True
    Limitations:
    a) Retries will appear as different paths because 'Attempt #1' etc introduces extra nodes.
    """
    actual_path_no_cold = [n for n in actual_path if n != 'Initialization']
    if len(actual_path_no_cold) != len(path_pattern):
        return False
    for name, pattern in zip(actual_path_no_cold, path_pattern):
        if not fnmatch.fnmatch(name, pattern):
            return False
    return True

def request_type(app, url, method, longest_path_names):
    """Mapping method with heuristics to identify different request types for common sb apps.
    """
    # NOTE: Most likely caused by a disconnected trace (i.e., 2nd part of non-HTTP-triggered trace)
    if type(url) == float:
        return 'NaN'
    if app == 'apigw_node':
        if url:
            return 'getPath'
    if app == 'event_processing':
        # NOTE: depending on the event data, a different flow is triggered
        # NOTE: Disconnected trace needs to be merged (NaN traces without url are the 2nd trace part)
        if url.endswith('/ingest'):
            return 'ingestEvent'
            # return 'ingestTemperatureEvent|ingestForecastEvent|ingestStateChangeEvent'
    elif app == 'hello_retail':
        # NOTE: depends on data (maybe app diagram / unique trace path could help)
        # NOTE: Disconnected trace needs to be merged (NaN traces without url are the 2nd trace part)
        # Disconnected traces do not help to distinguish request type :(
        if url.endswith('/event-writer'):
            return 'registerPhotographer|newProduct'
        elif url.endswith('/sms'):
            return 'commitPhoto'
        # WARNING: Load increases with more categories
        elif url.endswith('/categories'):
            return 'listCategories'
        elif '/products?category=' in url:
            return 'listProductsByCategory'
        elif '/products?id=' in url:
            return 'listProductsByID'
    elif app == 'image_processing' and url.endswith('/execute/'):
        # Depending on the image, either face or non-face, a different flow is triggered
        # NOTE: There are 5 less common flows (10s, few 100s) and 14 exceptional flows (1-5 instances) out of ~30k traces
        # Queryable by: df[df['request_type']=='postImage'].groupby(['longest_path_names']).agg({'trace_id': 'nunique'})
        face_img_success_pattern = ['APIGatewayToStepFunctions/execute', 'STEPFUNCTIONS', 'RiderPhotoProcessing-*', 'FaceDetection', 'Lambda', 'wildrydes-FaceDetectionFunction-*', 'wildrydes-FaceDetectionFunction-*', 'Invocation', 'rekognition', 'rekognition', 'Overhead', 'CheckFaceDuplicate', 'Lambda', 'wildrydes-FaceSearchFunction-*', 'wildrydes-FaceSearchFunction-*', 'Invocation', 'rekognition', 'rekognition', 'Overhead', 'ParallelProcessing', 'Branch ?', 'Thumbnail', 'Lambda', 'wildrydes-ThumbnailFunction-*', 'wildrydes-ThumbnailFunction-*', 'Invocation', 'S3', 'S3', 'S3', 'S3', 'Overhead', 'PersistMetadata', 'Lambda', 'wildrydes-PersistMetadataFunction-*', 'wildrydes-PersistMetadataFunction-*', 'Invocation', 'DynamoDB', 'DynamoDB', 'Overhead']
        non_face_img_success_pattern = ['APIGatewayToStepFunctions/execute', 'STEPFUNCTIONS', 'RiderPhotoProcessing-*', 'FaceDetection', 'Lambda', 'wildrydes-FaceDetectionFunction-*', 'wildrydes-FaceDetectionFunction-*', 'Invocation', 'rekognition', 'rekognition', 'Overhead', 'PhotoDoesNotMeetRequirement', 'Lambda', 'wildrydes-NotificationPlaceholderFunction-*', 'wildrydes-NotificationPlaceholderFunction-*', 'Invocation', 'Overhead']
        if fuzzy_match(longest_path_names, face_img_success_pattern):
            return 'postFaceImage'
        elif fuzzy_match(longest_path_names, non_face_img_success_pattern):
            return 'postNonFaceImage'
        else:
            return 'postImage'
    elif app == 'matrix_multiplication':
        if url.endswith('/run'):
            return 'multiplyMatrix'
    elif app == 'model_training':
        if url.endswith('/train'):
            return 'trainModel'
    elif app == 'video_processing':
        if url.endswith('/process'):
            return 'processVideo'
    elif app == 'realworld_backend':
        if url.endswith('/users'):
            return 'createUser'
        elif url.endswith('/login'):
            return 'loginUser'
        elif method == 'GET' and url.endswith('/user'):
            return 'getUser'
        elif method == 'PUT' and url.endswith('/user'):
            return 'updateUser'
        elif method == 'GET' and '/api/profiles/' in url:
            return 'getProfile'
        elif method == 'POST' and url.endswith('/follow'):
            return 'followUser'
        elif method == 'DELETE' and url.endswith('/follow'):
            return 'unfollowUser'
        elif method == 'POST' and url.endswith('/articles'):
            return 'createArticle'
        elif method == 'GET' and '/api/articles/' in url:
            return 'getArticle'
        elif method == 'PUT' and '/api/articles/' in url:
            return 'updateArticle'
        elif method == 'DELETE' and '/api/articles/' in url:
            return 'deleteArticle'
        elif method == 'POST' and url.endswith('/favorite'):
            return 'favoriteArticle'
        elif method == 'DELETE' and url.endswith('/favorite'):
            return 'unfavoriteArticle'
        # WARNING: Load increases with more articles
        elif method == 'GET' and '/api/articles?author=' in url:
            return 'listArticlesByAuthor'
        # WARNING: Load increases (probably) with more articles
        elif url.endswith('/articles/feed'):
            return 'getArticlesFeed'
        elif url.endswith('/tags'):
            return 'getTags'
        elif method == 'POST' and url.endswith('/comments'):
            return 'createComment'
        # WARNING: Load increases (slightly) with more comments per article
        elif method == 'GET' and url.endswith('/comments'):
            return 'getComments'
        elif method == 'DELETE' and '/comments/' in url:
            return 'deleteComment'
    elif app == 'thumbnail_generator':
        if ('/upload?') in url:
            return 'uploadImage'
    elif app == 'todo_api':
        if '/del?id=' in url:
            return 'deleteTodo'
        elif url.endswith('/put'):
            return 'createTodo'
        # WARNING: Load increases with more todos
        elif url.endswith('/lst'):
            return 'listTodos'
        elif '/get?id=' in url:
            return 'getTodo'
        elif '/done?id' in url:
            return 'markTodoAsDone'
    return 'unmatched'

# %%
