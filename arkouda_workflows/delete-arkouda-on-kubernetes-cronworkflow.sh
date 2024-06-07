#!/bin/bash

argo cron create -n $ARKOUDA_NAMESPACE \
                 delete-arkouda-on-kubernetes-cronworkflow.yaml \
                 -p arkouda-instance-name=$ARKOUDA_INSTANCE_NAME \
                 -p kubernetes-api-url=$KUBERNETES_URL
