from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))
# Long description will be contents of README
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="aklisp",
    version="0.0.1",
    description="Lisp expression computation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["aklisp"],
    python_requires=">=3.10",
    install_requires=["arkouda", "typeguard"],
)
