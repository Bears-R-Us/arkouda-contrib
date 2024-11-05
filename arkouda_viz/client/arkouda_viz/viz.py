import arkouda as ak
import holoviews as hv
import panel as pn
import param
from typing import Tuple, Union
import numpy as np
import math
from bokeh.models import HoverTool

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
    if engine in ("bokeh", "b"):
        hv.extension("bokeh", inline=True, logo=False)
        return dict(width=width, height=height)
    elif engine in ("plotly", "p"):
        hv.extension("plotly", inline=True, logo=False)
        return dict(width=width, height=height)
    elif engine in ("matplotlib", "m"):
        hv.extension("matplotlib", inline=True, logo=False)
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
            h = ak.histogram(data[data.columns[0]], bins=bins)[0]

            all_widget = pn.widgets.Checkbox(name="all")
            var_widget = pn.widgets.Select(
                name="variable", value=data.columns[0], options=list(data.columns), width=180
            )
            opacity_widget = pn.widgets.FloatSlider(
                name="opacity", start=0.5, end=1, step=0.1, value=0.5, width=180
            )

            @pn.depends(
                all_widget.param.value,
                var_widget.param.value,
                opacity_widget.param.value,
            )
            def create_figure(all, var, opacity_value):
                if all:
                    overlay = hv.Overlay()
                    for column in data.columns:
                        h, b = ak.histogram(data[column], bins=bins)
                        overlay *= hv.Area(
                            (b[:-1].to_ndarray(), h.to_ndarray()), label=column
                        ).opts(
                            alpha=opacity_value,
                            xlabel="all variables",
                            ylabel="count",
                            **opts,
                        )
                    return overlay.opts(legend_position="top_right", **opts)

                else:
                    h, b = ak.histogram(data[var], bins=bins)
                    return hv.Area((b[:-1].to_ndarray(), h.to_ndarray())).opts(
                        xlabel=var, ylabel="count", **opts
                    )

            def handle_checkbox_change(event):
                if event.obj.name == "all":
                    var_widget.disabled = event.new

            all_widget.param.watch(handle_checkbox_change, "value")

            widgets = pn.WidgetBox(
                var_widget, all_widget, opacity_widget, width=200
            )
            return pn.Row(widgets, create_figure).servable("Area")
        if isinstance(data, ak.pdarray) and data.dtype in ["int64", "float64"]:
            h = ak.histogram(data, bins=bins)[0]
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
                name="variable", value=data.columns[0], options=list(data.columns), width=180
            )

            @pn.depends(var.param.value)
            def create_figure(var):
                h, b = ak.histogram(data[var], bins=bins)
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
Plots a scatter plot for numeric data.
Parameters
----------
data : ak.pdarray
    The data to be plotted.
"""


def scatter(data: ak.pdarray = None):
    return hv.Scatter(data.to_ndarray())

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
background : string
    The backround color expected for the map.
Returns
-------
hv.Image().
    An image with or without a variable dropdown menu based in single or multiple columns.
"""


