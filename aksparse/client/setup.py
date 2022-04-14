from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
        name='aksparse',
        version='1.0.0',
        author="U.S. Government",
        author_email="",
        description="Sparse matrix operations for arkouda",
        long_description=long_description,
        long_decription_content_type="text/markdown",
        keywords="HPC exploratory analysis parallel distribute arrays Chapel sparse matrix linear",
        packages=setuptools.find_packages(),
        classifiers=[
            "Programming Language :: Python :: 3"
        ],
        install_requires=['numpy', 'pandas', 'scipy'],
        python_requires='>= 3.6',
        project_urls={
            'Bug Reports': 'https://github.com/Bear-R-Us/arkouda/issues',
        }
)
