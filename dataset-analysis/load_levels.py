"""Implements plots to analyze the effect of different load levels on performance and cold starts."""

# %% Imports
from sb_importer import *
from mizani.formatters import date_format

# RCIW
from statistics import variance
from scipy.stats import norm
from scipy.stats.mstats import mjci, hdquantiles


# %% Statistics helper

# laaber:21 "Predicting unstable software benchmarks using static source code features"
# See 4.4.2 Variability Measure > Maritz-Jarrett Confidence Interval of the Median Estimation
# Source: https://github.com/sealuzh/benchmark-instability-prediction-replication-package/blob/51d55bbc91fe0084860081cf627e0c81b9732c4c/approach/BenchmarkVariabilities/calculation.py#L105
def calculate_RCIW_MJ_HD(data, prob = 0.5, alpha = 0.01, axis = None):
    """
    Computes the alpha confidence interval for the selected quantiles of the data, with Maritz-Jarrett estimators.
    :param prob:
    :param alpha:
    :param axis:
    :return:
    """
    if len(data) < 2:
        return -1
    
    if variance(data) == 0.0:
        return 0.0
    
    alpha = min(alpha, 1 - alpha)
    z = norm.ppf(1 - alpha/2.)
    xq = hdquantiles(data, prob, axis=axis)
    med = round(xq[0], 5)
    if med == 0:
        return 0.0

    smj = 0.0

    try:
        smj = mjci(data, prob, axis=axis)
    except:
        return 0.0

    ci_bounds = (xq - z * smj, xq + z * smj)
    ci_lower = ci_bounds[0][0]
    ci_lower = 0 if ci_lower < 0 else ci_lower
    ci_upper = ci_bounds[1][0]
    ci_upper = 0 if ci_upper < 0 else ci_upper

    rciw = ((ci_upper - ci_lower) / med) * 100
    
    return rciw

# %% Plotting methods

def plot_latency_over_time(all_apps):
    # NOTE: doesn't scale for large datasets (~315MB for exp22), needs more aggregation
    p = (
        ggplot(all_apps)
        + aes(x='start_time_ts', y='duration') # fill='factor(num_cold_starts)'
        + geom_point()
        + scale_x_datetime(labels=date_format('%H:%M:%S'))
        + facet_wrap('~ app + iteration', scales = 'free', ncol = 3)
        + theme(subplots_adjust={'wspace': 0.25, 'hspace': 0.25})
    )
    p.save(path=plots_path('all_apps'), filename=f"latency_over_time.pdf", width=35, height=50, units='cm')


def plot_latency_over_time_per_app(all_iterations, app_name):
    # NOTE: still doesn't scale (~50MB for exp22 image_processing with 3 iterations)
    p = (
        ggplot(all_iterations)
        + aes(x='start_time_ts', y='duration')
        + geom_point()
        + scale_x_datetime(labels=date_format('%H:%M:%S'))
        + facet_wrap('iteration', scales = 'free', ncol = 1)
        + theme(subplots_adjust={'vspace': 0.25})
    )
    p.save(path=plots_path(app_name), filename=f"latency_over_time.pdf", width=16, height=30, units='cm')


def plot_load_level_validation(all_iterations, app_name):
    p = (
        ggplot(all_iterations)
        + aes(x='relative_time', y='invocations_per_second', color='variable')
        + geom_line(alpha=0.8)
        + facet_wrap('iteration', scales = 'free_y', ncol = 1)
        + theme(subplots_adjust={'vspace': 0.25})
        # Minute separators
        # + geom_vline(xintercept=range(0, 1250, 60), color='lightgrey')
    )
    p.save(path=plots_path(app_name), filename=f"load_level_validation.pdf", width=16, height=30, units='cm')


