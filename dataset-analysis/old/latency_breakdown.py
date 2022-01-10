# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %% [markdown]
# # Latency Breakdown

# %% Imports
import yaml
from pathlib import Path
import logging
import pandas as pd
# Plotting
from plotnine import *
from plotnine.positions import position_fill
from mizani.breaks import date_breaks
from mizani.formatters import date_format

# %% Configure paths
plots_root_path = Path('/Users/anonymous/Downloads/exp7x')
data_path = Path('/Users/anonymous/Documents/Datasets/serverless-study/data')
apps_path = data_path / 'lg7/ec2-user'
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
categories = ['trigger', 'container_initialization', 'runtime_initialization', 'computation', 'orchestration', 'queing', 'overhead', 'external_service', 'unclassified']

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

# %% Boxplot per latency category Function
def plot_latency_breakdown(traces_df, app_name, exe_pick=0):
    # Identify percentiles
    traces_df['p95'] = traces_df['duration'] > traces_df['duration'].quantile(0.95)
    traces_df['p99'] = traces_df['duration'] > traces_df['duration'].quantile(0.99)

    long = pd.melt(traces_df, id_vars=['trace_id', 'start_time', 'num_cold_starts', 'p95', 'p99'], value_vars=categories)
    long['latency'] = long['value'].fillna(pd.Timedelta(seconds=0))
    # long.head()

    plots_path = plots_root_path / app_name
    plots_path.mkdir(exist_ok=True)

    # warm_only = long[long['num_cold_starts']==0]

    p = (
        ggplot(long)
        + geom_boxplot(aes(x='variable', y='latency', color='p95'))
        + theme(
            axis_text_x=element_text(size=7, angle = 90)
        )
    )
    p.save(path=plots_path, filename=f"latency_breakdown_{exe_pick}.pdf")

    # Stacked area plot over time
    long['start_time_ts'] = pd.to_datetime(long['start_time'], unit='s')
    lg = long.groupby(['variable', pd.Grouper(key='start_time_ts', freq='2S')]).mean(numeric_only=False)
    lg = lg.reset_index()
    start_time = lg['start_time_ts'].min()
    end_time = lg['start_time_ts'].max()
    timeformat = "%Y-%m-%d %H:%M:%S.%f"
    p = (
        ggplot(lg)
        + geom_col(aes(x='start_time_ts', y='latency', fill='variable'))
        + scale_x_datetime(labels=date_format('%H:%M:%S'))
        + labs(
            x=f"start_time={start_time.strftime(timeformat)}\nend_time={end_time.strftime(timeformat)}\nduration={end_time-start_time}"
        )
    )
    p.save(path=plots_path, filename=f"latency_breakdown_timeseries_{exe_pick}.pdf")


# %% Share of cold starts over time
def plot_cold_start_share(traces_df, app_name, exe_pick=0):
    plots_path = plots_root_path / app_name
    plots_path.mkdir(exist_ok=True)

    # Stacked area plot over time
    traces_df['start_time_ts'] = pd.to_datetime(traces_df['start_time'], unit='s')
    lg = traces_df.groupby(['num_cold_starts', pd.Grouper(key='start_time_ts', freq='100ms')]).size().reset_index(name='counts')
    # lg.head()

    start_time = lg['start_time_ts'].min()
    end_time = lg['start_time_ts'].max()
    timeformat = "%Y-%m-%d %H:%M:%S.%f"
    p = (
        ggplot(lg)
        + geom_col(aes(x='start_time_ts', y='counts', fill='factor(num_cold_starts)'))
        + scale_x_datetime(labels=date_format('%H:%M:%S'))
        + labs(
            x=f"start_time={start_time.strftime(timeformat)}\nend_time={end_time.strftime(timeformat)}\nduration={end_time-start_time}"
        )
    )
    p.save(path=plots_path, filename=f"cold_starts_share_timeseries_{exe_pick}.pdf")


