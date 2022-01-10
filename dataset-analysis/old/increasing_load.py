# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %% [markdown]
# # Increasing Workload

# %% Imports
from pathlib import Path
from datetime import timedelta
import pandas as pd
import numpy as np
from plotnine import *
import yaml
import logging

# %% Configure paths
data_path = Path('/Users/anonymous/Documents/Datasets/serverless-study/data')
apps_path = data_path / 'lg2/ec2-user'
apps = {
    'image_processing': 'aws-serverless-workshops/ImageProcessing/image_processing_benchmark.py',
    'todo_api': 'faas-migration-go/aws/todo_api_benchmark.py',
    'event_processing': 'faas-migration/Event-Processing/Lambda/event_processing_benchmark.py',
    'matrix_multiplication': 'faas-migration/MatrixMultiplication/Lambda/matrix_multiplication_benchmark.py',
    'thumbnail_generator': 'faas-migration/ThumbnailGenerator/Lambda/thumbnail_benchmark.py',
    'hello_retail': 'hello-retail/hello_retail_benchmark.py',
    'realworld_backend': 'realworld-dynamodb-lambda/realworld_benchmark.py',
    'mtraining_benchmark': 'serverless-faas-workbench/aws/cpu-memory/model_training/mtraining_benchmark.py',
    'vprocessing_benchmark': 'serverless-faas-workbench/aws/cpu-memory/video_processing/vprocessing_benchmark.py'
}

# %% Analysis Function
def do_analysis(logs_path):
    workload_traces_path = data_path / 'workload_traces'
    patterns_path = workload_traces_path / '20rps_20min'
    workload_type = 'constant'

    # Invocation patterns per minute based on the Azure Function traces
    patterns_path = patterns_path / f"{workload_type}.csv"
    # Generated workload options using a FractionalBrownianMotion model
    workload_path = logs_path / 'workload_options.json'
    # Actual invocations log from k6
    invocations_path = logs_path / 'k6_metrics.csv'
    # Based on AWS XRay traces
    traces_path = logs_path / 'trace_breakdown.csv'
    invalid_path = logs_path / 'invalid_traces.csv'
    # Sb config
    config_path = logs_path / 'sb_config.yml'


    ## Load sb config
    sb_config = {}
    app_config = {}
    app = ''
    if config_path.is_file():
        with open(config_path) as f:
            sb_config = yaml.load(f, Loader=yaml.FullLoader)
        app = list(sb_config.keys())[0]
        # Workaround for cases where sb is the first key
        if app == 'sb':
            app = list(sb_config.keys())[1]
        app_config = sb_config[app]
    else:
        logging.warning(f"Config file missing at {config_path}.")

    # Extract name of workload trace path
    # NOTE: Can be null when using an inline config via experiment plan!
    # wt_path = PurePosixPath(app_config['workload_trace'])
    # workload_trace = wt_path.stem

    ## Read traces csv based on sb trace analyzer output
    traces_df = pd.read_csv(traces_path)
    # see CSV_FIELDS in aws_trace_analyzer.py
    timedelta_cols = [
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
    # Parse timedelta fields
    traces_df[timedelta_cols] = traces_df[timedelta_cols].apply(pd.to_timedelta)
    num_valid_traces = len(traces_df)
    traces_df['app'] = app
    traces_df['label'] = app_config.get('label', '')
    # traces_df['workload_trace'] = workload_trace
    # traces_df.head()

    # Add relative time
    traces_start = traces_df['start_time'].min()
    traces_df['relative_time'] = traces_df['start_time'] - traces_start
    traces_df = traces_df.sort_values(by=['relative_time'])

    return traces_df

# %% Analyze all apps
traces = []
exe_pick = 0  # maps to execution ordered by time based on directories within an experiment, 0-based index
app_name_pick = 'thumbnail_generator'  # needs to match with app_pick!
for app_name, app_source in apps.items():
    # HACK to skip expensive analysis for non-relevant apps
    if app_name != app_name_pick:
        continue
    app_logs_path = apps_path / Path(app_source).parent / 'logs'
    execution_paths = [x for x in app_logs_path.iterdir() if x.is_dir()]
    exe_count = 0
    for execution in sorted(execution_paths):
        traces_df = do_analysis(execution)
        if (traces_df['label'] == 'exp22.py').all():
            if not traces_df.empty and exe_count == exe_pick and (traces_df['app'] == app_name_pick).all():
                traces.append(traces_df)
            exe_count += 1

# %% Combine and filter traces
all_traces = pd.concat(traces)
all_traces.head()

# %% Duration over time
plots_path = Path('/Users/anonymous/Downloads')
(
    ggplot(all_traces)
    + geom_line(aes(x='relative_time', y='duration', color='factor(num_cold_starts)'))
    # 5-minute separators
    + geom_vline(xintercept=range(0, 2300, 300), color='lightgrey')
)

# %% Add load range
bins = np.arange(0, 2300, 300)
labels = [1, 10, 20, 50, 100, 150, 200]
all_traces['load'] = pd.cut(all_traces['relative_time'], bins, labels=labels, include_lowest=True)
all_traces.head()

# %% Stats by load group
# by_load = all_traces.groupby(pd.cut(all_traces['relative_time'], np.arange(0, 2300, 300)))[['num_cold_starts']].count()
# by_load = by_load.reset_index()
# by_load.head()

# %% Duration by load
filtered = all_traces[all_traces['duration'] < timedelta(seconds=5)]
p = (
    ggplot(all_traces)
    + geom_boxplot(aes(x='load', y='duration', color='factor(num_cold_starts)'))
)
p.save(path=plots_path, filename=f"increasing_load_exe{exe_pick}.pdf")

# %% Filter out steady periods
query = ' | '.join([f'(relative_time >{bin+20} & relative_time <={bin+300-10})' for bin in bins])
steady = all_traces.query(query)
steady.head()

# %% Duration by steady load
p = (
    ggplot(steady)
    + geom_boxplot(aes(x='load', y='duration', color='factor(num_cold_starts)'))
)
p.save(path=plots_path, filename=f"increasing_load_steady_exe{exe_pick}.pdf")
# %%
