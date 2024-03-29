import arkouda as ak
import holoviews as hv
import panel as pn
import param
from typing import Tuple, Union

"""
Helper method for setting up the plot rendering environment.
Parameters
----------
engine : str
    The plotting engine.
width : int
    Width of the plot.
height : int
    Height of the plot.
Returns
-------
Dictionary
    Plot options for proper rendering in the environment.
"""


def render_env(engine: str, width: int, height: int):
    from bokeh.io import output_notebook

    output_notebook()
    if engine in ("bokeh", "b"):
        hv.extension("bokeh")
        return dict(width=width, height=height)
    elif engine in ("plotly", "p"):
        hv.extension("plotly")
        return dict(width=width, height=height)
    elif engine in ("matplotlib", "m"):
        hv.extension("matplotlib")
        return dict(fig_inches=(5, 5))
    else:
        raise ValueError("Please provide a supported plotting engine.")


"""
Plots an area plot for numeric data.
Parameters
----------
data : ak.DataFrame or ak.pdarray
    The data to be plotted.
engine : string
    The plotting engine.
width : int
    Width of the plot.
height : int
    Height of the plot.
Returns
-------
hv.Area()
    An area plot with or without a variable dropdown menu based in single or multiple columns.
"""


def area(
    data: Union[ak.DataFrame, ak.pdarray] = None,
    bins=10,
    engine: str = "matplotlib",
    width: int = 500,
    height: int = 500,
):
    opts = render_env(engine, width=width, height=height)
    if data is not None:
        if isinstance(data, ak.DataFrame):
            numeric_columns = [
                col
                for col, dtype in data.dtypes.items()
                if dtype in ["float64", "int64"]
            ]
            if len(numeric_columns) == 0:
                raise ValueError(
                    "The provided ak.DataFrame does not have at least one numeric columns."
                )
            data = data[numeric_columns]
            h, b = ak.histogram(data[data.columns[0]], bins=bins)
            var = pn.widgets.Select(
                name="variable", value=data.columns[0], options=data.columns
            )
            all = pn.widgets.Checkbox(name="all")

            @pn.depends(var.param.value, all.param.value)
            def create_figure(var, all):
                if all:
                    var.disabled = True
                    overlay = hv.Overlay()
                    for column in data.columns:
                        h, b = ak.histogram(data[column], bins=bins)
                        overlay *= hv.Area((h.to_ndarray())).opts(**opts)
                    return overlay
                else:
                    h, b = ak.histogram(data[var], bins=bins)
                    return hv.Area((h.to_ndarray())).opts(**opts)

            widgets = pn.WidgetBox(var, all, width=200)
            return pn.Row(widgets, create_figure).servable("Area")
        if isinstance(data, ak.pdarray) and data.dtype in ["int64", "float64"]:
            h, b = ak.histogram(data, bins=bins)
            return hv.Area(h.to_ndarray()).opts(**opts)
        else:
            raise ValueError(
                f"Please provide data in the form of an ak.pdarray instead of {str(type(data))}."
            )
    else:
        raise ValueError("No data was provided.")


"""
Plots a histogram for numeric data.
Parameters
----------
data : ak.DataFrame or ak.pdarray
    The data to be plotted.
bins : int
    Number of bins to divide the data into.
engine : string
    The plotting engine.
width : int
    Width of the plot.
height : int
    Height of the plot.
Returns
-------
hv.Histogram() or pn.Row(pn.WidgetBox(), hv.Histogram).
    A histogram with or without a variable dropdown menu based in single or multiple columns.
"""


def hist(
    data: Union[ak.DataFrame, ak.pdarray] = None,
    bins=10,
    engine: str = "matplotlib",
    width: int = 500,
    height: int = 500,
):
    opts = render_env(engine, width=width, height=height)
    if data is not None:
        if isinstance(data, ak.DataFrame):
            numeric_columns = [
                col
                for col, dtype in data.dtypes.items()
                if dtype in ["float64", "int64"]
            ]
            if len(numeric_columns) == 0:
                raise ValueError(
                    "The provided ak.DataFrame does not have at least one numeric columns."
                )
            data = data[numeric_columns]
            h, b = ak.histogram(data[data.columns[0]], bins=bins)
            var = pn.widgets.Select(
                name="variable", value=data.columns[0], options=data.columns
            )

            @pn.depends(var.param.value)
            def create_figure(var):
                return hv.Histogram((h.to_ndarray(), b.to_ndarray())).opts(**opts)

            widgets = pn.WidgetBox(var, width=200)
            return pn.Row(widgets, create_figure).servable("Histogram")
        if isinstance(data, ak.pdarray) and data.dtype in ["int64", "float64"]:
            h, b = ak.histogram(data, bins=bins)
            return hv.Histogram((h.to_ndarray(), b.to_ndarray())).opts(**opts)
        else:
            raise ValueError(
                f"Please provide data in the form of an ak.pdarray instead of {str(type(data))}."
            )
    else:
        raise ValueError("No data was provided.")


