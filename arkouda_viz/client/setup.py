from os import path
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))
# Long description will be contents of README
with open(path.join(here, "..", "README.md"), encoding="utf-8") as f:
    long_description = f.read()

requirements = [
    "arkouda",
    "holoviews",
    "datashader",
    "panel",
    "param",
    "numpy",
    "bokeh"
]

setup(
    name="arkouda_viz",
    description="Visualizations for Arkouda.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Bears-R-Us/arkouda-contrib/tree/main/arkouda_viz",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.9, <3.12.4",
)