<p align="center">
<<<<<<< HEAD
  <img src="./pictures/logo.png"/>
</p>

Arkouda Viz is a Python package built on top of the [Arkouda](https://github.com/Bears-R-Us/arkouda) library, enabling high-performance data visualization for large-scale datasets specialized for distributed systems. Arkouda is designed to allow data scientists and engineers to interactively work with data at scale, and Arkouda Viz extends this functionality by adding rich visualization capabilities.

Users can utilize this tool to create detailed and insightful visualizations of their datasets without the need for data aggregation or movement to a centralized environment. This is particularly valuable in scenarios where datasets are too large to fit into memory on a single machine, as Arkouda Viz seamlessly integrates with the parallel processing architecture of Arkouda.

## Data Visualizations Implemented
- 'area()' - Creates an area plot with or without a variable dropdown menu based on single or multiple columns.

- 'hist()' - Creates a histogram with or without a variable dropdown menu based on single or multiple columns.

- 'explore()' - Creates an interactive plot using datashader. The method then updates the plot based on the user's selections of a variety of widgets.

## Usage

Arkouda must be installed prior to use. See instructions [here](https://github.com/ItsQuinnMoore/arkouda?tab=readme-ov-file#prereqs).

In order to use the `explore()` method, you need to run the following code to update your Arkouda build configuration to support `arkouda.histogram2d()

```bash
sed -i '/"nd": \[1\]/s/\[1\]/[1, 2]/' $PATH_TO_ARKOUDA/registration-config.json
=======
  <img src="../pictures/logo.png"/>
</p>

This is a client only implementation of vizualizations using Arkouda. Thus, all code is python and uses only server elements currently included in the main arkouda repository. 

## Functionality Implemented

- 'datashade()' - Takes an Arkouda DataFrame along with optional parameters and creates an interactive plot using datashader. The method then updates the plot based on the user's selections of a variety of widgets.

- 'crossfilter()' - Takes an Arkouda Dataframe and creates a scatterplot with the widgets of size and color that manipulates the points.

## Usage

Arkouda must be installed prior to utilization.

```commandline
pip install arkouda
>>>>>>> main
```

In your code,

```python
<<<<<<< HEAD
import arkouda # as ak
import arkouda_viz # as akv
=======
import arkouda_viz
>>>>>>> main
```