# This file is designed to provide a user with the commands required to configure their external module.
# NOTE - this file will not automatically execute any commands, the user must manually copy the commands and run them.
# TODO - add option to export commands to shell script
# TODO - detect if module has client & server or just client and configure accordingly

import os
import optparse
import pkg_resources as pr
import subprocess


def install_client_pkg(client_path):
    """
    Install the python package if not already installed.
    :param client_path: absolute path to module
    """
    # get list of installed pkgs
    installed_pkgs = {pkg.key for pkg in pr.working_set}
    if 'pip' not in installed_pkgs:
        raise RuntimeError("pip is required for the client installation and is not installed.")
    if not os.path.exists(client_path+"/setup.py"):
        raise RuntimeError(f"Configuration requires a setup.py file to install client. Please configure {client_path}/setup.py")
    p = subprocess.Popen(["python3", f"{client_path}/setup.py", "--name"])
    pkg_name, error = p.communicate()

    # Only provide install command if not already installed on system
    if pkg_name not in installed_pkgs:
        print(f"pip install {client_path}")


def configure_server_module():
    print("Not Implemented")


def run(mod_path):
    client_path = mod_path+"/client"
    server_path = mod_path+"/server"
    if os.path.exists(client_path):
        install_client_pkg(client_path)
        if os.path.isdir(mod_path+"/server"):
            configure_server_module()
    else:
        print(f"Please provide a valid path to your module. {mod_path} does not exist. "
              "Please be sure you are providing the full path.")


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("--path", dest="module", help="Path to external module you would like to configure, REQUIRED")
    (options, args) = parser.parse_args()

    if not options.module:
        print("--path is REQUIRED, but was empty.")
    else:
        run(options.module)
