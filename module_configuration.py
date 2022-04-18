# This file is designed to provide a user with the commands required to configure their external module.
# NOTE - this file will not automatically execute any commands, the user must manually copy the commands and run them.
# TODO - add option to export commands to shell script

# Currently export of PYTHONPATH is only functional when run manually or source file.sh.

import os
import optparse
import glob
import time
import pkg_resources as pr
import subprocess

PIP_INSTALLS = []
USER_MODS = []
ADD_TO_CONFIG = []


def install_client_pkg(client_path):
    global PIP_INSTALLS
    """
    Install the python package if not already installed.
    :param client_path: absolute path to module
    """
    # get list of installed pkgs

    if not os.path.exists(client_path + "/setup.py"):
        raise RuntimeError("Configuration requires a setup.py file to install client. "
                           f"Please configure {client_path}/setup.py")
    p = subprocess.check_output(["python3", f"{client_path}/setup.py", "--name"], universal_newlines=True)
    PIP_INSTALLS.append(client_path)
    # Only provide install command if not already installed on system
    # installed_pkgs = {pkg.key for pkg in pr.working_set}
    # if pkg_name not in installed_pkgs:
    #     print(f"pip install {client_path}")

    # TODO - else update already installed package


def get_server_modules(cfg):
    mod_list = []
    with open(cfg) as f:
        for line in f.readlines():
            m = line.split("#")[0].split("/")[-1].strip()
            mod_list += [m] if m else []
    return mod_list


def get_chpl_files(mod_path):
    path = mod_path + "/server/*.chpl"
    return glob.glob(path)


def configure_server_module(mod_path, ak_loc):
    global ADD_TO_CONFIG, USER_MODS

    mod_cfg = mod_path + "/server/ServerModules.cfg"
    # ak_cfg = ak_loc + "/ServerModules.cfg"

    # get all of the modules listed in the .cfg file
    mods = get_server_modules(mod_cfg)
    ADD_TO_CONFIG += mods

    # Get chpl files that will be added to arkouda
    c_files = get_chpl_files(mod_path)
    USER_MODS += c_files

    # Generate commands - these can be piped into a shell for execution
    # 1 make copy of the Arkouda ServerModules.cfg
    # tmp_cfg = f"{mod_path}/TmpServerModules.cfg.{int(time.time())}"
    # print(f"cp {ak_cfg} {tmp_cfg}")

    # 2 append our modules
    # for c in mods:
    # print(f"echo {c} >> {tmp_cfg}")

    # 3 generate make command with vars
    # ak_srv_user_mods = '"' + " ".join(c_files) + '"' # setup our ARKOUDA_SERVER_USER_MODULES
    # print(f"ARKOUDA_SERVER_USER_MODULES={ak_srv_user_mods} ARKOUDA_CONFIG_FILE={tmp_cfg} "
    # f"ARKOUDA_SKIP_CHECK_DEPS=true make -C {ak_loc}")


def validate_pkgs(pkg_list, ak_loc):
    """
    Validate that all packages are configured as required and provide errors if not

    :param pkg_list: List of full paths to packages
    :param ak_loc: string path to arkouda
    :return: None
    """
    # Pip is required to install client pkgs, verify if is installed.
    installed_pkgs = {pkg.key for pkg in pr.working_set}
    if 'pip' not in installed_pkgs:
        raise RuntimeError("pip is required for the client installation. Please install pip.")

    ak_checked = False
    for pkg in pkg_list:
        # Verify that the pkg path exists
        if not os.path.exists(pkg):
            raise RuntimeError(f"Package Not Found. {pkg} does not exist.")
        client_path = pkg + "/client"
        server_path = pkg + "/server"
        # Verify the client package configuration
        if not os.path.exists(client_path):
            raise RuntimeError(f"Invalid package. Client package not found. {pkg}")
        if not os.path.exists(client_path + "/setup.py"):
            raise RuntimeError(f"Invalid Package Configuration. Missing setup.py. {pkg}")

        # Verify the server module configuration
        if os.path.exists(server_path):
            # If the arkouda location has not yet been checked, validate it exists.
            if not ak_checked:
                if ak_loc:
                    if not os.path.exists(ak_loc):
                        raise RuntimeError(f"Arkouda Location not provided or invalid. Set using --ak argument."
                                           f" Provided: {ak_loc}")
                    ak_cfg = ak_loc + "/ServerModules.cfg"
                    if not os.path.exists(ak_cfg):
                        raise RuntimeError(f"Could not locate arkouda ServerModules.cfg: {ak_cfg}")
                else:
                    raise RuntimeError(f"Arkouda Location not provided or invalid. Set using --ak argument."
                                       f" Provided: {ak_loc}")
                ak_checked = True

            # Verify that ServerModules.cfg exists for the module
            mod_cfg = server_path + "/ServerModules.cfg"
            if not os.path.exists(mod_cfg):
                raise RuntimeError(f"Could not locate module ServerModules.cfg: {mod_cfg}")


