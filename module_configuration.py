# This file is designed to provide a user with the commands required to configure their external module.
# NOTE - this file will not automatically execute any commands, the user must manually copy the commands and run them.
# TODO - add option to export commands to shell script

# Currently export of PYTHONPATH is only functional when run manually or source file.sh.

import os
import optparse
import pkg_resources as pr
import subprocess
import glob
import time


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
    if not ak_loc:
        raise RuntimeError("--ak option is required when configuring a module with server components.")
    mod_cfg = mod_path + "/server/ServerModules.cfg"
    ak_cfg = ak_loc + "/ServerModules.cfg"
    if not os.path.exists(mod_cfg):
        raise RuntimeError(f"Could not locate module ServerModules.cfg: {mod_cfg}")
    if not os.path.exists(ak_cfg):
        raise RuntimeError(f"Could not locate module ServerModules.cfg: {ak_cfg}")

    # get all of the modules listed in the .cfg file
    mods = get_server_modules(mod_cfg)

    # Get chpl files that will be added to arkouda
    c_files = get_chpl_files(mod_path)

    # Generate commands - these can be piped into a shell for execution
    # 1 make copy of the Arkouda ServerModules.cfg
    tmp_cfg = f"{mod_path}/TmpServerModules.cfg.{int(time.time())}"
    print(f"cp {ak_cfg} {tmp_cfg}")

    #2 append our modules
    for c in mods:
        print(f"echo {c} >> {tmp_cfg}")

    #3 generate make command with vars
    ak_srv_user_mods = '"' + " ".join(c_files) + '"' # setup our ARKOUDA_SERVER_USER_MODULES
    print(f"ARKOUDA_SERVER_USER_MODULES={ak_srv_user_mods} ARKOUDA_CONFIG_FILE={tmp_cfg} "
          f"ARKOUDA_SKIP_CHECK_DEPS=true make -C {ak_loc}")

def run(mod_path, ak_loc):
    mod_path = mod_path.rstrip("/")  # remove trailing slash
    ak_loc = ak_loc.rstrip("/")  # remove trailing slash

    client_path = mod_path + "/client"
    server_path = mod_path + "/server"

    if os.path.exists(mod_path):
        add_client_path(client_path)
        if os.path.exists(server_path) and os.path.exists(ak_loc):
            if os.path.exists(ak_loc):
                configure_server_module(mod_path, ak_loc)
            else:
                raise RuntimeError("Arkouda Location must be provided when module contains a server element.")
    else:
        raise RuntimeError(f"Module path not valid: {mod_path}")

if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("--path", dest="module", help="Full Path to external module you would like to configure, REQUIRED")
    parser.add_option("--ak", dest="arkouda", help="Full Path to Arkouda installation, required when a server module provided.")
    (options, args) = parser.parse_args()

    if not options.module:
        print("--path is REQUIRED, but was empty.")
    else:
        run(options.module, options.arkouda)
