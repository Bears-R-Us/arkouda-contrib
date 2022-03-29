# arkouda-contrib
a place for contributed functionality for arkouda

## Environment Configuration

```commandline
python3 module_configuration <path to your module>
```

This command will output an export command. If your environment is already configured to import this module, this will be indicated by the output and no command will be returned.

## Module Usage

```python
import arkouda as ak
import yourModuleName

ak.connect()
```
