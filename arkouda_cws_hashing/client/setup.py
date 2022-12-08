from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))
# Long description will be contents of README
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="lsh_minmax",
    version="0.0.1",
    description="Locality sensitive hashing/consistent weighted sampling for the MinMax (weighted Jaccard) distance.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["lsh_minmax"],
    python_requires=">=3.8",
    install_requires=["arkouda", "typeguard"],
)