def plot_latency_by_load_level(trace_breakdown_both_groups, app_name, iteration):
    """Plots the latency distribution by different load levels.
    Filters timespan with clean data and creates load level bins.
    Hardcoded: The timespan and bins depend on the experiment!"""
    # Only consider time with clean data as traces might not meet the designated load level (e.g., due to sampling)
    only_clean = trace_breakdown_both_groups[trace_breakdown_both_groups['relative_time'] < 3000]
    # lg2/exp22.py
    bins = [1, 10, 20, 50, 100, 150, 200]
    # exp22.py/thumbnail_generator (t<1500), image_processing (t<1500)
    # tuples = [(0, 2), (5, 15), (15, 25), (40, 60), (80, 120)]
    # exp22.py/event_processing (t<1500) => produces double the traces due to disconnected traces!
    # tuples = [(0, 4), (10, 30), (30, 50), (80, 120), (160, 240)]
    # exp22.py/mtraining_benchmark (t<900), matrix_multiplication (t<900)
    # tuples = [(0, 2), (5, 15), (15, 25)]
    # exp22.py/todo_api (t<3000)
    tuples = [(0, 2), (5, 15), (15, 25), (40, 60), (80, 120), (130, 170), (170, 230)]
    # exp22.py/realworld_backend (t<3000)
    # tuples = [(0, 2), (3, 13), (13, 22), (30, 55), (60, 110), (120, 150), (165, 220)]
    interval_range = pd.IntervalIndex.from_tuples(tuples)
    # NOTE: generates a "SettingWithCopyWarning" warning when filtering a subset of only_clean because:
    # "A value is trying to be set on a copy of a slice from a DataFrame."
    # only_clean['trace_breakdown_ips_bin'] = pd.cut(only_clean['trace_breakdown_ips'], bins=interval_range)
    # Alternative time-based bins
    labels = [10, 50, 100]
    timestep = 60  # seconds
    range_end = (len(labels) + 1) * timestep
    bins = np.arange(0, range_end, timestep)
    only_clean['trace_breakdown_ips_bin'] = pd.cut(only_clean['relative_time'], bins, labels=labels, include_lowest=True)
    p = (
        ggplot(only_clean)
        + aes(color='trace_breakdown_ips_bin', x='duration') # color='factor(percentiles)'
        # Hides distribution
        # + geom_boxplot()
        # Nice output but takes very long to compute
        # + geom_violin()
        # Works best although close lines are hard to distinguish
        + stat_ecdf(alpha=0.7)
    )
    p.save(path=plots_path(app_name), filename=f"latency_by_load_level_{iteration}.pdf", width=16, height=16, units='cm')


def latency_label(latency, latency_share, prefix='') -> str:
    """Returns a label for the absolute latency (difference) when above a certain relative threshold."""
    if latency_share > 0.03:
        latency_ms = round(latency.total_seconds() * 1000)
        return f"{prefix}{latency_ms}ms"
    else:
        return ""


