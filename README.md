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

## Installation

`module_configuration.py` is provided for easy set up. Currently, the script will print out commands that can be copied and run to configure Arkouda with your module. Currently, these commands cannot be piped due to an `export` that must be run manually.

### Install Parameters
- `path` - this is the full path to the module you want to configure. *REQUIRED*
- `ak` - this is the full path to the Arkouda installation on your machince. *REQUIRED when module contains a server element only*.

```commandline
python3 module_configuration.py --path <path to module> --ak <path to arkouda>
```

#### Defining Tests

In the `test` directory of your module, you will need to define testing for the newly defined functionality. At the same level as your `test` directory, be sure to define `pytest.ini`.

```text
[pytest]
filterwarnings =
    ignore:Version mismatch between client .*
testpaths =
    test/pkg1_test.py
    test/pkg2_test.py
    .
    .
    .
    test/pkgn_test.py
python_functions = test*
env =
    D:ARKOUDA_SERVER_HOST=localhost
    D:ARKOUDA_SERVER_PORT=5555
    D:ARKOUDA_RUNNING_MODE=CLASS_SERVER
    D:ARKOUDA_NUMLOCALES=2
    D:ARKOUDA_VERBOSE=True
    D:ARKOUDA_CLIENT_TIMEOUT=0
    D:ARKOUDA_LOG_LEVEL=DEBUG
```
**NOTE** - All methods within test files should be named following this format `def test_<my_functionality_name>`.

To run your tests,
```commandline
python3 -m pytest /path_to_module/test/test_file.py
```

## Usage Notes

```python
import arkouda as ak
import yourModule
<<<<<<< HEAD
=======

>>>>>>> 53bb761 (Updated documentation. Updated module configuration. Updated build process. This will work if user manually runs printed commands.)
# Code using your module and Arkouda
```