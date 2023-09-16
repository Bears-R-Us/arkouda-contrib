#!/bin/bash

argo submit -n arkouda deploy-arkouda-on-kubernetes-workflow.yaml -p arkouda-release-version=v2023.09.06 \
            -p arkouda-ssl-secret=arkouda-tls -p arkouda-ssh-secret=arkouda-ssh -p arkouda-number-of-locales=2 \
            -p arkouda-instance-name=arkouda-on-k8s -p arkouda-total-number-of-locales=3 \
            -p kubernetes-api-url=https://192.168.1.11:6443 -p arkouda-namespace=arkouda -p arkouda-server-name=arkouda-on-k8s \
            -p arkouda-service-port=5555 -p arkouda-metrics-service-name=project-a-metrics -p arkouda-metrics-service-port=5556 \
            -p arkouda-log-level=LogLevel.DEBUG -p arkouda-user=arkouda -p metrics-exporter-service-port=5080 \
            -p metrics-polling-interval-seconds=15 -p image-pull-policy=IfNotPresent 
