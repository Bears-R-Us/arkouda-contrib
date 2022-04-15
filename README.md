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

`module_configuration.py` is provided for easy set up. Currently, the script will print out commands that can be copied and run to configure Arkouda with your module or piped into bash for immediate execution.

```commandline
# To see the commands that will be run
python3 module_configuration.py --path=<path_to_module> --ak=<path_to_arkouda>

# To automatically run the commands
python3 module_configuration.py --path=<path_to_module> --ak=<path_to_arkouda> | bash
```

### Install Parameters
- `path` - this is the full path to the module you want to configure. *REQUIRED*
- `ak` - this is the full path to the Arkouda installation on your machine. *REQUIRED when module contains a server element only*.

```commandline
python3 module_configuration.py --path <path to module> --ak <path to arkouda>
```

## Usage Notes

```python
import arkouda as ak
import yourModule
# Code using your module and Arkouda
```