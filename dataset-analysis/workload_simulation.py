# %% Imports
import pandas as pd
from pathlib import Path
from plotnine import *

# HACK: WorkloadGenerator copied from sb repo:
# https://github.com/anonymous/serverless-benchmarker/blob/master/sb/workload_generator.py
# After a public release, we could import sb as pip package
from lib.workload_generator import WorkloadGenerator

from sb_importer import parse_workload_options_ips, parse_workload_rates_ips
from functools import reduce

# %% Configuration

plots_path = Path.home() / 'Downloads'

# original archetypical picks
choice = '20min_min1rps'
# selected for approx. similar request rate. Non-optimal choice because:
# * spike: only 1 at the beginning that gets cut as part of the 3 min warmup time
# * jump: goes down but it's more common to have jumps up
# * fluctuating: steadily increases load over time (ok to have)
# choice = '20min_20rps'
# choice = '60min_72rps'  # longer scenario (only steady + fluctuating)

pwd = Path(__file__).parent.resolve()
workload_path = pwd / 'data/workload_traces' / choice
# workload_path = Path.home() / 'Datasets/serverless-study/data/workload_traces' / choice
workload_types = [
    'steady',
    'fluctuating',
    'spikes',
    'jump'
]

# %% Import and merge
dfs = dict()
for workload in workload_types:
    path = workload_path / f"{workload}.csv"
    # Read raw trace
    workload_rates_ips = parse_workload_rates_ips(path)
    # Generate workload
    workload_type='custom'
    scale_factor=1
    scale_type='linear'
    workload_trace=path
    seconds_to_skip=0
    generator = WorkloadGenerator(workload_type, scale_factor, scale_type, workload_trace, seconds_to_skip)
    workload_dict = generator.generate_trace()
    workload_options_ips = parse_workload_options_ips(workload_dict)
    data_frames = [workload_rates_ips, workload_options_ips]
    df_merged = reduce(lambda  left,right: pd.merge(left,right,on=['relative_time'], how='outer'), data_frames)
    dfs[workload] = df_merged


# Merge data frames from different workload types
df = pd.concat(dfs.values(), keys=dfs.keys(), names=['workload_type']).reset_index()
# Transform to long format
df_long = pd.melt(df, id_vars=['relative_time', 'workload_type'], value_vars=['workload_rates_ips', 'workload_options_ips'])


# %% Demonstrate Workload generator
# NOTE: The first 3 minutes have target rate 0 but could instead just be removed from the experiment because it's just waiting time
# generator = WorkloadGenerator('custom', 1, 'linear', workload_trace)
# workload_dict = generator.generate_trace()
# workload_dict

# %% Workload types grouped together

# We ignore the first 3 minutes to alleviate the bootstrapping problem of the trace upscaler
start_to_ignore = 3 * 60
p = (
    ggplot(df, aes(x='relative_time', y='workload_rates_ips', color='workload_type'))
    + geom_line()
    + geom_vline(xintercept=start_to_ignore) # linetype='dotted'
)
p.save(path=plots_path, filename=f"invocation_patterns.pdf", width=12, height=8, units='cm')
p

# %% Simulate upscaled trace
p = (
    ggplot(df_long, aes(x='relative_time', y='value', color='variable'))
    # Individual y-scales are needed when the traces have too different invocation rates
    + facet_wrap('workload_type', scales='free_y')
    + geom_line()
    + geom_vline(xintercept=start_to_ignore) # linetype='dotted'
)
p.save(path=plots_path, filename=f"invocation_patterns_upscaled.pdf", width=14, height=10, units='cm')
p
# %%
