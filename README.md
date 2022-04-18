# arkouda-contrib
a place for contributed functionality for arkouda

## Creating a Module

- All modules must include a `client` directory
  - `client` directory must include a `README.md` and `setup.py`.
  - The client module will be installed using `pip`. 
  - Install uses `setuptools`
- `test` directory is REQUIRED
  - `pytest.ini` is also required in the top level of your module.
- `server` directory is optional

*For more details, visit [CONTRIBUTING.md](https://github.com/Bears-R-Us/arkouda-contrib/blob/main/CONTRIBUTING.md)*.

## Installation

Installation is performed by running `module_configuration.py`. For detailed package installation instructions please view [INSTALL.md](https://github.com/Bears-R-Us/arkouda-contrib/blob/main/INSTALL.md).

## Usage Notes

```python
import arkouda as ak
import yourModule
# Code using your module and Arkouda
```