#!/bin/bash

nohup /opt/arkouda/arkouda_server -nl ${NUMLOCALES:-1} > /dev/null &

ipython3