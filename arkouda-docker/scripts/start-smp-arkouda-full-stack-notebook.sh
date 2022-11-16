#!/bin/bash

nohup /opt/arkouda/arkouda_server -nl ${NUMLOCALES:-1} > /dev/null &

jupyter notebook --ip=0.0.0.0 --allow-root --no-browser --NotebookApp.token=$JUPYTER_TOKEN