"""
Plots a histogram for numeric data.
Parameters
----------
data : ak.DataFrame or ak.pdarray
    The data to be plotted.
engine : string
    The plotting engine.
width : int
    Width of the plot.
height : int
    Height of the plot.
Returns
-------
hv.Histogram() or pn.Row(pn.WidgetBox(), hv.Histogram).
    A histogram with or without a variable dropdown menu based in single or multiple columns.
"""


def boxWhisker(
    data: Union[ak.DataFrame, ak.pdarray] = None,
    engine: str = "matplotlib",
    width: int = 5,
    height: int = 5,
):
    opts = render_env(engine, width=width, height=height)
    if data is not None:
        if isinstance(data, ak.DataFrame):
            numeric_columns = [
                col
                for col, dtype in data.dtypes.items()
                if dtype in ["float64", "int64"]
            ]
            if len(numeric_columns) == 0:
                raise ValueError(
                    "The provided ak.DataFrame does not have at least one numeric columns."
                )

            data = data[numeric_columns]

            var = pn.widgets.Select(
                name="variable", value=data.columns[0], options=data.columns
            )

            @pn.depends(var.param.value)
            def create_figure(var):
                sorted_data = ak.sort(data[var])

                values = {
                    "Q1": sorted_data[int(sorted_data.size * 0.25)],
                    "median": sorted_data[int(sorted_data.size * 0.5)],
                    "Q3": sorted_data[int(sorted_data.size * 0.75)],
                    "lower": sorted_data[0],
                    "upper": sorted_data[-1],
                    # "outliers" TODO,
                }

                box = hv.Bounds((0, values["Q1"], 1, values["Q3"]))
                median = hv.HLine(values["median"])
                lower_whisker = hv.Segments((1, values["lower"], 1, values["Q1"]))
                upper_whisker = hv.Segments((1, values["Q3"], 1, values["upper"]))
                # outliers = hv.Points((1, outlier) for outlier in values["outliers"])
                boxwhisker = box * median * lower_whisker * upper_whisker  # * outliers

                return boxwhisker.opts(
                    hv.opts.Bounds(alpha=0.5, color="blue"),
                    hv.opts.HLine(color="red", linewidth=2, xlim=(0, 1)),
                    hv.opts.Segments(color="black"),
                    hv.opts.Points(color="green"),
                )

            widgets = pn.WidgetBox(var, width=200)
            return pn.Row(widgets, create_figure).servable("Box and Whisker")
        if isinstance(data, ak.pdarray) and data.dtype in ["int64", "float64"]:
            sorted_data = ak.sort(data)

            values = {
                "Q1": sorted_data[int(sorted_data.size * 0.25)],
                "median": sorted_data[int(sorted_data.size * 0.5)],
                "Q3": sorted_data[int(sorted_data.size * 0.75)],
                "lower": sorted_data[0],
                "upper": sorted_data[-1],
                # "outliers" TODO,
            }

            box = hv.Bounds((0, values["Q1"], 1, values["Q3"]))
            median = hv.HLine(values["median"])
            lower_whisker = hv.Segments((1, values["lower"], 1, values["Q1"]))
            upper_whisker = hv.Segments((1, values["Q3"], 1, values["upper"]))
            # outliers = hv.Points((1, outlier) for outlier in values["outliers"])
            boxwhisker = box * median * lower_whisker * upper_whisker  # * outliers

            return boxwhisker.opts(
                hv.opts.Bounds(alpha=0.5, color="blue"),
                hv.opts.HLine(color="red", linewidth=2, xlim=(0, 1)),
                hv.opts.Segments(color="black"),
                hv.opts.Points(color="green"),
            )
        else:
            raise ValueError(
                f"Please provide data in the form of an ak.pdarray instead of {str(type(data))}."
            )
    else:
        raise ValueError("No data was provided.")


