# arkouda-contrib Package Installations

`module_configuration.py` is used for installation of packages. This will handle packages that are client only and those that include server modules. The script is configured to print the commands required to run arkouda with your desired package.

## Pull the Package(s) from GitHub

You can either clone the entire `arkouda-contrib` repository or use sparse-checkout to only checkout the packages you will be using.

```commandline
# Clone entire Repository
git clone https://github.com/Bears-R-Us/arkouda-contrib.git

# Only Checkout Desired Packages
mkdir arkouda_ext
cd arkouda_ext
git init
git remote add origin -f https://github.com/Bears-R-Us/arkouda-contrib.git
touch .git/info/sparse-checkout

# Repeat this echo for all packages you would like to checkout
echo "<pkg_name>" >> .git/info/sparse-checkout

git pull origin main
```

## Install a Package

`module_configuration.py` allows external Arkouda packages to be installed. If your package contains server elements, you will only be able to use a single package. Additional client-only modules could be installed. `module_configuration.py` will print the commands necessary to install a package. This output can be piped to `bash` to automatically execute the installation.

*Note - Support for installing multiple modules is being tracked by [Issue #8](https://github.com/Bears-R-Us/arkouda-contrib/issues/8).*


### Installation Parameters
- `--pkg_path` or `-p` - this is the full path to the module you want to configure. This should be pathed to the top level folder containing the `client`, `server` and `test` directories. **REQUIRED**
- `--ak_loc` or `-a` - this is the full path to the Arkouda installation on your machine. **REQUIRED when module contains a server element only**.
- `--config_loc` or `c` - path to save temporary .cfg file to when building arkouda. Defaults to the users home directory (~). **OPTIONAL**
- `--from_parent` - indicates that the `--pkg_path` being supplied is a parent directory whose child nodes are packages to install. Useful if packages share the same parent directory.
- `--from_file` - indicates that the `--pkg_path` being supplied is a .txt file containing a newline, `(\n)`, delimited list of paths to packages to install. Useful if packages do not have the same parent directory.


### Installation
```commandline
# Dry Run - only prints commands
python3 module_configuration.py --path <path to module> --ak <path to arkouda>

# Run the produced commands and install package
python3 module_configuration.py --path <path to module> --ak <path to arkouda> | bash
```