from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Sequence

from matplotlib import dates as mdates, pyplot as plt
import pygal

from pyecharts import options as opts
from pyecharts.charts import Line, Grid
from pyecharts.globals import ThemeType


def _parse_dates_iso_z(dates: Sequence[str]) -> list[datetime]:
    out = []
    for d in dates:
        try:
            out.append(datetime.strptime(d, "%Y-%m-%dT%H:%M:%SZ"))
            continue
        except ValueError:
            pass
        try:
            out.append(datetime.fromisoformat(d.replace("Z", "+00:00")).replace(tzinfo=None))
        except Exception:
            raise ValueError(f"Unrecognized date format: {d!r}")
    return out

def date_to_percentage(target_date_str: str, x_vals: list[str]) -> float:
    """Convert a date string to percentage position in the data range"""
    target_dt = datetime.fromisoformat(target_date_str)

    # Get min/max dates from data
    min_dt = datetime.fromisoformat(x_vals[0])
    max_dt = datetime.fromisoformat(x_vals[-1])

    # Calculate percentage
    total_range = (max_dt - min_dt).total_seconds()
    target_offset = (target_dt - min_dt).total_seconds()

    percentage = (target_offset / total_range) * 100
    return max(0, min(100, percentage))  # Clamp to 0-100

def plot_echarts(
    dates: Sequence[str],
    values: list[float],
    values2: Optional[list[float]],
    graph_subject: str,
    data_name_1: Optional[str],
    data_name_2: Optional[str],
    *,
    get_html: bool = False,
    file_name: str = "plot_with_echarts.html",
    width: str = "900px",
    height: str = "420px",
) -> Optional[str]:
    if not dates or not values:
        raise ValueError("dates and values must be non-empty")

    label0 = data_name_1 or ""
    label1 = data_name_2 or ""

    dt = _parse_dates_iso_z(dates)
    x_vals = [d.isoformat() for d in dt]

    ymax = max(values)
    if values2:
        ymax = max(ymax, max(values2))
    y_max_with_margin = ymax * 1.05 if ymax > 0 else 1

    min_date, max_date = min(dt), max(dt)
    if min_date.date() == max_date.date():
        max_date = max_date + timedelta(days=1)

    recent_date = "2021-09-07T00:00:00"
    start_percent = date_to_percentage(recent_date, x_vals)
    line = (
        Line()  # width/height will be applied on the Grid container
        .add_xaxis(xaxis_data=x_vals)
        .add_yaxis(
            series_name=label0 or "Series 1",
            y_axis=[int(value) for value in values],
            is_symbol_show=True,
            symbol_size=6,
            is_smooth=False,
            linestyle_opts=opts.LineStyleOpts(width=2),
            label_opts=opts.LabelOpts(is_show=False),  # ← hide labels initially
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=f"Plot of {graph_subject} vs Date"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            legend_opts=opts.LegendOpts(pos_top="2%"),
            datazoom_opts=[
                opts.DataZoomOpts(type_="inside", range_start=start_percent, range_end=100),
                opts.DataZoomOpts(type_="slider", pos_bottom="0", range_start=5, range_end=50), # TODO I think the range values here are ignored.
            ],
            xaxis_opts=opts.AxisOpts(
                type_="time",
                name="Date",
                min_=min_date.isoformat(),
                max_=max_date.isoformat(),
            ),
            yaxis_opts=opts.AxisOpts(
                name=graph_subject,
                min_=0,
                max_=y_max_with_margin,
                splitline_opts=opts.SplitLineOpts(is_show=True),
            ),
            toolbox_opts=opts.ToolboxOpts(
                is_show=True,
                feature=opts.ToolBoxFeatureOpts(
                    save_as_image=opts.ToolBoxFeatureSaveAsImageOpts(is_show=True),
                    data_zoom=opts.ToolBoxFeatureDataZoomOpts(is_show=True),
                    restore=opts.ToolBoxFeatureRestoreOpts(is_show=True),
                ),
            ),
        )
    )

    if values2 is not None:
        line.add_yaxis(
            series_name=label1 or "Series 2",
            y_axis=values2,
            is_symbol_show=True,
            symbol_size=6,
            is_smooth=False,
            linestyle_opts=opts.LineStyleOpts(width=2, type_="dashed"),
        )

    # Use Grid to control margins since set_global_opts() here doesn't support grid_opts
    grid = Grid(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width=width, height=height))
    grid.add(
        line,
        grid_opts=opts.GridOpts(pos_left="8%", pos_right="4%", pos_top="12%", pos_bottom="12%"),
    )

    if get_html:
        return grid.render_embed()
    else:
        grid.render(file_name)
        return None