def latency_stats_per_time_category(all_apps, aggregates = ['mean', 'p50', 'p99']) -> pd.DataFrame:
    """Calculates the mean, p50, and p99 latency stats across all apps per time category."""
    # Ignore partial cold starts because they cannot be compared to full cold starts
    filtered_all_apps = all_apps[all_apps['coldstart_status'] != 'partial']

    # Tranform to long format
    all_apps_long = pd.melt(filtered_all_apps, id_vars=['app', 'request_type', 'trace_id', 'coldstart'], value_vars=categories)
    all_apps_long['latency'] = all_apps_long['value'].fillna(pd.Timedelta(seconds=0))

    # Aggregate for relative plot
    all_apps_agg = all_apps_long.groupby(['app', 'request_type', 'variable', 'coldstart']).agg(
        mean_latency=('latency', lambda x: x.mean(numeric_only=False)),
        p50_latency=('latency', lambda x: x.quantile(0.5)),
        p99_latency=('latency', lambda x: x.quantile(0.99))
    )
    all_apps_agg = all_apps_agg.reset_index()

    all_apps_sum = all_apps_agg.groupby(['app', 'request_type', 'coldstart']).agg(
        e2e_mean_latency=('mean_latency', lambda x: x.sum(numeric_only=False)),
        e2e_p50_latency=('p50_latency', lambda x: x.sum(numeric_only=False)),
        e2e_p99_latency=('p99_latency', lambda x: x.sum(numeric_only=False))
    )
    all_apps_sum = all_apps_sum.reset_index()
    df = pd.merge(all_apps_agg, all_apps_sum, on=['app', 'request_type', 'coldstart'], how='left')

    for agg in aggregates:
        df[f"{agg}_latency_share"] = df[f"{agg}_latency"] / df[f"e2e_{agg}_latency"]
        df[f"{agg}_latency_share_label"] = df.apply(lambda row: latency_label(row[f"{agg}_latency"], row[f"{agg}_latency_share"]), axis=1)

    # Re-order time categories
    categories_used_ordered = get_categories_used_ordered(categories, df['variable'])
    df['variable'] = df['variable'].astype('category')
    df['variable'].cat.reorder_categories(categories_used_ordered, inplace=True)

    app_order_used_ordered = get_categories_used_ordered(app_order, df['app'])
    df['app'] = df['app'].astype('category')
    df['app'].cat.reorder_categories(app_order_used_ordered, inplace=True)
    return df


def get_warm_cold_diff(df, aggregates) -> pd.DataFrame:
    """Calculate the difference between warm (even indices) and cold (uneven indices) invocations.
    df: a data frame with row-wise alternating cold and warm invocations."""
    # NOTE: The difference implementation is slow using a loop (didn't know how to do it vectorized)
    # NOTE: The aggregates are hardcoded to mean, p50, p99 here
    cols = ['mean_latency', 'p50_latency', 'p99_latency', 'e2e_mean_latency', 'e2e_p50_latency', 'e2e_p99_latency']
    rows = []
    df_length = len(df.index)
    shift = 0
    for i in range(int(df_length / 2)):
        warm_index = i * 2 - shift
        cold_index = warm_index + 1
        # Prepare primary key columns for new diff row
        row = [
            df['app'][cold_index],
            df['request_type'][cold_index],
            df['variable'][cold_index]
        ]
        # NOTE: It can happen that data is missing for the cold or warm invocation scenario.
        # Therefore, we need to check if both values are present and skip invalid combinations.
        warm_row = [
            df['app'][warm_index],
            df['request_type'][warm_index],
            df['variable'][warm_index]
        ]
        # Handle warm invocation data missing
        if df['coldstart'][warm_index]:
            shift += 1
            logging.warning(f"No data for warm invocations of {warm_row}. Skipping.")
            continue
        # Handle cold invocation data missing
        if not df['coldstart'][cold_index]:
            shift += 1
            logging.warning(f"No data for cold invocations of {row}. Skipping.")
            continue
        # Ensure that we compare the same same combination
        assert warm_row == row, f"Error trying to compute cold vs warm invocation difference of wrong combination: {warm_row} vs {row}"
        # Ensure that we are actually comparing cold vs warm invocation
        errorMsg = (
            'Error trying to compute the difference between cold and warm invocation:'
            f" Both values for the app {df['app'][cold_index]} and variable {df['variable'][cold_index]}"
            f" have the same coldstart flag {df['coldstart'][cold_index]}"
        )
        assert df['coldstart'][cold_index] != df['coldstart'][warm_index], errorMsg
        for col in cols:
            row.append(df[col][cold_index] - df[col][warm_index])
        rows.append(row)

    all_colums = ['app', 'request_type', 'variable'] + cols
    df_diff = pd.DataFrame(rows, columns=all_colums)

    for agg in aggregates:
        df_diff[f"{agg}_latency_share"] = df_diff[f"{agg}_latency"] / df_diff[f"e2e_{agg}_latency"]
        df_diff[f"{agg}_latency_share_label"] = df_diff.apply(lambda row: latency_label(row[f"{agg}_latency"], row[f"{agg}_latency_share"], '+'), axis=1)

    # Re-order time categories
    categories_used_ordered = get_categories_used_ordered(categories, df_diff['variable'])
    df_diff['variable'] = df_diff['variable'].astype('category')
    df_diff['variable'].cat.reorder_categories(categories_used_ordered, inplace=True)

    app_order_used_ordered = get_categories_used_ordered(app_order, df_diff['app'])
    df_diff['app'] = df_diff['app'].astype('category')
    df_diff['app'].cat.reorder_categories(app_order_used_ordered, inplace=True)
    return df_diff


