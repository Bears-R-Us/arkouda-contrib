from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))
# Long description will be contents of README
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="arkouda_metrics_exporter",
    version="0.0.1",
    description="Arkouda metrics exporter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["arkouda_metrics_exporter"],
    python_requires=">=3.8",
    install_requires=["arkouda","prometheus_client"],
)