"""
Explore data using binning techniques.
Parameters
----------
data : ak.DataFrame or tuple(ak.pdarray)
    The data to be plotted.
xBin : int
    Number of bins to divide the x data into.
yBin : int
    Number of bins to divide the y data into.
engine : string
    The plotting engine.
width : int
    Width of the plot.
height : int
    Height of the plot.
Returns
-------
hv.Image().
    An image with or without a variable dropdown menu based in single or multiple columns.
"""


def explore(
    data: Union[ak.DataFrame, Tuple[ak.pdarray, ak.pdarray]] = None,
    xBin: int = 10,
    yBin: int = 10,
    engine: str = "bokeh",
    width: int = 500,
    height: int = 500,
):
    render_env(engine, width=width, height=height)
    pn.extension()
    full_data = None
    if data is not None:
        if isinstance(data, ak.DataFrame):
            numeric_columns = [
                col
                for col, dtype in data.dtypes.items()
                if dtype in ["float64", "int64"]
            ]
            if len(numeric_columns) < 2:
                raise ValueError(
                    "The provided DataFrame does not have at least two numeric columns."
                )
            full_data = data[numeric_columns]
        elif (
            isinstance(data, tuple)
            and len(data) == 2
            and all(isinstance(item, ak.pdarray) for item in data)
        ):
            full_data = ak.DataFrame(data[0], data[1])
        else:
            raise ValueError(
                "Invalid data. Please provide an ak.Dataframe or [ak.pdarray, ak.pdarray]."
            )
    else:
        raise ValueError("Please provide data.")

    class Explore(param.Parameterized):
        cmap = param.Selector(
            label="color map", default="turbo", objects=hv.plotting.list_cmaps()
        )
        x_var = param.Selector(
            label="x-variable", default=data.columns[0], objects=data.columns
        )
        y_var = param.Selector(
            label="y-variable", default=data.columns[1], objects=data.columns
        )
        enable_slider_checkbox = pn.widgets.Checkbox(
            name="remove outliers", value=False
        )
        z_score_threshold_slider = pn.widgets.FloatSlider(
            name="z-score threshold", start=0.0, end=5, step=0.1, value=3.0
        )

    params = Explore()
    cols = full_data.columns
    initial_xrange = (ak.min(full_data[cols[0]]), ak.max(full_data[cols[0]]))
    initial_yrange = (ak.min(full_data[cols[1]]), ak.max(full_data[cols[1]]))

    def make_data(x_range, y_range, cmap, x_var, y_var):
        if x_range is None or y_range is None or not x_range or not y_range:
            binned_data = ak.histogram2d(
                full_data[x_var], full_data[y_var], bins=(xBin, yBin)
            )
            return hv.Image(binned_data[0].to_ndarray(), bounds=(0, 0, 1, 1)).opts(
                cmap=cmap, width=width, height=height, color_bar=True
            )
        else:
            subset_data = data[
                (full_data[x_var] >= x_range[0])
                & (full_data[x_var] <= x_range[1])
                & (full_data[y_var] >= y_range[0])
                & (full_data[y_var] <= y_range[1])
            ]
        x_span = x_range[1] - x_range[0]
        y_span = y_range[1] - y_range[0]
        binned_data = ak.histogram2d(
            subset_data[x_var], subset_data[y_var], bins=(1000, 1000)
        )
        return hv.Image(
            binned_data[0].to_ndarray(),
            bounds=(x_range[0], y_range[0], x_range[0] + x_span, y_range[0] + y_span),
        ).opts(cmap=cmap, width=width, height=height, colorbar=True)

    @pn.depends(
        cmap=params.param.cmap, x_var=params.param.x_var, y_var=params.param.y_var
    )
    def update(cmap, x_var, y_var):
        stream = hv.streams.RangeXY(x_range=initial_xrange, y_range=initial_yrange)
        dmap = hv.DynamicMap(
            lambda x_range, y_range: make_data(x_range, y_range, cmap, x_var, y_var),
            streams=[stream],
        )
        return dmap

    widget_column = pn.Column(
        "## Data Explorer",
        params.param.cmap,
        params.param.x_var,
        params.param.y_var,
        params.enable_slider_checkbox,
        params.z_score_threshold_slider,
        width=200,
    )
    return pn.Row(widget_column, update)