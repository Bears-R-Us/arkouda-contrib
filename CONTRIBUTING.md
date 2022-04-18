#Contributing to arkouda-contrib

arkouda-contrib welcomes contributions via feedback, bug reports, and pull requests.

We use a simple [Git Feature Branch Workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/feature-branch-workflow).

##Development
All packages are required to contain `client` and `test` directories. The `server` directory is utilized when your package requires additional processing code on the Arkouda server.

### Package Structure

- Package Name
    - client **(REQUIRED)**
      - client_package_name
        - `__init__.py`
        - `package.py` files
      - README.md
      - setup.py
    - server **(OPTIONAL)**
      - `package.chpl`files
      - `ServerModules.cfg`
    - test **(REQUIRED)**
      - `name_test.py` files
    - pytest.ini

The top level of your package should be added under the `arkouda-contrib` directory. This is the top level of the repository.

##Testing

In the `test` directory of your package, you will need to define testing for the newly defined functionality. At the same level as your `test` directory, be sure to define `pytest.ini`. Example definition below:

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

##PR Submissions
arkouda-contrib asks that when submitting a PR, you link the issue you are closing to the PR.