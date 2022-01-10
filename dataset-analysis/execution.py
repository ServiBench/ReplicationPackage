# %% Imports
from sb_importer import *

# %% Analyze single app
# relative path
execution = data_path / 'lg2/ec2-user/aws-serverless-workshops/ImageProcessing/logs/2021-04-21_14-32-51'
# absolute path
# execution = Path('/Users/anonymous/Documents/Datasets/serverless-study/data/lg3/ec2-user/faas-migration/ThumbnailGenerator/Lambda/logs/2021-04-30_00-10-50')
app_config, app_name = read_sb_app_config(execution)
workload_rates = read_workload_rates(app_config)
workload_options = read_workload_options(execution)
k6_invocations = read_k6_invocations(execution)
k6_invocations_grouped = group_by_relative_time(k6_invocations, 'k6_invocations_ips')
trace_breakdown = read_trace_breakdown(execution)
trace_breakdown_grouped = group_by_relative_time(trace_breakdown, 'trace_breakdown_ips')
invalid_traces = read_invalid_traces(execution)
received_traces = merge_traces_by_id(trace_breakdown, invalid_traces)

# Group all 4 different data sources
data_frames= [workload_rates, workload_options, k6_invocations_grouped, trace_breakdown_grouped]
df_long = merge_by_relative_time(data_frames)

# NOTE: currently requires matching lg_name in sb_importer due to hardcoded apps_path in summary generator
summary = generate_summary(execution, app_config, app_name, workload_rates, workload_options, k6_invocations, trace_breakdown, invalid_traces)
