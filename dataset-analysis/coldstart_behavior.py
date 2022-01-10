# %% Imports
from sb_importer import *
from plotnine import *
from mizani.formatters import date_format

# %% Analyze single app
# absolute path
execution = Path('/Users/anonymous/Documents/Datasets/serverless-study/data/lg7/ec2-user/faas-migration/ThumbnailGenerator/Lambda/logs/2021-08-30_09-34-20')
timestamp = execution.name
app_config, app_name = read_sb_app_config(execution)
label = app_config.get('label', '')
trace_breakdown = read_trace_breakdown(execution)
trace_breakdown_long = unpivot_trace_breakdown_to_time_category(trace_breakdown)
trace_breakdown_grouped_category = group_by_time_category_and_relative_time(trace_breakdown_long)
df = trace_breakdown_grouped_category

# Re-order time categories
categories_used_ordered = get_categories_used_ordered(categories, df['variable'])
df['variable'] = df['variable'].astype('category')
df['variable'].cat.reorder_categories(categories_used_ordered, inplace=True)

# Group by dominant number of cold starts
start_time = trace_breakdown['start_time_ts'].min().floor('1s')
time_grouping = pd.Grouper(key='start_time_ts', freq='1s')
trace_breakdown_grouped = trace_breakdown.groupby([time_grouping]).agg(pd.Series.mode).reset_index()

# %% Plot the latency breakdown by time category (e.g., computation time) as stacked barplot timeseries.
# TODO: Find a way to add the dominant number of coldstarts as 2nd y-axis
# Unfortunately, this is not implemented in plotnine and I haven't figured out how to
# hack this using an internal API (https://github.com/has2k1/plotnine/issues/68#issuecomment-347681470)
# or Matplotlib directly (https://github.com/has2k1/plotnine/issues/63 and
# https://matplotlib.org/stable/gallery/subplots_axes_and_figures/two_scales.html#sphx-glr-gallery-subplots-axes-and-figures-two-scales-py)
p = (
    ggplot(df)
    + geom_col(aes(x='start_time_ts', y='latency', fill='variable'))
    # TODO: Use relative time for x-axis with sensible breaks and unit (e.g., seconds since first request)
    # + scale_x_datetime(labels=date_format('%H:%M:%S'))
    # Attempt#1 to use timedelta scale with x='relative_time' creates correct x-axis labels
    # but an empty graph (https://plotnine.readthedocs.io/en/stable/generated/plotnine.scales.scale_x_timedelta.html)
    # + scale_x_timedelta(name="Time since first request")
    # Attempt#2 adjusting breaks yielded the same empty graph based on (https://stackoverflow.com/questions/54678274/how-to-scale-x-axis-with-intervals-of-1-hour-with-x-data-type-being-timedelta64)
    # + scale_x_timedelta(
    #     breaks=lambda x: pd.to_timedelta(
    #         pd.Series(range(0, 60, 10)),
    #         unit='seconds'
    #     )
    # )
)
p.save(path=plots_path(app_name), filename=f"latency_breakdown_timeseries_{label}.pdf", units='cm') # , width=15, height=30

# %% Plot the dominant number of cold starts over time using the mode (i.e., most common num_cold_starts per second)
p = (
    ggplot(trace_breakdown_grouped)
    + geom_line(aes(x='start_time_ts', y='num_cold_starts'))
    + scale_x_datetime(labels=date_format('%H:%M:%S'))
)
p.save(path=plots_path(app_name), filename=f"latency_breakdown_timeseries_{label}_coldstarts.pdf", units='cm') # , width=15, height=30
