from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))
# Long description will be contents of README
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="arkouda_distance",
    version="0.0.2",
    description="Distance Computations for Arkouda pdarrays.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["arkouda_distance"],
    python_requires=">=3.8",
    install_requires=["arkouda"],
)
