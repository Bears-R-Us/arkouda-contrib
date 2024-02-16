from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))
# Long description will be contents of README
with open(path.join(here, "..", "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="arkouda_viz",
    version="0.0.0",
    description="Vizualizations for Arkouda.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["arkouda_viz"],
    python_requires=">=3.8",
    install_requires=["arkouda", "holoviews", "datashader"],
)