def get_warm_slow_diff(df) -> pd.DataFrame:
    """Calculate difference between warm and slow (p99) invocations."""
    warm = df[df['coldstart'] == False]
    # Calculate delta
    warm['p50_p99_delta'] = warm['p99_latency'] - warm['p50_latency']
    warm['e2e_p50_p99_delta'] = warm['e2e_p99_latency'] - warm['e2e_p50_latency']
    # Calculate share of delta relative to e2e latency
    warm['slow_latency_share'] = warm['p50_p99_delta'] / warm['e2e_p50_p99_delta']
    warm['slow_latency_share_label'] = warm.apply(lambda row: latency_label(row['p50_p99_delta'], row['slow_latency_share'], '+'), axis=1)
    return warm


font_size = 6
def plot_latency_breakdown_warm(df, agg):
    # TODO: Fix this quick attempt to values not appearing for warm invocations.
    # # Remove runtime_initialization and container_initialization because they are all 0 for warm invocations
    # filter_list = ['runtime_initialization', 'container_initialization']
    # df_filtered = df[~df['variable'].isin(filter_list)]
    # df_filtered = df[(df['variable'] != 'runtime_initialization')&(df['variable'] != 'container_initialization')]
    # # Failed attempt to remove categories as well :(
    # df_filtered['variable'].cat.remove_unused_categories(inplace=True)
    p = (
        ggplot(df, aes(x='app_request_type', y=f"{agg}_latency_share", fill='variable'))
        + geom_bar(stat='identity', position='fill')
        + geom_text(aes(label=f"{agg}_latency_share_label"), position=position_fill(vjust=0.5), size=font_size)  # format_string='{:.2%}'
        + labs(x='Application\n(Request type)', y=f"Latency share: {agg} warm", fill='Time category')
        + theme(
            axis_text_x=element_text(size=font_size, angle = 90)
        )
    )
    p.save(path=plots_path('all_apps'), filename=f"latency_breakdown_warm_{agg}.pdf", width=12, height=11, units='cm')


def plot_latency_breakdown_warm_cold_diff(df_diff, agg):
    """Plot difference between cold and warm invocations"""
    p = (
        ggplot(df_diff, aes(x='app_request_type', y=f"{agg}_latency_share", fill='variable'))
        + geom_bar(stat='identity', position='fill')
        + geom_text(aes(label=f"{agg}_latency_share_label"), position=position_fill(vjust=0.5), size=font_size)  # format_string='{:.2%}'
        # NOTE: automatically removes rows with negative values
        + ylim(0, 1)
        + labs(x='Application\n(Request type)', y=f"Latency penalty: {agg} cold - {agg} warm", fill='Time category')
        + theme(
            axis_text_x=element_text(size=font_size, angle = 90)
        )
    )
    p.save(path=plots_path('all_apps'), filename=f"latency_breakdown_warm_cold_diff_{agg}.pdf", width=12, height=11, units='cm')


