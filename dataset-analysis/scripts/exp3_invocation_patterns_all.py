"""This script generates the plots for the invocation patterns experiment (exp3)
used in the paper. See the _all.py script for more plots.
Formerly called workload types."""

# %% Imports
from sb_importer import *
from rciw import calculate_RCIW_MJ_HD


# %% Helper methods
def app_request_type_label(app, request_type) -> str:
    return f"{app}\n({request_type})"


def read_all_apps() -> pd.DataFrame:
    """Import and combine data from all applications and executions to a data frame."""
    app_dfs = dict()
    for app_name, app_source in apps.items():
        execution_paths = find_execution_paths(apps_path, app_source)
        trace_breakdown_dfs = dict()
        iteration = 1
        for index, execution in enumerate(sorted(execution_paths)):
            app_config, app_name = read_sb_app_config(execution)
            label = app_config.get('label', '')
            # Optionally use a filter to avoid importing apps that are not needed
            # as this can take some time for large traces.
            app_include_list = ['']
            if label != '' and label.startswith('exp3_workload_types_20min'):  # app_name in app_include_list
                trace_breakdown = read_trace_breakdown(execution)
                k6_invocations = read_k6_invocations(execution)
                # Optional info:
                # workload_rates = read_workload_rates(app_config)
                # workload_options = read_workload_options(execution)
                # k6_invocations_grouped = group_by_relative_time(k6_invocations, 'k6_invocations_ips')
                # if trace_breakdown.empty:
                #     logging.warning(f"Skipping empty trace breakdown {execution}")
                #     continue
                # trace_breakdown_grouped = group_by_relative_time(trace_breakdown, 'trace_breakdown_ips')
                # trace_breakdown_warm = trace_breakdown[trace_breakdown['num_cold_starts'] == 0]
                # trace_breakdown_duration_grouped = group_by_duration_and_relative_time(trace_breakdown_warm)
                # trace_breakdown_both_groups = pd.merge(trace_breakdown_grouped, trace_breakdown_duration_grouped, on=['relative_time'], how='inner')
                # # plot_latency_by_load_level(trace_breakdown_both_groups, app_name, iteration)
                # # Append full URL to trace_breakdown from k6_invocations
                trace_breakdown_merged = pd.merge(trace_breakdown, k6_invocations, how='left', on=['trace_id'])
                trace_breakdown_merged['request_type'] = trace_breakdown_merged.apply(lambda row: request_type(app_name, row['url_y'], row['method'], row['longest_path_names']), axis=1)
                # Save iteration with an appropriate label
                workload_label = get_workload_label(app_config)
                trace_breakdown_dfs[workload_label] = trace_breakdown_merged
                iteration = iteration + 1
        if trace_breakdown_dfs:
            # Combine all interations of an app into single df
            all_iterations = pd.concat(trace_breakdown_dfs.values(), keys=trace_breakdown_dfs.keys(), names=['iteration']).reset_index()
            all_iterations['app_request_type'] = all_iterations.apply(lambda row: app_request_type_label(app_name, row['request_type']), axis=1)
            # Optimization: Select only used columns
            all_iterations = all_iterations[['iteration', 'trace_id', 'relative_time_x', 'duration', 'app_request_type', 'request_type', 'num_cold_starts']]
            app_dfs[app_name] = all_iterations

    # Combine all app_dfs into a single data frame
    all_apps = pd.concat(app_dfs.values(), keys=app_dfs.keys(), names=['app']).rename(columns={'level_1':'old_level_1'}).reset_index()
    return all_apps


# %% Import data from all apps
cache_dir.mkdir(exist_ok=True, parents=True)
cache_path = cache_dir / 'exp3_all_apps.parquet'
use_cache = True
all_apps = None
# Load from cache if possible to speed up plotting as reading
# all data from disk can take time (15+ minutes)
if use_cache and cache_path.is_file():
    print(f"Using cached data from {cache_path}")
    all_apps = pd.read_parquet(cache_path)
else:  # Create cache
    print('No cached data found. Reading from disk.')
    all_apps = read_all_apps()
    all_apps['duration'] = all_apps['duration'].dt.total_seconds()
    all_apps.to_parquet(cache_path)
all_apps['duration_sec'] = all_apps['duration']


# %% Prepare data for plotting
seconds_to_skip = 60
df = all_apps[all_apps['relative_time_x']>=seconds_to_skip]
df = add_coldstart_status(df)