# %% Analyze all apps
cold_dfs = []
warm_dfs = []
for app_name, app_source in apps.items():
    app_logs_path = apps_path / Path(app_source).parent / 'logs'
    execution_paths = []
    if app_logs_path.is_dir():
        execution_paths = [x for x in app_logs_path.iterdir() if x.is_dir()]
    exe_count = 0
    for execution in sorted(execution_paths):
        # NOTE: would be better to parse execution metadata first and filter relevant executions before expensive analysis
        traces_df = do_analysis(execution)
        if (traces_df['label'] != 'exp71').all() and not traces_df.empty:
            # plot_latency_breakdown(traces_df, app_name, exe_count)
            plot_cold_start_share(traces_df, app_name, exe_count)
            # HACK: only pick first execution (hopefully the same pattern) for relative latency breakdown
            # id = f"{app_name}_{exe_count}"
            if exe_count == 0:
                traces_df['id'] = app_name
                warm = traces_df[traces_df['num_cold_starts'] == 0]
                warm_dfs.append(warm)
                cold = traces_df[traces_df['num_cold_starts'] > 0]
                cold_dfs.append(cold)
            exe_count += 1


# %% Prepare data for breakdown delta plot across all apps
# Cold
cold_df = pd.concat(cold_dfs)

# Identify percentiles
cold_df['p95'] = cold_df['duration'] > cold_df['duration'].quantile(0.95)
cold_df['p99'] = cold_df['duration'] > cold_df['duration'].quantile(0.99)

# Transform to long format
cold_long = pd.melt(cold_df, id_vars=['id', 'trace_id', 'start_time', 'num_cold_starts', 'p95', 'p99'], value_vars=categories)
cold_long['latency'] = cold_long['value'].fillna(pd.Timedelta(seconds=0))

cold_no_video = cold_long[cold_long['id'] != 'vprocessing_benchmark']

# %% Aggregate for relative plot
cold_ag = cold_no_video.groupby(['id', 'variable']).agg(
    mean_latency_cold=('latency', lambda x: x.mean(numeric_only=False))
)
cold_ag = cold_ag.reset_index()

# sum per app
cold_ag2 = cold_ag.groupby(['id']).agg(
    e2e_latency_cold=('mean_latency_cold', lambda x: x.sum(numeric_only=False))
)
cold_ag2 = cold_ag2.reset_index()
cold_ag = pd.merge(cold_ag, cold_ag2, on=['id'], how='left')

# Warm
# Prepare data for breakdown overview plot across all apps
warm_df = pd.concat(warm_dfs)

# Identify percentiles
warm_df['p95'] = warm_df['duration'] > warm_df['duration'].quantile(0.95)
warm_df['p99'] = warm_df['duration'] > warm_df['duration'].quantile(0.99)

# Transform to long format
warm_long = pd.melt(warm_df, id_vars=['id', 'trace_id', 'start_time', 'num_cold_starts', 'p95', 'p99'], value_vars=categories)
warm_long['latency'] = warm_long['value'].fillna(pd.Timedelta(seconds=0))

warm_no_video = warm_long[warm_long['id'] != 'vprocessing_benchmark']

# %% Aggregate for relative plot
warm_ag = warm_no_video.groupby(['id', 'variable']).agg(
    mean_latency_warm=('latency', lambda x: x.mean(numeric_only=False))
)
warm_ag = warm_ag.reset_index()

# sum per app
warm_ag2 = warm_ag.groupby(['id']).agg(
    e2e_latency_warm=('mean_latency_warm', lambda x: x.sum(numeric_only=False))
)
warm_ag2 = warm_ag2.reset_index()
warm_ag = pd.merge(warm_ag, warm_ag2, on=['id'], how='left')

both = pd.merge(cold_ag, warm_ag, on=['id', 'variable'], how='left')
both['latency_delta_change'] = (both['mean_latency_cold'] - both['mean_latency_warm']) / both['mean_latency_warm']
both['latency_delta'] = both['mean_latency_cold'] - both['mean_latency_warm']
both['e2e_latency_delta'] = both['e2e_latency_cold'] - both['e2e_latency_warm']
both['latency_delta_share'] = both['latency_delta'] / both['e2e_latency_delta']
both['latency_delta_label'] = both['latency_delta'].apply(lambda x: f"{round(x.total_seconds() * 1000)}ms")
both.head()

# %% Plot relative latency breakdown of delta between warm and cold starts
p = (
    ggplot(both, aes(x='id', y='latency_delta_share', fill='variable'))
    + geom_bar(stat="identity", position='fill')
    + geom_text(aes(label='latency_delta_label'), position=position_fill(vjust=0.5), size=7)  # format_string='{:.2%}'
    + theme(
        axis_text_x=element_text(size=7, angle = 90)
    )
)
p.save(path=plots_root_path, filename=f"relative_latency_breakdown_all_apps_delta.pdf")
