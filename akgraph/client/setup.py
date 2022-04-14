from setuptools import setup, find_packages
from os import path


HERE = path.abspath(path.dirname(__file__))
with open(path.join(HERE, 'README.md'), encoding='utf-8') as fh:
    LONG_DESCRIPTION = fh.read()

setuptools.setup(
    name='akgraph',
    version='0.2.0',
    author="U.S. Government",
    author_email="",
    description="Graph algorithms in arkouda",
    long_description=LONG_DESCRIPTION,
    long_decription_content_type="text/markdown",
    keywords="HPC graph algorithm",
    packages=setuptools.find_packages(),
    classifiers=["Programming Language :: Python :: 3"],
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    install_requires=['h5py','numpy'],
    python_requires='>=3.6',
    project_urls={
        'Bug Reports': 'https://github.com/Bears-R-Us/arkouda/issues',
    }
)
