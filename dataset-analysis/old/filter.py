# %% Imports
from datetime import timedelta
from pathlib import Path
import pandas as pd
from plotnine import *

# %% Import trace breakdown
data_path = Path('/Users/anonymous/Documents/Datasets/serverless-study/data')
apps_path = data_path / 'lg3/ec2-user'
app = 'faas-migration/ThumbnailGenerator/Lambda/logs/2021-04-30_01-09-33'
trace_breakdown_path = apps_path / app / 'trace_breakdown.csv'
tp = pd.read_csv(trace_breakdown_path)

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
tp[timedelta_cols] = tp[timedelta_cols].apply(pd.to_timedelta)

# %% Filter
errors = tp[tp['unclassified'] > timedelta(0)]
errors.head()
# errors.count()

# %%
start = tp['start_time'].min()
t1 = start + (10 * 60)
t2 = start + (15 * 60)
outlier = tp.loc[(tp['duration'] > timedelta(seconds = 3)) & (tp['start_time'] > t1) & (tp['start_time'] < t2)]
outlier.head()

# %%
