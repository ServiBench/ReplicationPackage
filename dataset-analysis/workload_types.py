"""Implements plots to analyze how different workload types impact the performance and cold starts."""

# %% Imports
from datetime import timedelta
from plotnine import *
from mizani.formatters import date_format
from mizani.breaks import date_breaks, timedelta_breaks
from sb_importer import *

# %% Plotting methods
def plot_cold_start_share(all_grouped_workloads, app_name):
    """Plots the share of cold starts over time as stacked barplot timeseries."""
    timeformat = "%Y-%m-%d %H:%M:%S.%f"
    p = (
        ggplot(all_grouped_workloads)
        + geom_col(aes(x='start_time_ts', y='counts', fill='factor(num_cold_starts)'))
        # start_time_ts: works but displays datetime instead of time since first request
        + scale_x_datetime(labels=date_format('%H:%M:%S'))
        + facet_wrap('iteration', scales = 'free', ncol = 1)
        + theme(subplots_adjust={'hspace': 0.22})
        # start_time_ts: weird 8-digit minutes labels (e.g., 26996105 minutes) and no data
        # + scale_x_timedelta(name="Minutes since first request")
        # relative_time: correct labels with minutes since first request but empty data (same without fill)
        # + scale_x_timedelta(name="Minutes since first request")
        # start_time_ts: missing x-axis altogether
        # Based on SO: https://stackoverflow.com/questions/54678274/how-to-scale-x-axis-with-intervals-of-1-hour-with-x-data-type-being-timedelta64
        # + scale_x_timedelta(
        #     breaks=lambda x: pd.to_timedelta(
        #         pd.Series(range(0, 20, 5)),
        #         unit='minutes'
        #     )
        # )
        # Optional title when used individually without facet
        # + labs(
        #     x=f"start_time={start_time.strftime(timeformat)}\nend_time={end_time.strftime(timeformat)}\nduration={end_time-start_time}\nlabel={label}"
        # )
    )
    p.save(path=plots_path(app_name), filename=f"cold_starts_share_timeseries.pdf", width=25, height=30, units='cm')


def plot_latency_breakdown_timeseries(all_grouped_breakdowns, app_name):
    """Plots the latency breakdown by time category (e.g., computation time) as stacked barplot timeseries."""
    p = (
        ggplot(all_grouped_breakdowns)
        + geom_col(aes(x='start_time_ts', y='latency', fill='variable'))
        + scale_x_datetime(labels=date_format('%H:%M:%S'))
        + facet_wrap('iteration', scales = 'free', ncol = 1)
        + theme(subplots_adjust={'hspace': 0.22})
    )
    p.save(path=plots_path(app_name), filename=f"latency_breakdown_timeseries.pdf", width=15, height=30, units='cm')


def plot_latency_breakdown_by_color(all_breakdowns, app_name, color):
    """Plots a boxplot for the trace duration for all latency breakdown categories per color variable (e.g., percentile or num_cold_starts).
    For example, it generates a boxplot for non-outliers <=p95 (p95==False) and one for outliers >p95."""
    p = (
        ggplot(all_breakdowns)
        + geom_boxplot(aes(x='variable', y='latency', color=f"factor({color})"))
        + facet_wrap('iteration', scales = 'free_y', ncol = 1)
        + theme(
            axis_text_x=element_text(size=7, angle = 90),
            subplots_adjust={'hspace': 0.22}
        )
    )
    p.save(path=plots_path(app_name), filename=f"latency_breakdown_by_{color}.pdf", width=15, height=30, units='cm')


def plot_cdf_all_apps(all_apps):
    """Plots a CDF for the trace duration for all apps per workload label."""
    p = (
        ggplot(all_apps, aes(x="duration", color="factor(iteration)"))
        + stat_ecdf()
        + facet_wrap('~app', scales = "free_x", ncol=3)
        # Add more space for the y-axis tick text
        + theme(subplots_adjust={'hspace': 0.2})
    )
    p.save(path=plots_path('all_apps'), filename=f"latency_cdf_by_workload.pdf", width=50, height=35, units='cm')


