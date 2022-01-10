
"""Generates a CSV summary for an experiment including all executions of all apps."""

# %% Imports
from sb_importer import *


# %% Iterate over apps
summaries = []
for app_name, app_source in apps.items():
    execution_paths = find_execution_paths(apps_path, app_source)
    for index, execution in enumerate(sorted(execution_paths)):
        app_config, app_name = read_sb_app_config(execution)
        label = app_config.get('label', '')
        # Only consider non-empty labels. Optionally add other filters:
        # if label != '' and label.startswith('exp3_workload_types_on_off_'):
        if label != '' and label == 'exp3_workload_types_on_off':
            workload_rates = read_workload_rates(app_config)
            workload_options = read_workload_options(execution)
            k6_invocations = read_k6_invocations(execution)
            trace_breakdown = read_trace_breakdown(execution)
            invalid_traces = read_invalid_traces(execution)
            summary = generate_summary(execution, app_config, app_name, workload_rates, workload_options, k6_invocations, trace_breakdown, invalid_traces)
            summaries.append(summary)
            save_summary(summary, execution)

# Export experiment overview
overview_df = pd.concat(summaries)
overview_path = plots_path() / 'overview.csv'
overview_df.to_csv(overview_path, index=False)