def create_commands(ak_loc, config_loc):
    # install clients
    print(f"pip install {' '.join(PIP_INSTALLS)}")

    # Create modified config file with user modules - .cfg saved to user home directory
    ak_cfg = ak_loc + "/ServerModules.cfg"
    tmp_cfg = f"{config_loc}/TmpServerModules.cfg.{int(time.time())}"
    print(f"cp {ak_cfg} {tmp_cfg}")

    for c in ADD_TO_CONFIG:
        print(f"echo {c} >> {tmp_cfg}")

    ak_srv_user_mods = '"' + " ".join(USER_MODS) + '"'  # setup our ARKOUDA_SERVER_USER_MODULES
    print(f"ARKOUDA_SERVER_USER_MODULES={ak_srv_user_mods} ARKOUDA_CONFIG_FILE={tmp_cfg} "
          f"ARKOUDA_SKIP_CHECK_DEPS=true make -C {ak_loc}")


def run(pkg_list, ak_loc, config_loc):
    # If only single pkg being installed, convert to list
    if isinstance(pkg_list, str):
        pkg_list = [pkg_list.rstrip("/")]

    # All packages reviewed at once. This prevents partial installs and alerts user to issues sooner.
    validate_pkgs(pkg_list, ak_loc)

    # Configure the components needed to build install commands
    for pkg in pkg_list:
        pkg = pkg.rstrip("/")  # remove trailing slash
        if ak_loc:
            ak_loc = ak_loc.rstrip("/")  # remove trailing slash

        client_path = pkg + "/client"
        server_path = pkg + "/server"

        install_client_pkg(client_path)
        if os.path.exists(server_path):
            configure_server_module(pkg, ak_loc)

    create_commands(ak_loc, config_loc)


def get_package_list_from_file(path):
    # Verify we have a text file
    if not path.endswith('.txt'):
        raise RuntimeError("Package List must be a newline(\n) delimited text file.")

    # read lines of the file and strip whitespace
    with open(path, 'r') as f:
        pkg_list = [line.rstrip().rstrip("/") for line in f]

    # Verify that we are not given an empty list
    if not pkg_list:
        raise RuntimeError("No packages found to be installed. "
                           "Please provide a file with a minimum of 1 package location.")

    return pkg_list


def get_package_list_from_directory(path):
    # Verify the provided parent directory exists
    if not os.path.exists(path):
        raise RuntimeError(f"Specified parent directory does not exist. {path} Not Found.")
    if not os.path.isdir(path):
        raise RuntimeError(f"Specified parent directory is not a directory. {path} is not a directory.")

    pkg_list = [path.rstrip("/") + "/" + x for x in os.listdir(path) if os.path.isdir(os.path.join(path, x)) and
                not x.startswith('.') and not x.startswith('__')]
    return pkg_list


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("--from_file", dest="pkg_list_file", action="store_true", default=False,
                      help="Indicates that your supplied pkg_path will be a file listing the packages to be installed.")
    parser.add_option("--from_parent", dest="parent_dir", action="store_true", default=False,
                      help="Indicates that your supplied pkg_path will be a directory containing all pkgs to be installed.")
    parser.add_option("-p", "--pkg_path", dest="pkg",
                      help="Full Path to external module you would like to configure, REQUIRED")
    parser.add_option("-a", "--ak_loc", dest="arkouda",
                      help="Full Path to Arkouda installation, required when a server module provided.")
    parser.add_option("-c", "--config_loc", dest="config_location", default="~",
                      help="Indicates the directory to save the temporary configuration files to. Defaults to ~/.")
    (options, args) = parser.parse_args()

    if not options.pkg:
        print("--pkg_path/-p is REQUIRED, but was empty.")
    elif options.pkg_list_file:
        pkg_list = get_package_list_from_file(options.pkg)
        run(pkg_list, options.arkouda, options.config_location)
    elif options.parent_dir:
        pkg_list = get_package_list_from_directory(options.pkg)
        run(pkg_list, options.arkouda, options.config_location)
    else:
        run(options.pkg, options.arkouda, options.config_location)
