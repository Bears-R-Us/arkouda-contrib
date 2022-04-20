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

Currently, `module_configuration.py` only supports installing a single package. If your package contains server elements, you will only be able to use a single package. Additional client-only modules could be installed. `module_configuration.py` will print the commands necessary to install a package. This output can be piped to `bash` to automatically execute the installation.

<em>Note - Support for installing multiple modules is being tracked by [Issue #8](https://github.com/Bears-R-Us/arkouda-contrib/issues/8).</em>

### Installation Parameters
- `path` - this is the full path to the module you want to configure. This should be pathed to the top level folder containing the `client`, `server` and `test` directories.*REQUIRED*
- `ak` - this is the full path to the Arkouda installation on your machine. *REQUIRED when module contains a server element only*.

### Installation
```commandline
# Dry Run - only prints commands
python3 module_configuration.py --path <path to module> --ak <path to arkouda>

# Run the produced commands and install package
python3 module_configuration.py --path <path to module> --ak <path to arkouda> | bash
```