# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %% [markdown]
# # Performance Assessment

# %%
# Imports
from pathlib import Path, PurePosixPath
from datetime import timedelta
import pandas as pd
from plotnine import *
import yaml


# %%
# Configure paths
data_path = Path('/Users/anonymous/Documents/Datasets/serverless-study/data')
apps_path = data_path / 'lg3/ec2-user'
apps = [
    'faas-migration/ThumbnailGenerator/Lambda/thumbnail_benchmark.py',
    'faas-migration/MatrixMultiplication/Lambda/matrix_multiplication_benchmark.py',
    'faas-migration/Event-Processing/Lambda/event_processing_benchmark.py',
    'aws-serverless-workshops/ImageProcessing/image_processing_benchmark.py',
    'faas-migration-go/aws/todo_api_benchmark.py',
    'hello-retail/hello_retail_benchmark.py',
    'realworld-dynamodb-lambda/realworld_benchmark.py',
    'serverless-faas-workbench/aws/cpu-memory/video_processing/vprocessing_benchmark.py',
    'serverless-faas-workbench/aws/cpu-memory/model_training/mtraining_benchmark.py'
]
app_logs_path = apps_path / Path(apps[4]).parent / 'logs'
execution_paths = [x for x in app_logs_path.iterdir() if x.is_dir()]
# dynamic
logs_path = execution_paths[1]
# static
# logs_path = apps_path / 'aws-serverless-workshops/ImageProcessing/logs/2021-04-30_07-02-35'

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

    # Extract name of workload trace path
    wt_path = PurePosixPath(app_config['workload_trace'])
    workload_trace = wt_path.stem

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
    traces_df['workload_trace'] = workload_trace
    # traces_df.head()

    return traces_df

traces = []
for app in apps:
        app_logs_path = apps_path / Path(app).parent / 'logs'
        execution_paths = [x for x in app_logs_path.iterdir() if x.is_dir()]
        for execution in execution_paths:
            # print(execution)
            traces_df = do_analysis(execution)
            if not traces_df.empty:
                traces.append(traces_df)

# %% Combine and filter traces
all_traces = pd.concat(traces)
steady_traces = all_traces[all_traces['workload_trace'] == 'constant']
steady_no_video = steady_traces[steady_traces['app'] != 'vprocessing_benchmark']

no_video = all_traces[(all_traces['app'] != 'vprocessing_benchmark') & (all_traces['duration'] < timedelta(seconds=20))]
# all_traces.head()

# %% Boxplot for steady
(
    ggplot(steady_no_video)
    + aes(x="factor(app)", y="duration")
    + geom_boxplot()
    + coord_flip()
)

# %% Boxplot for all workload traces
(
    ggplot(no_video)
    + aes(x="factor(app)", y="duration", color="workload_trace")
    + geom_boxplot()
    + coord_flip()
)

# %% CDF for steady
(
    ggplot(steady_no_video)
    + aes(x="duration", color="factor(app)")
    + stat_ecdf()
)
