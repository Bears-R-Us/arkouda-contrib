#!/bin/bash

argo submit -n $ARKOUDA_NAMESPACE \
            delete-arkouda-on-kubernetes-workflow.yaml \
            -p arkouda-instance-name=$ARKOUDA_INSTANCE_NAME \
            -p kubernetes-api-url=$KUBERNETES_URL \
