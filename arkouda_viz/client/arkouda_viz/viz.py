import arkouda as ak
import holoviews as hv
import panel as pn
import param
from typing import Tuple, Union, Optional

_numeric_types = ["float64", "int64", "uint64"]

"""
The plotting engine to be used by default
unless specified explicitly.
"""


default_engine = "matplotlib"


"""
Helper method for setting up the plot rendering environment.
Parameters
----------
engine : string
    The plotting engine; 'default_engine' by default.
width : int
    Width of the plot.
height : int
    Height of the plot.
Returns
-------
Dictionary
    Plot options for proper rendering in the environment.
"""


def render_env(engine: Optional[str], width: int, height: int):
    global default_engine
    if engine == None: engine = default_engine

    def ensure(name):
        if not hv.extension._loaded or hv.Store.current_backend != name:
            hv.extension(name)

    if engine in ("bokeh", "b"):
        ensure("bokeh")
        return dict(width=width, height=height)
    elif engine in ("plotly", "p"):
        ensure("plotly")
        return dict(width=width, height=height)
    elif engine in ("matplotlib", "m"):
        ensure("matplotlib")
        return dict(fig_inches=(int(width/100), int(height/100)))
    else:
        raise ValueError("Please provide a supported plotting engine.")


"""
Plots a histogram for numeric data as an area plot.
The X axis is always range(0, bins).
Parameters
----------
data : ak.DataFrame or ak.pdarray
    The data to be plotted.
bins : int
    Number of bins to divide the data into.
engine : string
    The plotting engine; 'default_engine' by default.
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
    bins: int = 10,
    engine: Optional[str] = None,
    width: int = 500,
    height: int = 500,
):
    opts = render_env(engine, width=width, height=height)
    if data is not None:
        if isinstance(data, ak.DataFrame):
            numeric_columns = [
                col
                for col, dtype in data.dtypes.items()
                if dtype in _numeric_types
            ]
            if len(numeric_columns) == 0:
                raise ValueError(
                    "The provided ak.DataFrame does not have at least one numeric columns."
                )
            data = data[numeric_columns]
            h, b = ak.histogram(data[data.columns[0]], bins=bins)
            var = pn.widgets.Select(
                name="variable", value=data.columns[0], options=data.columns.to_list()
            )
            all = pn.widgets.Checkbox(name="all")

            @pn.depends(var.param.value, all.param.value)
            def create_figure(var, all):
                if all:
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
        if isinstance(data, ak.pdarray) and data.dtype in _numeric_types:
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
    The plotting engine; 'default_engine' by default.
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
    engine: Optional[str] = None,
    width: int = 500,
    height: int = 500,
):
    opts = render_env(engine, width=width, height=height)
    if data is not None:
        if isinstance(data, ak.DataFrame):
            numeric_columns = [
                col
                for col, dtype in data.dtypes.items()
                if dtype in _numeric_types
            ]
            if len(numeric_columns) == 0:
                raise ValueError(
                    "The provided ak.DataFrame does not have at least one numeric columns."
                )
            data = data[numeric_columns]
            h, b = ak.histogram(data[data.columns[0]], bins=bins)
            var = pn.widgets.Select(
                name="variable", value=data.columns[0], options=data.columns.to_list()
            )

            @pn.depends(var.param.value)
            def create_figure(var):
                return hv.Histogram((h.to_ndarray(), b.to_ndarray())).opts(**opts)

            widgets = pn.WidgetBox(var, width=200)
            return pn.Row(widgets, create_figure).servable("Histogram")
        if isinstance(data, ak.pdarray) and data.dtype in _numeric_types:
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
    The plotting engine; 'default_engine' by default.
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
    engine: Optional[str] = None,
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
                name="variable", value=data.columns[0], options=data.columns.to_list()
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
                    hv.opts.HLine(color="red", line_width=2, xlim=(0, 1)),
                    hv.opts.Segments(color="black"),
                    hv.opts.Points(color="green"),
                )

            widgets = pn.WidgetBox(var, width=200)
            return pn.Row(widgets, create_figure).servable("Box and Whisker")
        if isinstance(data, ak.pdarray) and data.dtype in _numeric_types:
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
                hv.opts.HLine(color="red", line_width=2, xlim=(0, 1)),
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
    The plotting engine; 'bokeh' by default.
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
    xBin: int = 100,
    yBin: int = 100,
    engine: Optional[str] = "bokeh",
    width: int = 500,
    height: int = 500,
):
    opts = render_env(engine, width=width, height=height)
    pn.extension()
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
        elif (
            isinstance(data, tuple)
            and len(data) == 2
            and all(isinstance(item, ak.pdarray) for item in data)
        ):
            data = ak.DataFrame({"0":data[0], "1":data[1]})
            numeric_columns = ["0", "1"]
        else:
            raise ValueError(
                "Invalid data. Please provide an ak.Dataframe or (ak.pdarray, ak.pdarray)."
            )
    else:
        raise ValueError("Please provide data.")

    class Explore(param.Parameterized):
        cmap = param.Selector(
            label="color map", default="turbo", objects=hv.plotting.list_cmaps()
        )
        x_var = param.Selector(
            label="x-variable", default=numeric_columns[0], objects=numeric_columns
        )
        y_var = param.Selector(
            label="y-variable", default=numeric_columns[1], objects=numeric_columns
        )
        enable_slider_checkbox = pn.widgets.Checkbox(
            name="remove outliers", value=False
        )
        z_score_threshold_slider = pn.widgets.FloatSlider(
            name="z-score threshold", start=0.0, end=5, step=0.1, value=3.0
        )

    params = Explore()
    server_widget = pn.widgets.StaticText(name="", value="", styles = {'color': 'red'})

    # use caching to preserve the current range when changing the color map and to
    # avoid unnecessary re-histogramming, which sometimes happens with hv.streams
    class Cache: pass
    h_cache = Cache()
    h_cache.x_var, h_cache.y_var, h_cache.histo, h_cache.range2 = None, None, None, None

    def make_data(x_range, y_range, cmap, x_var, y_var, h_cache=h_cache):
        if x_var == h_cache.x_var and y_var == h_cache.y_var \
           and (x_range == None or (x_range, y_range) == h_cache.range2):
            histo, range2 = h_cache.histo, h_cache.range2
        else:
            if x_range == None: range = None
            else:               range = (x_range, y_range)
            server_widget.value = "server processing"
            histo,xbins,ybins = ak.histogram2d(data[x_var], data[y_var], bins=(xBin, yBin), range=range)
            server_widget.value = ""
            histo = histo.to_ndarray().T[::-1,:]
            range2 = ((xbins[0], xbins[-1]), (ybins[0], ybins[-1]))  # ((xmin,xmax),(ymin,ymax))
            h_cache.x_var, h_cache.y_var, h_cache.histo, h_cache.range2 = x_var, y_var, histo, range2

        return hv.Image(
            histo,
            bounds=(range2[0][0], range2[1][0], range2[0][1], range2[1][1])  # xmin, ymin, xmax, ymax
        ).opts(cmap=cmap, colorbar=True, **opts)

    @pn.depends(
        cmap=params.param.cmap, x_var=params.param.x_var, y_var=params.param.y_var
    )
    def update(cmap, x_var, y_var):
        stream = hv.streams.RangeXY()
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
        # these are currently unused:
        #params.enable_slider_checkbox,
        #params.z_score_threshold_slider,
        server_widget,
        width=200,
    )
    return pn.Row(widget_column, update)