def export_latency_table(all_apps):
    """Exports a CSV summary table of the latency in seconds ordered by app and the 99.99th percentile."""
    all_apps['duration_s'] = all_apps['duration'].apply(timedelta.total_seconds)
    all_apps_grouped = all_apps.groupby(by=['app', 'iteration'])['duration_s'].describe(percentiles=[.25, .5, .75, .99, .999, .9999]).sort_values(['app','99.99%'], ascending=False)
    table_path = plots_path('all_apps') / 'latency_by_workload.csv'
    all_apps_grouped.to_csv(table_path)


def export_coldstart_frequency(all_apps):
    """Exports a CSV summary table with frequencies of cold starts by workload type."""
    all_apps_grouped = all_apps.groupby(by=['app', 'iteration']).agg({'num_cold_starts' : [np.count_nonzero, 'count']}).sort_values(['app', ('num_cold_starts', 'count_nonzero')], ascending=False)
    all_apps_grouped['cold_start_frequency'] = all_apps_grouped['num_cold_starts', 'count_nonzero'] / all_apps_grouped['num_cold_starts', 'count'] * 100
    table_path = plots_path('all_apps') / 'num_cold_starts_by_workload.csv'
    all_apps_grouped.to_csv(table_path)


# %% Iterate over all apps
app_dfs = dict()
for app_name, app_source in apps.items():
    execution_paths = find_execution_paths(apps_path, app_source)
    workload_dfs = dict()
    workload_grouped_dfs = dict()
    breakdown_dfs = dict()
    breakdown_grouped_dfs = dict()
    iteration = 1
    for index, execution in enumerate(sorted(execution_paths)):
        app_config, app_name = read_sb_app_config(execution)
        label = app_config.get('label', None)
        if label:
            workload_label = get_workload_label(app_config)
            iteration_label = f"{label}-{iteration}-{workload_label}"
            trace_breakdown = read_trace_breakdown(execution)
            workload_dfs[iteration_label] = trace_breakdown
            trace_breakdown_grouped_cold = group_by_cold_starts_and_relative_time(trace_breakdown)
            workload_grouped_dfs[iteration_label] = trace_breakdown_grouped_cold
            trace_breakdown_long = unpivot_trace_breakdown_to_time_category(trace_breakdown)
            breakdown_dfs[iteration_label] = trace_breakdown_long
            trace_breakdown_grouped_category = group_by_time_category_and_relative_time(trace_breakdown_long)
            breakdown_grouped_dfs[iteration_label] = trace_breakdown_grouped_category
            iteration = iteration + 1
    # Combine all iterations per app
    if workload_dfs:
        all_workloads = pd.concat(workload_dfs.values(), keys=workload_dfs.keys(), names=['iteration'])
        app_dfs[app_name] = all_workloads
        all_grouped_workloads = pd.concat(workload_grouped_dfs.values(), keys=workload_grouped_dfs.keys(), names=['iteration']).reset_index()
        plot_cold_start_share(all_grouped_workloads, app_name)
        all_breakdowns = pd.concat(breakdown_dfs.values(), keys=breakdown_dfs.keys(), names=['iteration']).reset_index()
        # plot_latency_breakdown_by_color(all_breakdowns, app_name, 'p95')
        plot_latency_breakdown_by_color(all_breakdowns, app_name, 'p99')
        plot_latency_breakdown_by_color(all_breakdowns, app_name, 'num_cold_starts')
        all_grouped_breakdowns = pd.concat(breakdown_grouped_dfs.values(), keys=breakdown_grouped_dfs.keys(), names=['iteration']).reset_index()
        plot_latency_breakdown_timeseries(all_grouped_breakdowns, app_name)
# Combine all app_dfs into a single data frame
all_apps = pd.concat(app_dfs.values(), keys=app_dfs.keys(), names=['app']).reset_index()

# %% Overview plots
plot_cdf_all_apps(all_apps)
export_latency_table(all_apps)
export_coldstart_frequency(all_apps)