def plot_latency_breakdown_warm_slow_diff(df_slow):
    """Plot difference between slow (p99) and warm (p50) invocations"""
    p = (
        ggplot(df_slow, aes(x='app_request_type', y='slow_latency_share', fill='variable'))
        + geom_bar(stat='identity', position='fill')
        + geom_text(aes(label='slow_latency_share_label'), position=position_fill(vjust=0.5), size=font_size)  # format_string='{:.2%}'
        # NOTE: automatically removes rows with negative values
        + ylim(0, 1)
        + labs(x='Application\n(Request type)', y='Latency penalty: p99 warm - p50 warm', fill='Time category')
        + theme(
            axis_text_x=element_text(size=font_size, angle = 90)
        )
    )
    p.save(path=plots_path('all_apps'), filename=f"latency_breakdown_warm_slow_diff.pdf", width=12, height=11, units='cm')


def plot_latency_boxplot(df):
    """Plots the e2e latency as boxplot per iteration."""
    p = (
        ggplot(df)
        + geom_boxplot(aes(x='app_request_type', y='duration'))
        + facet_wrap('~ app + iteration', scales = 'free', ncol = 4)
        + theme(
            axis_text_x=element_text(size=4, angle = 0),
            # axis_text_x=element_text(size=7, angle = 90),
            subplots_adjust={'hspace': 0.22, 'wspace': 0.12}
        )
    )
    p.save(path=plots_path('all_apps'), filename=f"latency_boxplot.pdf", width=40, height=80, units='cm', limitsize=False)


def plot_latency_boxplot_warm(df):
    """Plots e2e latency as a single boxplot for warm invocations."""
    # no_outliers = df[df['duration'] < timedelta(seconds = 20)]
    p = (
        ggplot(df)
        + geom_boxplot(aes(x='app_request_type', y='duration'))
        + theme(
            axis_text_x=element_text(size=4, angle = 90),
        )
    )
    p.save(path=plots_path('all_apps'), filename=f"latency_boxplot_warm.pdf", width=16, height=8, units='cm')


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


def plot_latency_cdf_per_coldstart_status(all_apps, request_types_order):
    """Plots an e2e latency CDF for each app_request_type grouped by coldstart status.
    Used to compare cold vs partial vs warm invocations.
    Adds extra label with RCIW and sample count."""
    # filtered = filter_and_reorder_categories(request_types_order, all_apps, 'app_request_type')
    # Add sample count label
    alpha = 0.05
    sample_counts = all_apps.groupby(['app_request_type', 'coldstart_status']).agg(
        counts=('duration', 'count'),
        x_position=('duration', lambda x: x.quantile(0.8)),
        rciw_duration=('duration', lambda x: calculate_RCIW_MJ_HD(x.dt.total_seconds(), prob = 0.5, alpha = alpha))
    ).reset_index()
    sample_counts['y_position'] = sample_counts.apply(lambda row: y_position(row['coldstart_status']), axis=1)
    sample_counts['info_label'] = sample_counts['counts'].astype(str) + '\n(' + sample_counts['rciw_duration'].round(2).astype(str) +')'
    both = pd.merge(all_apps, sample_counts, on=['app_request_type', 'coldstart_status'], how='inner')
    # Plot
    p = (
        ggplot(both)
        + aes(x='duration', color='coldstart_status')
        + facet_wrap('app_request_type', scales = 'free', ncol = 2)
        + theme(subplots_adjust={'wspace': 0.25, 'hspace': 0.25})
        # Works best although close lines are hard to distinguish
        + stat_ecdf(alpha=0.8)
        + geom_text(aes(x='x_position', y='y_position', label = 'info_label', color='coldstart_status'), data=sample_counts, size=7)
        # Hides distribution
        # + geom_boxplot()
        # Nice output but takes very long to compute
        # + geom_violin(x='coldstart', y='duration')
        # + geom_histogram(alpha=0.8, bins=50)
    )
    p.save(path=plots_path('all_apps'), filename=f"latency_cdf_per_coldstart_status.pdf", width=14, height=94, limitsize=False, units='cm')