# Clip data because facetting doesn't support dynamic limits
# and the tail is too long to be shown.
# Important: This needs to be described when presenting 
# Based on StackOverflow: https://stackoverflow.com/a/54356494
def is_outlier(s):
    lower_limit = s.min()
    upper_limit = s.quantile(.99)
    return ~s.between(lower_limit, upper_limit)

df_filtered = df.loc[~df.groupby('app_request_type')['duration_sec'].apply(is_outlier), :].reset_index(drop=True)


# %% Plot facetted CDF of duration by workload type
p = (
    ggplot(df_filtered)
    + aes(x='duration_sec', color='iteration')
    + labs(
        x='Trace duration [s]', y=f"ECDF", color='Workload type')
    + facet_wrap('app_request_type', scales = 'free_x', nrow=4)
    + theme_light(base_size=12)
    + theme(figure_size=(18, 8), legend_position='right',
         legend_background=element_rect(alpha=0), legend_margin=0,
         subplots_adjust={'hspace': 0.55, 'wspace': 0.02},
         legend_box_margin=0)
    # Works best although close lines cab be hard to distinguish
    # Density plot would be better in that regard (but plotnine impl. has a memory leak)
    + stat_ecdf(alpha=0.8)
    + scale_color_brewer('qual', 'Dark2')
    # MAYBE: Add p99 marker indicating that we cut the extreme tail here
    # + geom_vline(xintercept=p99,colour='red')
    # Need to clip due to extreme outliers but that's not supported for facet:
    # https://github.com/has2k1/plotnine/issues/289
    # + scale_x_continuous(limits=(p_low, p_high))
    # Hides distribution takes long due to outliers
    # + geom_boxplot()
    # Nice output but takes very long to compute
    # + geom_violin(x='coldstart', y='duration')
    # + geom_histogram(alpha=0.8, bins=50)
)
p.save(path=plots_path('exp3'), filename=f"latency_cdf_by_workload_type_all.pdf")
p


# %% Plot facetted CDF of duration by cold start status
def y_position(coldstart_status):
    """Returns a hardcoded y-position for text
    depending on coldstart status."""
    if coldstart_status == 'warm':
        return 0.8
    elif coldstart_status == 'partial':
        return 0.6
    elif coldstart_status == 'cold':
        return 0.4
    else:
        return 0.1


def plot_latency_cdf_by_coldstart_status(all_apps):
    """Plots an e2e latency CDF for each app_request_type grouped by coldstart status.
    Used to compare cold vs partial vs warm invocations.
    Adds extra label with RCIW and sample count."""
    alpha = 0.05
    sample_counts = all_apps.groupby(['app_request_type', 'coldstart_status']).agg(
        counts=('duration_sec', 'count'),
        x_position=('duration_sec', lambda x: x.quantile(0.8)),
        rciw_duration=('duration_sec', lambda x: calculate_RCIW_MJ_HD(x, prob = 0.5, alpha = alpha))
    ).reset_index()
    sample_counts['y_position'] = sample_counts.apply(lambda row: y_position(row['coldstart_status']), axis=1)
    sample_counts['info_label'] = sample_counts['counts'].astype(str) + '\n(' + sample_counts['rciw_duration'].round(2).astype(str) +')'
    both = pd.merge(all_apps, sample_counts, on=['app_request_type', 'coldstart_status'], how='inner')
    p = (
        ggplot(both)
        + aes(x='duration_sec', color='coldstart_status')
        + labs(
            x='Trace duration [s]', y=f"ECDF", color='Coldstart Status')
        + facet_wrap('app_request_type', scales = 'free_x', nrow=4)
        + theme_light(base_size=12)
        + theme(figure_size=(18, 8), legend_position='right',
            legend_background=element_rect(alpha=0), legend_margin=0,
            subplots_adjust={'hspace': 0.55, 'wspace': 0.02},
            legend_box_margin=0)
        + stat_ecdf(alpha=0.8)
        + scale_color_manual(['blue', 'orange','red'])
        + geom_text(aes(x='x_position', y='y_position', label = 'info_label', color='coldstart_status'), data=sample_counts, size=7)
    )
    p.save(path=plots_path('exp3'), filename=f"latency_cdf_by_coldstart_status_all.pdf")
    return p
plot_latency_cdf_by_coldstart_status(df_filtered)

# %%
