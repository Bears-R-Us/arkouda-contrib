#!/bin/bash

argo submit -n $ARKOUDA_NAMESPACE \
            deploy-arkouda-on-kubernetes-workflow.yaml \
            -p arkouda-release-version=$ARKOUDA_VERSION \
            -p arkouda-ssl-secret=$ARKOUDA_SSL_SECRET \
            -p arkouda-ssh-secret=$ARKOUDA_SSH_SECRET \
            -p arkouda-number-of-locales=$NUMBER_OF_LOCALES \
            -p arkouda-instance-name=$ARKOUDA_INSTANCE_NAME \
            -p arkouda-total-number-of-locales=$TOTAL_NUMBER_OF_LOCALES \
            -p kubernetes-api-url=$KUBERNETES_URL \
            -p arkouda-namespace=$ARKOUDA_NAMESPACE \
            -p arkouda-log-level=LogLevel.DEBUG \
            -p arkouda-user=$ARKOUDA_USER  \
            -p metrics-polling-interval-seconds=$ARKOUDA_METRICS_POLLING_INTERVAL \
	    -p prometheus-match-label="$ARKOUDA_PROMETHEUS_MATCH_LABEL" \
	    -p launcher=$ARKOUDA_LAUNCHER \
            -p image-pull-policy=IfNotPresent \
            -p num-cpu-cores=$ARKOUDA_CPU_CORES \
            -p memory=$ARKOUDA_MEMORY \
            -p chpl-num-threads-per-locale=$CHPL_NUM_THREADS_PER_LOCALE \
            -p chpl-mem-max=$CHPL_MEM_MAX
