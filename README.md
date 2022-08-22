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

## Basic Examples
Basic examples of client-only and client-server extensions to [Arkouda](https://github.com/Bears-R-Us/arkouda):
- Client-only example: [arkouda_distance](https://github.com/Bears-R-Us/arkouda-contrib/tree/main/arkouda_distance)
- Client-server example: [arkouda_distance_wserver](https://github.com/Bears-R-Us/arkouda-contrib/tree/main/arkouda_distance_wserver)

## Installation

Installation is performed by running `module_configuration.py`. When running `module_configuration.py`, the complete path to the location of the Arkouda repo must be specified through the `ak_loc` flag along with the complete path to the Arkouda contrib repo module that you want to include. Example:
```
python3 module_configuration.py --ak_loc=/complete/path/to/arkouda/ --pkg_path=/complete/path/to/arkouda-
contrib/arkouda_distance_wserver/
```

After running this command, the result should be a couple of commands along the lines of:
```
pip install -U /complete/path/to/arkouda-contrib/arkouda_distance_wserver/client
cp /complete/path/to/arkouda/ServerModules.cfg ~/TmpServerModules.cfg.1660849671
ARKOUDA_SERVER_USER_MODULES=" /complete/path/to/arkouda-contrib/arkouda_distance_wserver/server/DistanceCalcMsg.chpl" ARKOUDA_CONFIG_FILE=~/TmpServerModules.cfg.1660849671 ARKOUDA_SKIP_CHECK_DEPS=true make -C /complete/path/to/arkouda
```

These commands will then need to be run and then the Arkouda server will be built including the module Arkouda contrib package specified.

For detailed package installation instructions please view [INSTALL.md](https://github.com/Bears-R-Us/arkouda-contrib/blob/main/INSTALL.md).

## Usage Notes

```python
import arkouda as ak
import yourModule
# Code using your module and Arkouda
```
