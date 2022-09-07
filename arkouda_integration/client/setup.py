from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))
# Long description will be contents of README
with open(path.join(here, "../README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="arkouda_integration",
    version="0.0.1",
    description="library for system integration with Arkouda",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["arkouda_integration"],
    python_requires=">=3.8",
    install_requires=["arkouda","kubernetes"],
)
