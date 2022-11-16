#!/bin/bash

/opt/arkouda/arkouda_server -nl ${NUMLOCALES:-1} --memTrack=${MEMTRACK:-true} --authenticate=${AUTHENTICATE:-false} \
                 --logLevel=${LOG_LEVEL:-LogLevel.INFO}