def explore(
    data: Union[ak.DataFrame, Tuple[ak.pdarray, ak.pdarray]] = None,
    xbins: int = 100,
    ybins: int = 100,
    engine: str = "bokeh",
    width: int = 500,
    height: int = 500,
    background: str = "any",
):
    render_env(engine, width=width, height=height)
    pn.extension()
    pn.config.throttled = True
    full_data = None
    if data is not None:
        if isinstance(data, ak.DataFrame):
            numeric_columns = [
                col
                for col, dtype in data.dtypes.items()
                if dtype in ["float64", "int64", "uint64"]
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
            label="color map",
            default="Bokeh",
            objects=hv.plotting.list_cmaps(
                reverse=False, bg=background, provider="bokeh"
            ),
        )
        x_var = param.Selector(
            label="x-variable", default=data.columns[0], objects=data.columns
        )
        y_var = param.Selector(
            label="y-variable", default=data.columns[1], objects=data.columns
        )

        x_bin = param.Integer(label="x-bin", default=xbins, bounds=(1, width))
        y_bin = param.Integer(label="y-bin", default=ybins, bounds=(1, height))

        enable_slider_checkbox = pn.widgets.Checkbox(
            name="remove outliers", value=False
        )

        log_checkbox = pn.widgets.Checkbox(name="log", value=False)

        z_score_threshold_slider = pn.widgets.FloatSlider(
            name="z-score threshold",
            start=0.0,
            end=5,
            step=0.1,
            value=3.0,
        )
        status_spinner = pn.widgets.LoadingSpinner(value=False, size=50, name="idle")

    params = Explore()

    def make_data(
        x_range,
        y_range,
        cmap,
        x_var,
        y_var,
        x_bin,
        y_bin,
        remove_outliers,
        log_checkbox,
        z_score,
    ):

        data = full_data

        if remove_outliers:
            params.status_spinner.value = True
            params.status_spinner.name = "removing outliers ..."
            params.status_spinner.color = "primary"
            z_scores_1 = (data[x_var] - ak.mean(data[x_var])) / ak.std(data[x_var])
            z_scores_2 = (data[y_var] - ak.mean(data[y_var])) / ak.std(data[y_var])

            var1 = data[x_var][ak.abs(z_scores_1) <= z_score]
            var2 = data[y_var][ak.abs(z_scores_2) <= z_score]

            data = data[ak.in1d(data[x_var], var1) & ak.in1d(data[y_var], var2)]

        if x_range is None or y_range is None or not x_range or not y_range:
            params.status_spinner.value = True
            params.status_spinner.name = "calculating bins ..."
            params.status_spinner.color = "primary"
            binned_data = ak.histogram2d(data[x_var], data[y_var], bins=(x_bin, y_bin))[
                0
            ]

            if log_checkbox:
                params.status_spinner.name = "log transforming ..."
                binned_data = ak.ArrayView(ak.log(binned_data.base), binned_data.shape)
            params.status_spinner.name = "rendering ..."
            params.status_spinner.color = "success"
            return hv.Image(
                np.rot90(binned_data.to_ndarray()), bounds=(0, 0, 1, 1)
            ).opts(
                cmap=cmap,
                width=width,
                height=height,
                xlabel=x_var,
                ylabel=y_var,
                color_bar=True,
                tools=[
                    HoverTool(tooltips=[("x", "$x"), ("y", "$y"), ("count", "@image")])
                ],
            )
        else:
            params.status_spinner.value = True
            params.status_spinner.name = "calculating bins ..."
            params.status_spinner.color = "primary"
            subset_data = data[
                (data[x_var] >= x_range[0])
                & (data[x_var] <= x_range[1])
                & (data[y_var] >= y_range[0])
                & (data[y_var] <= y_range[1])
            ]
            x_span = x_range[1] - x_range[0]
            y_span = y_range[1] - y_range[0]
            binned_data = ak.histogram2d(
                subset_data[x_var], subset_data[y_var], bins=(x_bin, y_bin)
            )[0]

            if log_checkbox:
                params.status_spinner.name = "log transforming ..."
                binned_data = ak.log(ak.where(binned_data > 0, binned_data, 1))
                #binned_data = ak.ArrayView(ak.log(binned_data.base), binned_data.shape)

            params.status_spinner.name = "rendering ..."
            params.status_spinner.color = "success"
            return hv.Image(
                np.rot90(binned_data.to_ndarray()),
                bounds=(
                    x_range[0],
                    y_range[0],
                    x_range[0] + x_span,
                    y_range[0] + y_span,
                ),
            ).opts(
                cmap=cmap,
                width=width,
                height=height,
                xlabel=x_var,
                ylabel=y_var,
                colorbar=True,
                tools=[
                    HoverTool(tooltips=[("x", "$x"), ("y", "$y"), ("count", "@image")])
                ],
            )

    @pn.depends(
        cmap=params.param.cmap,
        x_var=params.param.x_var,
        y_var=params.param.y_var,
        x_bin=params.param.x_bin,
        y_bin=params.param.y_bin,
        remove_outliers=params.enable_slider_checkbox.param.value,
        log_checkbox=params.log_checkbox.param.value,
        z_score=params.z_score_threshold_slider,
    )
    def update(
        cmap, x_var, y_var, x_bin, y_bin, remove_outliers, log_checkbox, z_score
    ):
        params.z_score_threshold_slider.disabled = not remove_outliers

        initial_xrange = (
            float(math.floor(ak.min(full_data[x_var]))),
            float(math.ceil(ak.max(full_data[x_var]))),
        )

        initial_yrange = (
            float(math.floor(ak.min(full_data[y_var]))),
            float(math.ceil(ak.max(full_data[y_var]))),
        )

        stream = hv.streams.RangeXY(x_range=initial_xrange, y_range=initial_yrange)
        dmap = hv.DynamicMap(
            lambda x_range, y_range: make_data(
                x_range,
                y_range,
                cmap,
                x_var,
                y_var,
                x_bin,
                y_bin,
                remove_outliers,
                log_checkbox,
                z_score,
            ),
            streams=[stream],
        )
        return dmap

    widget_column = pn.Column(
        "## Data Explorer",
        params.param.cmap,
        params.param.x_var,
        params.param.y_var,
        params.param.x_bin,
        params.param.y_bin,
        pn.Row(params.enable_slider_checkbox, params.log_checkbox),
        params.z_score_threshold_slider,
        params.status_spinner,
        width=310,
    )
    return pn.Row(widget_column, update)