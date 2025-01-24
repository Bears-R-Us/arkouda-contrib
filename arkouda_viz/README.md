<p align="center">
  <img src="pictures/logo.png"/>
</p>

This is a client only implementation of vizualizations using Arkouda. Thus, all code is python and uses only server elements currently included in the main arkouda repository. 

## Functionality Implemented

- 'hist()' - Plots a histogram for numeric data.

- 'area()' - Plots a histogram for numeric data as an area plot.

- 'boxWhisker()' - Plots a box plot for numeric data.

- 'explore()' - Creates an interactive 2-D histogram for numeric data.

## Usage

Arkouda must be installed prior to utilization.

```commandline
pip install arkouda
```

In your code,

```python
import arkouda_viz
```