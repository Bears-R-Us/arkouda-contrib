
import arkouda as ak
import geopandas as gpd
import holoviews as hv
import math
import matplotlib.pyplot as plt
import numpy as np
import panel as pn
import param
import plotly.figure_factory as ff

from bokeh.models import HoverTool
from bokeh.palettes import Category10
from bokeh.plotting import figure
from holoviews.operation.datashader import datashade, rasterize
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
dpi : int
    Dots per inch of the plot if matplotlib is used as the engine.
Returns
-------
Dictionary
    Plot options for proper rendering in the environment.
"""


def render_env(engine: str, width: int, height: int, dpi: int):
    if engine in ("bokeh", "b"):
        hv.extension("bokeh", inline=True, logo=False)
        return dict(width=width, height=height)
    elif engine in ("plotly", "p"):
        hv.extension("plotly", inline=True, logo=False)
        return dict(width=width, height=height)
    elif engine in ("matplotlib", "m"):
        hv.extension("matplotlib", inline=True, logo=False)
        fig_inches = (width / dpi, height / dpi)
        return dict(fig_inches=fig_inches, aspect=width/height)
    else:
        raise ValueError("Please provide a supported plotting engine.")

"""
Plots a scatter plot for numeric data.
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
dpi : int
    Dots per inch of the plot if matplotlib is used as the engine.
color : string
    Color for the points.
Returns
-------
hv.Area()
    An area plot with or without a variable dropdown menu based in single or multiple columns.