# keep your existing matplotlib/pygal helpers unchanged if you still use them:

def plot_mat(dates, values: list[float], values2: list[float], graph_subject, data_name_1, data_name_2) -> None:
    label0 = data_name_1 if data_name_1 else ""
    label1 = data_name_2 if data_name_2 else ""

    dates = [datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ') for date in dates]

    min_date = min(dates)
    max_date = max(dates)
    if min_date.date() == max_date.date():
        min_date=min_date.date()
        max_date = max_date.date() + timedelta(days=1)
    num_intervals = 6

    date_range = max_date - min_date
    interval_length = date_range / num_intervals

    if interval_length < timedelta(days=70):
        locator = mdates.WeekdayLocator(interval=max(1, int(interval_length.days / 7)))
        date_format = mdates.DateFormatter('%Y-%m-%d')
    elif interval_length < timedelta(days=365):
        locator = mdates.MonthLocator()
        date_format = mdates.DateFormatter('%Y-%m')
    else:
        locator = mdates.YearLocator()
        date_format = mdates.DateFormatter('%Y')

    plt.figure(figsize=(10, 6))
    plt.plot(dates, values, marker='o', label=label0)
    if values2 is not None:
        plt.plot(dates, values2, marker='x', linestyle='--', label=label1)

    plt.legend()
    plt.gca().xaxis.set_major_locator(locator)
    plt.gca().xaxis.set_major_formatter(date_format)
    plt.gcf().autofmt_xdate()
    plt.title(f'Plot of {graph_subject} vs Date')
    plt.xlabel('Date')
    plt.ylabel(graph_subject)
    plt.grid(True)
    plt.tight_layout()
    plt.ylim(0, max(values))
    plt.show()


def plot_pygal(dates, values: list[float], values2: Optional[list[float]], graph_subject,
               data_name_1, data_name_2, get_bytes=False) -> None | bytes:
    chart_max = max(values)
    if values2 is not None:
        chart_max2 = max(values2)
        chart_max = max(chart_max, chart_max2)
    pygal_chart = pygal.Line(width=800, height=100, explicit_size=True, range=(0, chart_max), title=graph_subject)
    pygal_chart.add(data_name_1, values)
    if values2 is not None:
        pygal_chart.add(data_name_2, values2)

    if get_bytes:
        return pygal_chart.render_data_uri()
    else:
        pygal_chart.render_to_file('plot_with_pygal.svg')


def plot_d3(dates, values: list[float], values2: Optional[list[float]], graph_subject,
            data_name_1, data_name_2, get_bytes=False) -> None | bytes:
    chart_max = max(values)
    if values2 is not None:
        chart_max2 = max(values2)
        chart_max = max(chart_max, chart_max2)
    pygal_chart = pygal.Line(width=800, height=100, explicit_size=True, range=(0, chart_max), title=graph_subject)
    pygal_chart.add(data_name_1, values)
    if values2 is not None:
        pygal_chart.add(data_name_2, values2)

    if get_bytes:
        return pygal_chart.render_data_uri()
    else:
        pygal_chart.render_to_file('plot_with_pygal.svg')


def plot(dates, values: list[float], values2: Optional[list[float]], graph_subject, data_name_1, data_name_2, file_name) -> None:
    USE_ECHARTS = True
    if USE_ECHARTS:
        plot_echarts(dates, values, values2, graph_subject, data_name_1, data_name_2, get_html=False, file_name=file_name)
    else:
        plot_pygal(dates, values, values2, graph_subject, data_name_1, data_name_2)