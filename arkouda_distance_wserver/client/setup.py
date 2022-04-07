from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))
# Long description will be contents of README
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='arkouda_distance',
    version='0.0.1',
    description='Distance Computations for Arkouda pdarrays.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['arkouda_distance'],
    python_requires=">=3.7",
    install_requires=[
        'arkouda',
        'typeguard'
    ]
)