"""

def scatter(
    data: Union[ak.DataFrame, Tuple[ak.pdarray, ak.pdarray]] = None,
    engine: str = "matplotlib",
    width: int = 500,
    height: int = 500,
    dpi: int = 100,
):
    opts = render_env(engine, width=width, height=height, dpi=dpi)
    pn.config.throttled = True

    if data:
        if isinstance(data, ak.DataFrame):
            numeric_columns = [
                col for col, dtype in data.dtypes.items() if dtype in ["float64", "int64"]
            ]
            if len(numeric_columns) < 2:
                raise ValueError(
                    "The provided ak.DataFrame does not have at least two numeric columns."
                )
            data = data[numeric_columns]
            x_var_widget = pn.widgets.Select(
                name="x-variable", value=data.columns[0], options=list(data.columns)
            )
            y_var_widget = pn.widgets.Select(
                name="y-variable", value=data.columns[1], options=list(data.columns)
            )
            color_widget = pn.widgets.ColorPicker(name="color", value='#1f77b4')
            size_widget = pn.widgets.IntSlider(
                name="size", start=1, end=20, step=1, value=5
            )

            @pn.depends(x_var_widget.param.value, y_var_widget.param.value, color_widget.param.value, size_widget.param.value)
            def create_figure(x_var, y_var, color, size):
                x_data = data[x_var]
                y_data = data[y_var]
                scatter = hv.Scatter((x_data.to_ndarray(), y_data.to_ndarray()))
                if engine == "matplotlib":
                    fig, ax = plt.subplots(figsize=(width / dpi, height / dpi))
                    ax.scatter(x_data.to_ndarray(), y_data.to_ndarray(), color=color, s=size)
                    ax.set_xlabel(x_var)
                    ax.set_ylabel(y_var)
                    return fig

                elif engine == "bokeh":
                    p = figure(width=width, height=height)
                    p.scatter(x_data.to_ndarray(), y_data.to_ndarray(), color=color, size=size)
                    p.xaxis.axis_label = x_var
                    p.yaxis.axis_label = y_var
                    return p

                elif engine == "plotly":
                    fig = hv.Scatter((x_data.to_ndarray(), y_data.to_ndarray())).opts(
                        color=color,
                        size=size,
                        xlabel=x_var,
                        ylabel=y_var,
                        **opts
                    ).to_plotly()
                    return fig

            widgets = pn.WidgetBox(x_var_widget, y_var_widget, color_widget, size_widget, width=200)
            return pn.Row(widgets, pn.pane.Matplotlib(create_figure) if engine == "matplotlib" else create_figure).servable("Scatter Plot")

        elif isinstance(data, tuple) and len(data) == 2 and all(isinstance(item, ak.pdarray) for item in data):
            x_data = data[0]
            y_data = data[1]
            if engine == "matplotlib":
                fig, ax = plt.subplots(figsize=(width / dpi, height / dpi))
                ax.scatter(x_data.to_ndarray(), y_data.to_ndarray())
                ax.set_xlabel("X")
                ax.set_ylabel("Y")
                return pn.pane.Matplotlib(fig).servable("Scatter Plot")

            elif engine == "bokeh":
                p = figure(width=width, height=height)
                p.scatter(x_data.to_ndarray(), y_data.to_ndarray())
                p.xaxis.axis_label = "X"
                p.yaxis.axis_label = "Y"
                return p

            elif engine == "plotly":
                fig = hv.Scatter((x_data.to_ndarray(), y_data.to_ndarray())).opts(
                    xlabel="X",
                    ylabel="Y",
                    **opts
                ).to_plotly()
                return pn.pane.Plotly(fig).servable("Scatter Plot")

        else:
            raise ValueError(
                "Invalid data. Please provide an ak.DataFrame or a tuple of two ak.pdarray."
            )
    else:
        raise ValueError("No data was provided.")
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
dpi : int
    Dots per inch of the plot if matplotlib is used as the engine.
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
    dpi: int = 100
):
    opts = render_env(engine, width=width, height=height, dpi=dpi)
    pn.config.throttled = True

    if data:
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
            stack_widget = pn.widgets.Checkbox(name="stack")
            var_widget = pn.widgets.Select(
                name="variable", value=data.columns[0], options=list(data.columns), sizing_mode = 'stretch_width'
            )
            opacity_widget = pn.widgets.FloatSlider(
                name="opacity", start=0.5, end=1, step=0.1, value=0.5, sizing_mode = 'stretch_width', disabled=True
            )
            bins_widget = pn.widgets.IntSlider(
                name="bins", start=1, end=width, step=1, value=bins, sizing_mode='stretch_width'
            )
            log_scale_widget = pn.widgets.Checkbox(name="log scale", value=False)
            color_widget = pn.widgets.ColorPicker(name="color", value='#1f77b4')


            @pn.depends(
                all_widget.param.value,
                stack_widget.param.value,
                var_widget.param.value,
                opacity_widget.param.value,
                bins_widget.param.value,
                log_scale_widget.param.value,
                color_widget.param.value,
            )
            def create_figure(all, stack, var, opacity_value, bins, log_scale, color):
                color_palette = Category10[len(data.columns)] if len(data.columns) <= 10 else pn.palettes.Plasma[len(data.columns)]

                if all:
                    overlay = hv.Overlay()
                    for idx, column in enumerate(data.columns):
                        h, b = ak.histogram(data[column], bins=bins)
                        overlay *= hv.Area(
                            (b[:-1].to_ndarray(), h.to_ndarray()), label=column
                        ).opts(
                            alpha=opacity_value,
                            xlabel="all variables",
                            ylabel="count",
                            logy=log_scale,
                            color=color_palette[idx],
                            **opts,
                        )
                    return overlay.opts(legend_position="top_right", **opts)

                elif stack:
                    overlays = []
                    cumulative = np.zeros(bins)
                    for idx, column in enumerate(data.columns):
                        h, b = ak.histogram(data[column], bins=bins)
                        cumulative += h.to_ndarray()
                        overlays.append(
                            hv.Area((b[:-1].to_ndarray(), cumulative), label=column).opts(
                                alpha=opacity_value,
                                xlabel="all variables",
                                ylabel="count",
                                logy=log_scale,
                                color=color_palette[idx],
                                **opts,
                            )
                        )
                    return hv.Overlay(overlays).opts(legend_position="top_right", **opts)

                else:
                    h, b = ak.histogram(data[var], bins=bins)
                    return hv.Area((b[:-1].to_ndarray(), h.to_ndarray())).opts(
                        xlabel=var, ylabel="count", logy=log_scale, color=color, **opts
                    )

            def handle_checkbox_change(event):
                if event.obj.name == "all":
                    stack_widget.disabled = event.new
                    var_widget.disabled = event.new
                    opacity_widget.disabled = not event.new
                    color_widget.disabled = event.new
                elif event.obj.name == "stack":
                    all_widget.disabled = event.new
                    var_widget.disabled = event.new
                    opacity_widget.disabled = event.new
                    color_widget.disabled = event.new

            all_widget.param.watch(handle_checkbox_change, "value")
            stack_widget.param.watch(handle_checkbox_change, "value")

            widgets = pn.WidgetBox(
                var_widget, all_widget, stack_widget, opacity_widget, bins_widget, log_scale_widget, color_widget, width=200, sizing_mode = 'stretch_height'
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
dpi : int
    Dots per inch of the plot if matplotlib is used as the engine.
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
    dpi: int = 100,
):
    opts = render_env(engine, width=width, height=height, dpi=dpi)
    pn.config.throttled = True

    if data:
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
            var_widget = pn.widgets.Select(
                name="variable", value=data.columns[0], options=list(data.columns)
            )

            @pn.depends(var_widget.param.value)
            def create_figure(var):
                h, b = ak.histogram(data[var], bins=bins)
                return hv.Histogram((h.to_ndarray(), b.to_ndarray())).opts(**opts)

            widgets = pn.WidgetBox(
                var_widget, width=200, sizing_mode = 'stretch_height'
            )
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
    dpi: int = 100,
    background: str = "any",
):
    render_env(engine, width=width, height=height, dpi=dpi)
    pn.extension()
    pn.config.throttled = True
    full_data = None
    if data is not None:
        if isinstance(data, ak.DataFrame):
            numeric_columns = [
                col
                for col, dtype in data.dtypes.items()
                if dtype in ["int64", "uint64", "float64"]
            ]

            string_columns = [
                col for col, dtype in data.dtypes.items() if dtype in ["str"]
            ]

            if len(numeric_columns) < 2:
                raise ValueError(
                    "The provided DataFrame does not have at least two numeric columns."
                )
            full_data = data[numeric_columns + string_columns]
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

        string_params = {}
        for s in range(len(string_columns)):
            curr = pn.widgets.MultiSelect(
                name=string_columns[s],
                value=list(ak.unique(data[string_columns[s]]).to_ndarray()),
                options=list(ak.unique(data[string_columns[s]]).to_ndarray()),
                size=8,
            )
            string_params[string_columns[s]] = curr

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
        **kwargs,
    ):

        data = full_data

        if kwargs:
            for key in kwargs:
                vals = kwargs[key]
                col = key
                data = data[data[col].isin(vals)]

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
                    HoverTool(
                        tooltips=[(x_var, "$x"), (y_var, "$y"), ("count", "@image")]
                    )
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
                binned_data = ak.ArrayView(ak.log(binned_data.base), binned_data.shape)

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
                    HoverTool(
                        tooltips=[(x_var, "$x"), (y_var, "$y"), ("count", "@image")]
                    )
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
        **params.string_params,
    )
    def update(
        cmap,
        x_var,
        y_var,
        x_bin,
        y_bin,
        remove_outliers,
        log_checkbox,
        z_score,
        **kwargs,
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
                **kwargs,
            ),
            streams=[stream],
        )

        return dmap

    widget_column = pn.Column(
        "## Data Explorer",
        params.param.cmap,
        params.param.x_var,
        params.param.y_var,
        *params.string_params,
        params.param.x_bin,
        params.param.y_bin,
        pn.Row(params.enable_slider_checkbox, params.log_checkbox),
        params.z_score_threshold_slider,
        params.status_spinner,
        width=310,
    )
    return pn.Row(widget_column, update)

def line_plot(
    data: Union[ak.DataFrame, ak.pdarray] = None,
    engine: str = "matplotlib",
    width: int = 500,
    height: int = 500,
    dpi: int = 100
):
    opts = render_env(engine, width=width, height=height, dpi=dpi)
    pn.config.throttled = True

    if data:
        if isinstance(data, ak.DataFrame):
            numeric_columns = [
                col for col, dtype in data.dtypes.items() if dtype in ["float64", "int64"]
            ]
            if len(numeric_columns) == 0:
                raise ValueError(
                    "The provided ak.DataFrame does not have at least one numeric column."
                )
            data = data[numeric_columns]
            var_widget = pn.widgets.Select(
                name="variable", value=data.columns[0], options=list(data.columns)
            )

            @pn.depends(var_widget.param.value)
            def create_figure(var):
                return hv.Curve((np.arange(len(data[var])), data[var].to_ndarray())).opts(
                    xlabel='Index', ylabel=var, **opts
                )

            widgets = pn.WidgetBox(var_widget, width=200)
            return pn.Row(widgets, create_figure).servable("Line Plot")
        elif isinstance(data, ak.pdarray) and data.dtype in ["int64", "float64"]:
            return hv.Curve((np.arange(len(data)), data.to_ndarray())).opts(**opts)
        else:
            raise ValueError(
                f"Please provide data in the form of an ak.pdarray instead of {str(type(data))}."
            )
    else:
        raise ValueError("No data was provided.")


def hexbin(
    data: Union[ak.DataFrame, Tuple[ak.pdarray, ak.pdarray]] = None,
    gridsize: int = 50,
    cmap: str = "Blues",
    engine: str = "matplotlib",
    width: int = 500,
    height: int = 500,
    dpi: int = 100,
):
    opts = render_env(engine, width=width, height=height, dpi=dpi)
    pn.config.throttled = True

    if data:
        if isinstance(data, ak.DataFrame):
            numeric_columns = [
                col for col, dtype in data.dtypes.items() if dtype in ["float64", "int64"]
            ]
            if len(numeric_columns) < 2:
                raise ValueError(
                    "The provided ak.DataFrame does not have at least two numeric columns."
                )
            data = data[numeric_columns]
            x_var_widget = pn.widgets.Select(
                name="x-variable", value=data.columns[0], options=list(data.columns)
            )
            y_var_widget = pn.widgets.Select(
                name="y-variable", value=data.columns[1], options=list(data.columns)
            )

            @pn.depends(x_var_widget.param.value, y_var_widget.param.value)
            def create_figure(x_var, y_var):
                x_data = data[x_var]
                y_data = data[y_var]
                
                hist, x_edges, y_edges = ak.histogram2d(x_data, y_data, bins=gridsize)

                if engine == "matplotlib":
                    fig, ax = plt.subplots(figsize=(width / dpi, height / dpi))
                    hb = ax.hexbin(x_edges[:-1], y_edges[:-1], C=hist.to_ndarray().flatten(), gridsize=gridsize, cmap=cmap)
                    ax.set_xlabel(x_var)
                    ax.set_ylabel(y_var)
                    cb = fig.colorbar(hb, ax=ax)
                    cb.set_label('Counts')
                    return fig

                elif engine == "bokeh":
                    p = figure(width=width, height=height, tools="hover", match_aspect=True)
                    bins = hist.to_ndarray()
                    hexbin = p.hexbin(x_edges[:-1], y_edges[:-1], size=gridsize, orientation="pointytop", fill_color=cmap)
                    mapper = LinearColorMapper(palette=cmap, low=bins.min(), high=bins.max())
                    color_bar = ColorBar(color_mapper=mapper, label_standoff=12, location=(0,0), title='Counts')
                    p.add_layout(color_bar, 'right')
                    p.xaxis.axis_label = x_var
                    p.yaxis.axis_label = y_var
                    return p

                elif engine == "plotly":
                    fig = ff.create_hexbin_mapbox(
                        data_frame=data.to_pandas(),
                        lat=x_var,
                        lon=y_var,
                        nx_hexagon=gridsize,
                        color_continuous_scale=cmap
                    )
                    fig.update_layout(width=width, height=height)
                    return fig

            widgets = pn.WidgetBox(x_var_widget, y_var_widget, width=200)
            return pn.Row(widgets, pn.pane.Matplotlib(create_figure) if engine == "matplotlib" else create_figure).servable("Hexbin Plot")

        elif isinstance(data, tuple) and len(data) == 2 and all(isinstance(item, ak.pdarray) for item in data):
            x_data = data[0]
            y_data = data[1]

            hist, x_edges, y_edges = ak.histogram2d(x_data, y_data, bins=gridsize)

            if engine == "matplotlib":
                fig, ax = plt.subplots(figsize=(width / dpi, height / dpi))
                hb = ax.hexbin(x_edges[:-1], y_edges[:-1], C=hist.to_ndarray().flatten(), gridsize=gridsize, cmap=cmap)
                ax.set_xlabel("X")
                ax.set_ylabel("Y")
                cb = fig.colorbar(hb, ax=ax)
                cb.set_label('Counts')
                return pn.pane.Matplotlib(fig).servable("Hexbin Plot")

            elif engine == "bokeh":
                p = figure(width=width, height=height, tools="hover", match_aspect=True)
                bins = hist.to_ndarray()
                hexbin = p.hexbin(x_edges[:-1], y_edges[:-1], size=gridsize, orientation="pointytop", fill_color=cmap)
                mapper = LinearColorMapper(palette=cmap, low=bins.min(), high=bins.max())
                color_bar = ColorBar(color_mapper=mapper, label_standoff=12, location=(0,0), title='Counts')
                p.add_layout(color_bar, 'right')
                p.xaxis.axis_label = "X"
                p.yaxis.axis_label = "Y"
                return p

            elif engine == "plotly":
                fig = ff.create_hexbin_mapbox(
                    data_frame={"x": x_data.to_ndarray(), "y": y_data.to_ndarray()},
                    lat="x",
                    lon="y",
                    nx_hexagon=gridsize,
                    color_continuous_scale=cmap
                )
                fig.update_layout(width=width, height=height)
                return pn.pane.Plotly(fig).servable("Hexbin Plot")

        else:
            raise ValueError(
                "Invalid data. Please provide an ak.DataFrame or a tuple of two ak.pdarray."
            )
    else:
        raise ValueError("No data was provided.")