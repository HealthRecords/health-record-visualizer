"""
Base module for creating an HTML page with Sparklines for each test.

https://www.markhneedham.com/blog/2017/09/23/python-3-create-sparklines-using-matplotlib/

Limits:
you can use a fixed value for the upper and lower limit of the value.True
    Date range should be from the lowest date of any  test,  to the highest date of any test.test_categories()
Need to figure out how to scale each sparkline separately
could also maybe use pygal, which sounds cool. But let's use matplotlib for now.


TODO: Need to match the date range across all sparklines, if I'm going to line them up.

TODO: I need normal range for every test we want to plot (I guess it's not required, just nice to have).
      It looks like what I want is in Observation-*.json files,
      as referenceRange. It's in 2707 out of 4541 files.

TODO: This file has a test name of "---": Observation-7881B1CD-55FD-42BD-8FFB-CE98D13C88CD.json, fix it.
"""
import argparse
import base64
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import TextIO

from matplotlib import pyplot as plt
import matplotlib.dates as mdates

from health_lib import extract_all_values, yield_observation_files, Observation, StatInfo, list_vitals
from plot_health import plot_pygal
import plot_health
from xml_reader import get_test_results, get_all_test_types


def sparkline(data_x_str: list[str], data_y: list[float], graph_y_min,
              graph_y_max, normal_min, normal_max, fig_size_x: float = 8, fig_size_y: float = 2):
    plot_lib = "mat"
    plot_func_nane = F"""sparkline_{plot_lib}"""
    this_module = sys.modules[__name__]
    func = getattr(this_module, plot_func_nane)
    assert func
    assert callable(func)
    # print(func)
    return func(data_x_str, data_y, graph_y_min, graph_y_max, normal_min, normal_max, fig_size_x, fig_size_y)
    # else:
    #     return sparkline_pygal(data_x_str, data_y, graph_y_min, graph_y_max, normal_min, normal_max, fig_size_x, fig_size_y)


