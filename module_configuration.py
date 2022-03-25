# This file is designed to provide a user with the commands required to configure their external module.
# NOTE - this file will not automatically execute any commands, the user must manually copy the commands and run them.
# TODO - add option to export commands to shell script
# TODO - detect if module has client & server or just client and configure accordingly

import os
import optparse


def add_client_path(mod_path):
    """
    Add path to the package to the PYTHONPATH environment variable.

    :param mod_path: absolute path to module
    """
    if os.getenv('PYTHONPATH') is None:
        # PYTHONPATH env var does not exist, add it and configure the module path
        print(f'\nRun the Following Command:\n\texport PYTHONPATH={mod_path}\n')
    elif os.getenv('PYTHONPATH') is not None and mod_path not in os.getenv('PYTHONPATH'):
        # PYTHONPATH exists, but the module path is not added
        print(f'\nRun the Following Command:\n\texport PYTHONPATH={mod_path}:$PYTHONPATH\n')
    else:
        print('Environment Pathed Correctly')


def configure_server_module():
    print("Not Implemented")


def run(mod_path):
    # TODO - validate mod_path exists
    # TODO - does the path contain server? Will always have client.

    if os.path.isdir(mod_path):
        add_client_path(mod_path)
        if os.path.isdir(mod_path+"/server"):
            configure_server_module(mod_path)
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
