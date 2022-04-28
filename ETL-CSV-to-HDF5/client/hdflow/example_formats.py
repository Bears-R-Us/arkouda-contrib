###################
# Example format specifications

import numpy as np
from copy import deepcopy
from functools import partial
from .converters import Converter, split_IP


# This is the dict that will be exported to the conversion script
# so that users can select the format from the command line.
OPTIONS = {}

# Field types and NA values
# Small Values: values [1, 10], so use int8 with -1==NA
# Positive Int: unbounded positive integer, so use int64 with -1==NA
# Start/end times: let pandas parse these
# Flag: 10-bit field, so use uint16 with high-bit indicating NA
# Flag2: 8-bit field with all bits used, but 0b110 is an invalid value, so use uint8 with 0b101==NA
# Nonzero int: unbounded nonzero integer, so use int64 with 0==NA
# srcIP: IPv4 or IPv6 address
# dstIP: IPv4 or IPv6 address

schema = {'small_vals':(np.int8, -1),
          'pos_ints':(np.int64, -1),
          'flag':(np.uint16, 0x8000),
          'flag2':(np.uint8, 0b110), 
          'nonzero':(np.int64, 0)
}
converters = {field: Converter(*params) for field, params in schema.items()}
IPtransform = partial(split_IP, IPcolumns=['srcIP', 'dstIP'])

example_options = {'delimiter':'\t', 
                'compression':'gzip',
                'header':None,
                'parse_dates':['starttime', 'endtime'],
                   'infer_datetime_format':True,
                   'transforms': [IPtransform]}

example_options['converters'] = converters
OPTIONS['example'] = example_options