def sparkline_mat(data_x_str: list[str], data_y: list[float], graph_y_min,
              graph_y_max, normal_min, normal_max, fig_size_x: float = 8, fig_size_y: float = 2):
    # TODO We assumed that normal ranges would be bounded by horizontal lines.
    #      We have found some tests that have a referenceRange
    #      for some values, and not for others. I think there is a way to shade between curves. Try that.
    for date in data_x_str:
        if date is None:
            print("XYZ")
    data_x = [datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ') for date in data_x_str]

    fig, axes = plt.subplots(1, 1, figsize=(fig_size_x, fig_size_y))
    # axes.axis('off')
    if normal_max is not None:
        assert normal_min is not None
        plt.axhspan(normal_min, normal_max, color='green', alpha=0.3)
    else:
        normal_max = graph_y_max
    axes.set_ylim([graph_y_min, max(graph_y_max, normal_max)])
    if len(data_x) == 1:
        # TODO combine with plot() in plot_health.py
        # Single points are invisible, so make it more obvious.
        axes.plot(data_x, data_y, 'o', markeredgecolor='r')
    else:
        axes.plot(data_x, data_y)

    # Calculate major ticks for x-axis
    years = mdates.YearLocator()
    plt.gca().xaxis.set_major_locator(years)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    img = BytesIO()
    plt.savefig(img)
    img.seek(0)
    plt.close()
    return '<img src="data:image/png;base64,{}"/>'.format(base64.b64encode(img.read()).decode())

def sparkline_pygal(data_x_str: list[str], data_y: list[float], graph_y_min,
              graph_y_max, normal_min, normal_max, fig_size_x: float = 8, fig_size_y: float = 2):
    # TODO We assumed that normal ranges would be bounded by horizontal lines.
    #      We have found some tests that have a referenceRange
    #      for some values, and not for others. I think there is a way to shade between curves. Try that.
    data_x = [datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ') for date in data_x_str]
    chart_bytes = plot_pygal(data_x, data_y,None,
                       graph_subject=None, data_name_1=None,
                             data_name_2=None, get_bytes=True)

    return F"""<img alt="health data chart"  height="100" width="1000" src="{chart_bytes}">"""
    # return F"""<img alt="health data chart" style="max-height: 3rem; max-width: 30em" src="{chart_bytes}">"""


def sparklines(incoming: list[list[Observation]], debug=False) -> list[tuple[str, str, int]]:
    """
    Generate a list of sparklines.
    :param incoming: a list of lists of Observations.
    :return: a list of (image tag, stat name, number of Observations) tuples
    """

    outgoing = []
    for index in range(0, len(incoming)):
        one_ob_list = incoming[index]
        if len(one_ob_list) == 0:
            continue

        data_x = [x.date for x in one_ob_list]
        data_y = [x.data[0].value for x in one_ob_list]  # TODO handle blood pressure and other multi-values stats.
        if one_ob_list[0].range is not None:
            check_for_messy_data = debug
            nn = [x.range for x in one_ob_list]
            if None in nn:
                print("We have a set of observations with different range limit values for the same test. "
                      "This is in the data, not a bug in code. Need to figure out what to do with it.",
                      one_ob_list[0].filename)
                if check_for_messy_data:  # TODO
                    range_ = {x.range.low.value for x in one_ob_list}
                    assert len(range_) == 1
            if not hasattr(one_ob_list[0].range, "low") or not hasattr(one_ob_list[0].range.low, "value"):
                if not hasattr(one_ob_list[0].range, "low"):
                    if hasattr(one_ob_list[0].range, "comparator"):
                        # TODO Figure out what to do for graphs that assume a single value. This is a range, like "<60"
                        print("No support for comparators at this time.", range, one_ob_list[0].filename)
                else:
                    # TODO This is normal in some conditions. Resolve how to handle
                    print("Missing low in the range:", range, one_ob_list[0].filename)
                normal_min = None
                normal_max = None
            else:
                normal_min = one_ob_list[0].range.low.value
                normal_max = one_ob_list[0].range.high.value
        else:
            normal_min = None
            normal_max = None
        baseline_at_zero = True
        if baseline_at_zero:
            baseline = 0
        else:
            baseline = min(data_y)
        graph_y_min = 0
        graph_y_max = max(data_y)
        img_info = sparkline(data_x, data_y, graph_y_min, graph_y_max,
                             normal_min, normal_max, 8, 1)
        outgoing.append((img_info, one_ob_list[0].name, len(one_ob_list)))

    return outgoing


def html_page(f: TextIO, incoming: list[list[Observation]], title: str = None,
              head_scripts: list[str] = (), head_styles: list[str] = ()):
    """
    Generate HTML page for the sparklines
    :param f:
    :param incoming: Currently a list of images to include in the HTML page. Should to to being a generator. TODO
    :param title
    :param head_styles CSS Styles to be included in the head. XYZ in  XYZ in
             <link rel="stylesheet" href="XYZ">
    :param head_scripts src of Scripts to be included in the head. XYZ in <script src="XYZ" defer></script>
    :return:
    """
    print("""<!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="utf-8">
                """, file=f)
    if title is not None:
        print(F"<title>{title}</title>", file=f)

    if head_styles:
        for style in head_styles:
            print(F"""<style>{style}</style>""", file=f)
    if head_scripts:
        for script in head_scripts:
            print(F"""{script}""", file=f)
    print("""</head>\n<body>""", file=f)
    if title is not None:
        print(F"<h1>{title}</H1>", file=f)
    sparks = sparklines(incoming)
    spark_len = len(sparks)
    print(
        F"""<div style="display: grid;grid-template-columns: 1fr 8fr; grid-template-rows: repeat({spark_len}, 5em);">"""
        , file=f)
    for imgtag, stat_name, count in sparks:
        print("""<div class="grid-item">""", file=f)
        print(F"""{stat_name}({count})""", file=f)
        print("</div>", file=f)
        print("""<div class="grid-item">""", file=f)
        print(imgtag, file=f)
        print("</div>", file=f)
    print("</div>", file=f)
    print("""</body></html>""", file=f)

def sparks(stats: list[list[Observation]], title: str = None, head_scripts: list[str] = (), head_styles=()):

    with open("output/sparkbase.html", "w") as fff:
        html_page(fff, stats, title, head_scripts, head_styles)

styles: str = """.grid-container {
      display: grid;
      grid-template-columns: 30% 70%;
      gap: 10px; /* Adjust the gap between items as needed */
    }
    
    .item {
      display: flex;
      flex-direction: column;
    }
    
    .name {
      background-color: lightblue; /* Example styling */
    }
    
    .chart {
      background-color: lightgreen; /* Example styling */
    }"""


def vitals(stats: list[StatInfo], graph_title="Graph") -> None:
    """
    print a graph of the requests stats to a currently hardcoded file.
    :param stats: The stats to chart.
    :param graph_title The title for the html page generated
    :return: Nothing,
    """

    # stats: list[StatInfo] = [
    #     StatInfo("Lab", "Potassium"),
    #     StatInfo("Lab", "Bilirubin, total"),
    #     StatInfo("Vital Signs", "SpO2"),
    #     StatInfo("Vital Signs", "Pulse"),
    #     StatInfo("Vital Signs", "Height"),
    #     StatInfo("Vital Signs", "Blood Pressure"),
    #     StatInfo("Vital Signs", "Weight"),
    #     StatInfo("Vital Signs", "Respirations"),
    #     StatInfo("Vital Signs", "Temperature")
    # ]
    # TODO: Should we sort by frequency of test? Recency of test? Name of test?
    stats: list[StatInfo] = sorted(stats, key=lambda x: (x.name, x.category_name))
    stats_to_graph: list[list[Observation]] = []
    for vital in stats:
        ws: list[Observation] = extract_all_values(yield_observation_files(condition_path), stat_info=vital)
        stats_to_graph.append(ws)

    sparks(stats_to_graph, head_styles=[styles], title=graph_title)

if __name__ == "__main__":
    base: Path = Path("export/apple_health_export")
    condition_path: Path = base / "clinical-records"

    parser = argparse.ArgumentParser(description="Create an html file containing sparklines")
    parser.add_argument("--all", action=argparse.BooleanOptionalAction, help="Graph all lab and vital signs")
    parser.add_argument("--apple", action=argparse.BooleanOptionalAction,
                        help="Source can be Apple Health data, or clinical data (default). ", default=False)
    parser.add_argument("--file", action='store',
                        help="Filename to write the html page to", default="output/sparkbase.html")
    parser.add_argument("--cat", action='store',
                        help="Category to filter to. Needs quotes if category name has spaces",
                        default="Vital Signs")
    parser.add_argument("-v", "--vitals", action=argparse.BooleanOptionalAction,
                        help='Shortcut for --cat "Vital Signs"')
    parser.add_argument("-l", "--labs", action=argparse.BooleanOptionalAction,
                        help='Shortcut for --cat "Labs". This can take a while.')

    args = parser.parse_args()
    if args.vitals:
        cat = "Vital Signs"
    elif args.labs:
        cat = "Lab"
    else:
        cat = args.cat
    if args.apple:
        if False:
            rc = get_all_test_types()
            for x in rc:
                print(x)
            sys.exit(0)
        else:  # plot
            cat = "apple"
            display_name = "Oxygen saturation"
            assert cat
            observations = get_test_results(display_name)
            stats_to_graph = [[ob for ob in observations]]
            sparks(stats_to_graph, head_styles=[styles], title="Hello, Neighbor")
            sys.exit(0)

    else:
        vs = list_vitals(observation_files=yield_observation_files(condition_path), category=cat)
        if args.list:
            for v in vs:
                print(v)
            sys.exit(0)
        else:
            vsi: list[StatInfo] = [StatInfo(cat, name) for name in vs]
            vitals(vsi, graph_title=cat)

