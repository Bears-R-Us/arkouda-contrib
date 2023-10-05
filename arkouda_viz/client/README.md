<p align="center">
  <img src="pictures/logo.png"/>
</p>

This is a client only implementation of vizualizations using Arkouda. Thus, all code is python and uses only server elements currently included in the main arkouda repository. 

## Functionality Implemented

- 'datashade()' - Takes an Arkouda DataFrame along with optional parameters and creates an interactive plot using datashader. The method then updates the plot based on the user's selections of a variety of widgets.

- 'crossfilter()' - Takes an Arkouda Dataframe and creates a scatterplot with the widgets of size and color that manipulates the points.

## Usage

Arkouda must be installed prior to utilization.

```commandline
pip install arkouda
```

In your code,

```python
import arkouda_viz
```