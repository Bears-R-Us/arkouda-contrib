#!/bin/bash

argo submit -n arkouda delete-arkouda-on-kubernetes-workflow.yaml -p arkouda-ssl-secret=arkouda-tls \
            -p arkouda-instance-name=arkouda-on-k8s -p kubernetes-api-url=https://192.168.1.11:6443 \
            -p arkouda-user=arkouda 