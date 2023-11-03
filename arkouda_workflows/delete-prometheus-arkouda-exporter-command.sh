#!/bin/bash

argo submit -n $ARKOUDA_EXPORTER_NAMESPACE \
            delete-prometheus-arkouda-exporter-workflow.yaml \
            -p exporter-service-name=$ARKOUDA_EXPORTER_SERVICE_NAME \
            -p exporter-app-name=$ARKOUDA_EXPORTER_APP_NAME