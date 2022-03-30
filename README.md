# arkouda-contrib
a place for contributed functionality for arkouda

## Creating a Module

- All modules must include a `client` directory
  - `client` directory must include a `README.md` and `setup.py`.
  - The client module will be installed using `pip`. 
  - Install uses `setuptools`
- `server` directory is optional

## Installation

`module_configuration.py` is provided for easy set up. Currently, the script will print out commands that can be copied and run to configure Arkouda with your module. Currently, these commands cannot be piped due to an `export` that must be run manually.

### Install Parameters
- `path` - this is the full path to the module you want to configure. *REQUIRED*
- `ak` - this is the full path to the Arkouda installation on your machince. *REQUIRED when module contains a server element only*.

```commandline
python3 module_configuration.py --path <path to module> --ak <path to arkouda>
```

## Usage Notes

```python
import arkouda as ak
import yourModule
# Code using your module and Arkouda
```