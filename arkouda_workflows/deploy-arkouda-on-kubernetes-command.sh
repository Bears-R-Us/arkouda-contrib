#!/bin/bash

argo submit -n arkouda deploy-arkouda-on-kubernetes-workflow.yaml -p arkouda-release-version=$ARKOUDA_VERSION \
            -p arkouda-ssl-secret=arkouda-tls -p arkouda-ssh-secret=arkouda-ssh \
            -p arkouda-number-of-locales=$NUMBER_OF_LOCALES -p arkouda-instance-name=arkouda-on-k8s \
            -p arkouda-total-number-of-locales=$TOTAL_NUMBER_OF_LOCALES \
            -p kubernetes-api-url=$KUBERNETES_URL -p arkouda-namespace=arkouda \
            -p arkouda-server-name=arkouda-on-k8s -p arkouda-metrics-service-name=project-a-metrics \
            -p arkouda-log-level=LogLevel.DEBUG -p arkouda-user=arkouda  \
            -p metrics-polling-interval-seconds=15 -p image-pull-policy=IfNotPresent 
