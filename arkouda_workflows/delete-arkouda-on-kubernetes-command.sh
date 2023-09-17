#!/bin/bash

argo submit -n $ARKOUDA_NAMESPACE \
            delete-arkouda-on-kubernetes-workflow.yaml \
            -p arkouda-ssl-secret=$ARKOUDA_SSL_SECRET \
            -p arkouda-instance-name=$ARKOUDA_INSTANCE_NAME \
            -p kubernetes-api-url=$KUBERNETES_URL \
            -p arkouda-user=$ARKOUDA_USER