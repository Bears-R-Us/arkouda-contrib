import holoviews as hv
import panel as pn
import panel.widgets as pnw
import param
from typeguard import typechecked
from typing import Union
from bokeh.io import output_notebook
import arkouda as ak

hv.extension("bokeh", logo=False)
pn.extension()
output_notebook()


def explore(
    data: Union[ak.DataFrame, tuple[ak.pdarray, ak.pdarray]] = None,
    xBin: int = 10,
    yBin: int = 10,
    xWin: int = 500,
    yWin: int = 500,
):
    if data is not None:
        if isinstance(data, ak.DataFrame):
            full_data = data

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

    cols = full_data.columns
    initial_xrange = (ak.min(full_data[cols[0]]), ak.max(full_data[cols[0]]))
    initial_yrange = (ak.min(full_data[cols[1]]), ak.max(full_data[cols[1]]))

    def make_data(x_range, y_range, cmap):
        if x_range is None or y_range is None or not x_range or not y_range:
            binned_data = ak.histogram2d(
                full_data[cols[0]], full_data[cols[1]], bins=(xBin, yBin)
            )
            return hv.Image(binned_data[0].to_ndarray(), bounds=(0, 0, 1, 1)).opts(
                cmap=cmap, width=xWin, height=yWin
            )
        else:
            subset_data = full_data[
                (full_data[cols[0]] >= x_range[0])
                & (full_data[cols[0]] <= x_range[1])
                & (full_data[cols[1]] >= y_range[0])
                & (full_data[cols[1]] <= y_range[1])
            ]

        x_span = x_range[1] - x_range[0]
        y_span = y_range[1] - y_range[0]
        binned_data = ak.histogram2d(
            subset_data[cols[0]], subset_data[cols[1]], bins=(1000, 1000)
        )
        return hv.Image(
            binned_data[0].to_ndarray(),
            bounds=(x_range[0], y_range[0], x_range[0] + x_span, y_range[0] + y_span),
        ).opts(cmap=cmap, width=xWin, height=yWin)

    class Explore(param.Parameterized):
        cmap = param.ObjectSelector(default="viridis", objects=hv.plotting.list_cmaps())

    params = Explore()

    @pn.depends(cmap=params.param.cmap)
    def update_plot(cmap):
        stream = hv.streams.RangeXY(x_range=initial_xrange, y_range=initial_yrange)
        dmap = hv.DynamicMap(
            lambda x_range, y_range: make_data(x_range, y_range, cmap), streams=[stream]
        )

        return dmap

    return pn.Row(params, update_plot)


@typechecked
def crossfilter(
    data: ak.DataFrame,
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
