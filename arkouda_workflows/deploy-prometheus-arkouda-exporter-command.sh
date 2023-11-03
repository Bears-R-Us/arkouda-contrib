#!/bin/bash

argo submit -n $ARKOUDA_EXPORTER_NAMESPACE \
            deploy-prometheus-arkouda-exporter-workflow.yaml \
            -p exporter-release-version=$ARKOUDA_EXPORTER_VERSION \
            -p exporter-service-name=$ARKOUDA_EXPORTER_SERVICE_NAME \
            -p exporter-app-name=$ARKOUDA_EXPORTER_APP_NAME \
            -p arkouda-metrics-service-host=$ARKOUDA_METRICS_SERVICE_HOST \
            -p arkouda-metrics-service-port=$ARKOUDA_METRICS_SERVICE_PORT \
            -p arkouda-server-name=$ARKOUDA_SERVER_NAME \
            -p exporter-polling-interval=15