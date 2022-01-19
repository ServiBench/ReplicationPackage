"""This script generates additional plots for the latency breakdown experiment (exp1)
including all endpoints of all applications.
It is based on load_levels.py which plots many more aspects."""

# %% Imports
from sb_importer import *
from rciw import calculate_RCIW_MJ_HD


# %% Helper methods
def latency_label(latency, latency_share, prefix='') -> str:
    """Returns a label for the absolute latency (difference) when above a certain relative threshold."""
    if latency_share > 0.03:
        latency_ms = round(latency.total_seconds() * 1000)
        return f"{prefix}{latency_ms}"
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
        df_diff[f"{agg}_latency_share_label"] = df_diff.apply(lambda row: latency_label(row[f"{agg}_latency"], row[f"{agg}_latency_share"]), axis=1)

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
    warm['slow_latency_share_label'] = warm.apply(lambda row: latency_label(row['p50_p99_delta'], row['slow_latency_share']), axis=1)
    return warm

# %% Import data from all apps
app_dfs = dict()
for app_name, app_source in apps.items():
    execution_paths = find_execution_paths(apps_path, app_source)
    trace_breakdown_dfs = dict()
    load_level_dfs = dict()
    iteration = 1
    for index, execution in enumerate(sorted(execution_paths)):
        app_config, app_name = read_sb_app_config(execution)
        label = app_config.get('label', '')
        workload_label = app_config.get('workload_label', '')
        # Filter by label of the latency breakdown experiment
        if label != '' and label == 'exp1_latency_breakdown_4x_burst20':
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
        all_iterations['app_request_type'] = all_iterations.apply(lambda row: app_request_type_label(app_name, row['request_type']), axis=1)
        app_dfs[app_name] = all_iterations

# Combine all app_dfs into a single data frame
all_apps_orig = pd.concat(app_dfs.values(), keys=app_dfs.keys(), names=['app']).rename(columns={'level_1':'old_level_1'}).reset_index()


# %% Filter and prepare for plotting
all_apps = all_apps_orig.copy()
all_apps['app_request_type'] = all_apps.apply(lambda row: app_request_type_label(row['app'], row['request_type']), axis=1)
all_apps = add_coldstart_status(all_apps)
# Introduce coldstart flag
all_apps['coldstart'] = all_apps['num_cold_starts'] > 0
all_apps_warm = all_apps[all_apps['num_cold_starts'] == 0]

# Add second-based duration as some operations do not support timedelta
all_apps['duration_sec'] = all_apps['duration'].dt.total_seconds()

# NOTE: currently hardcoded in get_warm_cold_diff() and latency_stats_per_time_category()
aggregates = ['mean', 'p50', 'p99']

df = latency_stats_per_time_category(all_apps, aggregates)
# Prepare warm invocations
warm = df[df['coldstart'] == False]
warm['app_request_type'] = warm.apply(lambda row: app_request_type_label(row['app'], row['request_type']), axis=1)

warm['variable'].dtype

warm_cold_diff = get_warm_cold_diff(df, aggregates)
warm_cold_diff['app_request_type'] = warm_cold_diff.apply(lambda row: app_request_type_label(row['app'], row['request_type']), axis=1)

# %% Plot latency breakdown for warm invocations
figure_size = (16, 2.5)
def plot_latency_breakdown_warm(df, agg):
    # MAYBE: Consider adding confidence intervals if we can fit them:
    # This would require Python 3.8 (need to update in docs): https://stackoverflow.com/questions/15033511/compute-a-confidence-interval-from-sample-data
    df = df.loc[~df['variable'].str.contains('initialization'), :].reset_index(drop=True)
    df['variable'] = (df['variable'].str.replace('computation', 'Computation')
                           .replace('external_service', 'External service')
                           .replace('orchestration', 'Orchestration')
                           .replace('trigger', 'Trigger')
                           .replace('queing', 'Queueing')
                           .replace('overhead', 'Finalization overhead')
                          )
    df['variable'] = pd.Categorical(df['variable'], categories=['Computation', 'External service', 'Orchestration',
                  'Trigger', 'Queueing', 'Finalization overhead'], ordered=True)
    p = (
        ggplot(df, aes(x='app_request_type', y=f"{agg}_latency_share", fill='variable'))
        + geom_bar(stat='identity', position='fill')
        + geom_text(aes(label=f"{agg}_latency_share_label"), position=position_fill(vjust=0.5),
                    size=10, color='black', fontweight='normal')  # format_string='{:.2%}'
        + labs(x='Application', y="Latency breakdown", fill='Activity')
        + theme_light(base_size=12)
        + theme(figure_size=figure_size, legend_position=(0.45, 1.01),
               legend_background=element_rect(alpha=0), legend_title_align='bottom',
               legend_margin=0, legend_box_margin=0,
               axis_text_x=element_text(angle = 90))
        # + scale_fill_brewer('qual', 'Set3', direction=-1)
        + scale_fill_manual(['#fdb462','#80b1d3','#d9ffcf','#bebada','#ffffb3','#8dd3c7',
                            '#fccde5','#b3de69'])
        + guides(fill=guide_legend(nrow=2, title='Activity',
                                   title_position='left', byrow=True))
    )
    p.save(path=plots_path('exp1'), filename=f"latency_breakdown_warm_{agg}_all.pdf")
    return p
