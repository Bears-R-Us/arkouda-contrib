"""Module providing our plotting capabilities."""
import holoviews as hv
import panel as pn
import panel.widgets as pnw
from arkouda.dataframe import DataFrame
from typeguard import typechecked
from holoviews.operation import datashader as ds

pn.extension()


def datashade(
    data: DataFrame,
    width: int = 500,
    height: int = 500,
    engine: str = "bokeh",
    point_size: int = 1,
):
    """Creates an interactive plot that can handle large datasets."""
    hv.extension(engine)

    data = data.to_pandas().select_dtypes(exclude=["object"])

    def make_data(x_col, y_col):
        return hv.Points((data[x_col], data[y_col]), label=f"{x_col} vs {y_col}").opts(
            size=point_size
        )

    column_names = list(data.columns)

    color_schemes = ["fire", "bgy", "gray", "kbc", "kb", "kgy"]

    x_widget = pn.widgets.Select(
        name="x data", options=column_names, value=column_names[0]
    )
    y_widget = pn.widgets.Select(
        name="y data", options=column_names, value=column_names[1]
    )
    color_widget = pn.widgets.Select(
        name="color scheme", options=color_schemes, value=color_schemes[0]
    )
    enable_slider_checkbox = pn.widgets.Checkbox(name="remove outliers", value=False)
    z_score_threshold_slider = pn.widgets.FloatSlider(
        name="z-score threshold", start=0.0, end=5, step=0.1, value=3.0
    )

    @pn.depends(
        x_widget.param.value,
        y_widget.param.value,
        color_widget.param.value,
        enable_slider_checkbox.param.value,
        z_score_threshold_slider.param.value,
    )
    def update_data(x_col, y_col, color_scheme, enable_slider, z_score_threshold):
        data_points = make_data(x_col, y_col)

        if enable_slider:
            z_scores = (
                data_points.data["y"] - data_points.data["y"].mean()
            ) / data_points.data["y"].std()
            data_points = data_points[abs(z_scores) < z_score_threshold]

        shaded_data = ds(data_points, cmap=color_scheme).opts(
            hv.opts.RGB(width=width, height=height)
        )

        shaded_data = shaded_data.opts(xlabel=f"{x_col}", ylabel=f"{y_col}")

        z_score_threshold_slider.disabled = not enable_slider

        return shaded_data

    logo = "../pictures/logo.png"
    logo_image = pn.panel(logo, width=x_widget.width, height=x_widget.height)
    layout = pn.Row(
        pn.Column(
            logo,
            x_widget,
            y_widget,
            color_widget,
            enable_slider_checkbox,
            z_score_threshold_slider,
        ),
        update_data,
    )

    tabs = pn.Tabs(("plot", layout))

    return tabs.servable()

    @pn.depends(x_widget.param.value, y_widget.param.value)
    def update_data(x_col, y_col):
        data_points = make_data(x_col, y_col)
        shaded_data = ds(data_points, cmap="viridis", color_key="log").opts(
            hv.opts.RGB(width=width, height=height)
        )
        return shaded_data

    logo = "../pictures/logo.png"
    layout = pn.Row(
        pn.Column("## Datashader Plot", logo_image, x_widget, y_widget), update_data
    )
    return layout.servable()


@typechecked
def crossfilter(
    data: DataFrame,
    width: int = 500,
    height: int = 500,
    engine: str = "bokeh",
    linecolor: str = "black",
    cmap="rainbow",
):
    """Takes an Arkouda Dataframe and creates a scatterplot with the widgets of size and color that manipulates the points."""
    hv.extension(engine)
    data = data.to_pandas()
    discrete = [x for x in data.columns if data[x].dtype == object]
    continuous = [x for x in data.columns if x not in discrete]
    quantileable = [x for x in continuous if len((data[x].unique())) > 20]

    x = pnw.Select(name="X-Axis", value=quantileable[0], options=quantileable)
    y = pnw.Select(name="Y-Axis", value=quantileable[0], options=quantileable)
    size = pnw.Select(name="Size", value="None", options=["None"] + quantileable)
    color = pnw.Select(name="Color", value="None", options=["None"] + quantileable)

    @pn.depends(x.param.value, y.param.value, color.param.value, size.param.value)
    def create_figure(x_data, y_data, color, size):
        opts = dict(cmap=cmap, width=width, height=height, linecolor=linecolor)
        if color != "None":
            opts["color"] = color
        if size != "None":
            opts["size"] = hv.dim(size).norm() * 20
        return hv.Points(
            data, [x_data, y_data], label=f"{x_data.title()} vs {y_data.title()}"
        ).opts(**opts)

    widgets = pn.WidgetBox(x, y, color, size, width=200)
    layout = pn.Row(widgets, create_figure).servable("Cross-selector")
    return layout.servable()