def plot_latency_cdf_by_label(all_apps):
    """Plots an e2e latency cdf for each app_request_type grouped by iteration.
    Used for plotting different load levels."""
    # Plot
    p = (
        ggplot(all_apps)
        + aes(x='duration', color='iteration')
        + facet_wrap('app_request_type', scales = 'free', ncol = 2)
        + theme(subplots_adjust={'wspace': 0.25, 'hspace': 0.25})
        # Works best although close lines are hard to distinguish
        + stat_ecdf(alpha=0.8)
        # Hides distribution
        # + geom_boxplot()
        # Nice output but takes very long to compute
        # + geom_violin(x='coldstart', y='duration')
        # + geom_histogram(alpha=0.8, bins=50)
    )
    p.save(path=plots_path('all_apps'), filename=f"latency_cdf_per_iteration.pdf", width=14, height=94, limitsize=False, units='cm')


# %% Iterate over all apps
app_dfs = dict()
for app_name, app_source in apps.items():
    execution_paths = find_execution_paths(apps_path, app_source)
    trace_breakdown_dfs = dict()
    load_level_dfs = dict()
    iteration = 1
    for index, execution in enumerate(sorted(execution_paths)):
        app_config, app_name = read_sb_app_config(execution)
        label = app_config.get('label', '')
        # Only consider non-empty labels. Optionally add other filters:
        # exp1_latency_breakdown_4x_burst20
        # exp2_load_levels_{load_level}
        # and label == 'exp22.py' and app_name == 'thumbnail_generator':
        # if label != '' and label == 'exp1_latency_breakdown_4x_burst20':
        # if label != '' and label.startswith('exp2_load_levels_'):
        # if label != '' and label.startswith('exp3_workload_types_on_off_'):
        if label != '' and label == 'exp3_workload_types_on_off':
            workload_rates = read_workload_rates(app_config)
            workload_options = read_workload_options(execution)
            k6_invocations = read_k6_invocations(execution)
            k6_invocations_grouped = group_by_relative_time(k6_invocations, 'k6_invocations_ips')
            trace_breakdown = read_trace_breakdown(execution)
            if trace_breakdown.empty:
                logging.warning(f"Skipping empty trace breakdown {execution}")
                continue
            trace_breakdown_grouped = group_by_relative_time(trace_breakdown, 'trace_breakdown_ips')
            trace_breakdown_warm = trace_breakdown[trace_breakdown['num_cold_starts'] == 0]
            trace_breakdown_duration_grouped = group_by_duration_and_relative_time(trace_breakdown_warm)
            trace_breakdown_both_groups = pd.merge(trace_breakdown_grouped, trace_breakdown_duration_grouped, on=['relative_time'], how='inner')
            # plot_latency_by_load_level(trace_breakdown_both_groups, app_name, iteration)
            # Append full URL to trace_breakdown from k6_invocations
            trace_breakdown_merged = pd.merge(trace_breakdown, k6_invocations, how='left', on=['trace_id'])
            trace_breakdown_merged['request_type'] = trace_breakdown_merged.apply(lambda row: request_type(app_name, row['url_y'], row['method'], row['longest_path_names']), axis=1)
            # Group all 4 different data sources
            ips_dfs = [workload_rates, workload_options, k6_invocations_grouped, trace_breakdown_grouped]
            df_long = merge_by_relative_time(ips_dfs)
            workload_label = get_workload_label(app_config)
            iteration_label = f"{label}-{iteration}-{workload_label}"
            load_level_dfs[iteration_label] = df_long
            trace_breakdown_dfs[iteration_label] = trace_breakdown_merged
            iteration = iteration + 1
    if trace_breakdown_dfs:
        # Combine all interations of an app into single df
        all_iterations = pd.concat(trace_breakdown_dfs.values(), keys=trace_breakdown_dfs.keys(), names=['iteration']).reset_index()
        app_dfs[app_name] = all_iterations
        # NOTE: Doesn't scale producing large files (>100MB)
        # plot_latency_over_time_per_app(all_iterations, app_name)
        # Load level validation plots
        all_load_level_iterations = pd.concat(load_level_dfs.values(), keys=load_level_dfs.keys(), names=['iteration']).reset_index()
        plot_load_level_validation(all_load_level_iterations, app_name)