plot_latency_breakdown_warm(warm, 'p50')


# %% Plot Latency-penalty breakdown for warm vs. cold invocations
def plot_latency_breakdown_warm_cold_diff(df_diff, agg):
    """Plot difference between cold and warm invocations"""
    df_diff['variable'] = (df_diff['variable'].str.replace('computation', 'Computation')
                           .replace('external_service', 'External service')
                           .replace('orchestration', 'Orchestration')
                           .replace('trigger', 'Trigger')
                           .replace('queing', 'Queueing')
                           .replace('overhead', 'Finalization overhead')
                           .replace('runtime_initialization', 'Runtime initialization')
                           .replace('container_initialization', 'Container initialization')
                          )
    df_diff['variable'] = pd.Categorical(df_diff['variable'], categories=['Computation', 'External service', 'Orchestration',
                  'Trigger', 'Queueing', 'Finalization overhead', 'Runtime initialization', 'Container initialization'], ordered=True)
    p = (
        ggplot(df_diff, aes(x='app_request_type', y=f"{agg}_latency_share", fill='variable'))
        + geom_bar(stat='identity', position='fill')
        + geom_text(aes(label=f"{agg}_latency_share_label"), position=position_fill(vjust=0.5),
                   size=10, color='black', fontweight='normal')  # format_string='{:.2%}'
        # NOTE: automatically removes rows with negative values
        + ylim(0, 1)
        + labs(x='Application', y=f"Latency-penalty breakdown", fill='Activity')
        + theme_light(base_size=12)
        + theme(figure_size=figure_size, legend_position=(0.45, 1.05),
               legend_background=element_rect(alpha=0), legend_title_align='bottom',
               legend_margin=0, legend_box_margin=0,
               axis_text_x=element_text(angle = 90))
        # + scale_fill_brewer('qual', 'Set3', direction=-1)
        + scale_fill_manual(['#fdb462','#80b1d3','#d9ffcf','#bebada','#ffffb3','#8dd3c7',
                            '#fccde5','#b3de69'])
        + guides(fill=guide_legend(nrow=3, title='Activity',
                                   title_position='left', byrow=True))
        )
    p.save(path=plots_path('exp1'), filename=f"latency_breakdown_warm_cold_diff_{agg}_all.pdf")
    return p

plot_latency_breakdown_warm_cold_diff(warm_cold_diff, 'p50')


# %% Prepare latency-penalty plot for warm vs. slow invocations
slow = get_warm_slow_diff(warm)
slow['app_request_type'] = slow.apply(lambda row: app_request_type_label(row['app'], row['request_type']), axis=1)

# %% Plot Latency-penalty breakdown for warm vs. slow invocations
def plot_latency_breakdown_warm_slow_diff(df_slow):
    """Plot difference between slow (p99) and warm (p50) invocations"""
    df_slow = df_slow.loc[~df['variable'].str.contains('initialization'), :].reset_index(drop=True)
    df_slow['variable'] = (df_slow['variable'].str.replace('computation', 'Computation')
                           .replace('external_service', 'External service')
                           .replace('orchestration', 'Orchestration')
                           .replace('trigger', 'Trigger')
                           .replace('queing', 'Queueing')
                           .replace('overhead', 'Finalization overhead')
                          )
    df_slow['variable'] = pd.Categorical(df_slow['variable'], categories=['Computation', 'External service', 'Orchestration',
                  'Trigger', 'Queueing', 'Finalization overhead'], ordered=True)
    p = (
        ggplot(df_slow, aes(x='app_request_type', y='slow_latency_share', fill='variable'))
        + geom_bar(stat='identity', position='fill')
        + geom_text(aes(label='slow_latency_share_label'), position=position_fill(vjust=0.5), size=10)  # format_string='{:.2%}'
        # NOTE: automatically removes rows with negative values
        + ylim(0, 1)
        + labs(x='Application', y="Latency-penalty breakdown", fill='Activity')
        + theme_light(base_size=12)
        + theme(figure_size=figure_size, legend_position=(0.45, 1),
               legend_background=element_rect(alpha=0), legend_title_align='bottom',
               legend_margin=0, legend_box_margin=0,
               axis_text_x=element_text(angle = 90))
        # + scale_fill_brewer('qual', 'Set3', direction=-1)
        + scale_fill_manual(['#fdb462','#80b1d3','#d9ffcf','#bebada','#ffffb3','#8dd3c7',
                            '#fccde5','#b3de69'])
        + guides(fill=guide_legend(nrow=2, title='Activity',
                                   title_position='left', byrow=True))
        )
    p.save(path=plots_path('exp1'), filename=f"latency_breakdown_warm_slow_diff_all.pdf")
    return p

plot_latency_breakdown_warm_slow_diff(slow)


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
    p.save(path=plots_path('exp1'), filename=f"latency_cdf_by_coldstart_status_all.pdf")
    return p
plot_latency_cdf_by_coldstart_status(all_apps)


# # %% Generate additional plots for other percentiles and endpoints
# # Difference between cold and warm invocations
# for agg in aggregates:
#     plot_latency_breakdown_warm(warm, agg)
#     plot_latency_breakdown_warm_cold_diff(warm_cold_diff, agg)

# # Difference between slow (p99) and warm (p50) invocations
# plot_latency_breakdown_warm_slow_diff(slow)

# %%