# %% Combine all app_dfs into a single data frame
all_apps = pd.concat(app_dfs.values(), keys=app_dfs.keys(), names=['app']).rename(columns={'level_1':'old_level_1'}).reset_index()
# Disable because it doesn't scale for large datasets with graphs ~315MB for exp22
# plot_latency_over_time(all_apps)

all_apps['app_request_type'] = all_apps.apply(lambda row: f"{row['app']}:{row['request_type']}", axis=1)
all_apps = add_coldstart_status(all_apps)
# Introduce coldstart flag
all_apps['coldstart'] = all_apps['num_cold_starts'] > 0
all_apps_warm = all_apps[all_apps['num_cold_starts'] == 0]
# plot_latency_boxplot_warm(all_apps_warm)

# NOTE: currently hardcoded in get_warm_cold_diff() and latency_stats_per_time_category()
aggregates = ['mean', 'p50', 'p99']
def app_request_type_label(app, request_type) -> str:
    return f"{app}\n({request_type})"

request_types_order = [app_request_type_label(app, request_type) for app, request_type in [
    ['apigw_node', 'getPath'],
    ['video_processing', 'processVideo'],
    ['model_training', 'trainModel'],
    ['matrix_multiplication', 'multiplyMatrix'],
    ['image_processing', 'postFaceImage'],
    ['image_processing', 'postNonFaceImage'],
    ['realworld_backend', 'createUser'],
    ['realworld_backend', 'followUser'],
    ['hello_retail', 'listCategories'],
    # unlikely to be triggered when not yet enough products and photographers
    # have been registered
    # ['hello_retail', 'commitPhoto'],
    ['todo_api', 'createTodo'],
    # unlikely to be triggered when not yet enough todos exist
    # ['todo_api', 'getTodo'],
    ['thumbnail_generator', 'uploadImage'],
    ['event_processing', 'ingestEvent'],
]]
plot_latency_cdf_per_coldstart_status(all_apps, request_types_order)
plot_latency_cdf_by_label(all_apps)

df = latency_stats_per_time_category(all_apps, aggregates)
# Prepare warm invocations
warm = df[df['coldstart'] == False]
warm['app_request_type'] = warm.apply(lambda row: app_request_type_label(row['app'], row['request_type']), axis=1)
warm = filter_and_reorder_categories(request_types_order, warm, 'app_request_type')

# Difference between cold and warm invocations
warm_cold_diff = get_warm_cold_diff(df, aggregates)
warm_cold_diff['app_request_type'] = warm_cold_diff.apply(lambda row: app_request_type_label(row['app'], row['request_type']), axis=1)
warm_cold_diff = filter_and_reorder_categories(request_types_order, warm_cold_diff, 'app_request_type')
for agg in aggregates:
    plot_latency_breakdown_warm(warm, agg)
    plot_latency_breakdown_warm_cold_diff(warm_cold_diff, agg)

# Difference between slow (p99) and warm (p50) invocations
slow = get_warm_slow_diff(warm)
slow['app_request_type'] = slow.apply(lambda row: app_request_type_label(row['app'], row['request_type']), axis=1)
slow = filter_and_reorder_categories(request_types_order, slow, 'app_request_type')
plot_latency_breakdown_warm_slow_diff(slow)

# Transform to long format
# all_apps_long = pd.melt(warm, id_vars=['app', 'trace_id', 'url'], value_vars=categories)
# all_apps_long['latency'] = all_apps_long['value'].fillna(pd.Timedelta(seconds=0))

# %%
