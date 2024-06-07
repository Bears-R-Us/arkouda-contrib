#!/bin/bash

argo submit -n $ARKOUDA_NAMESPACE \
            deploy-arkouda-on-kubernetes-workflow.yaml \
            -p arkouda-release-version=$ARKOUDA_VERSION \
            -p arkouda-ssh-secret=$ARKOUDA_SSH_SECRET \
            -p arkouda-number-of-locales=$ARKOUDA_NUMBER_OF_LOCALES \
            -p arkouda-instance-name=$ARKOUDA_INSTANCE_NAME \
            -p arkouda-total-number-of-locales=$ARKOUDA_TOTAL_NUMBER_OF_LOCALES \
            -p kubernetes-api-url=$KUBERNETES_URL \
            -p arkouda-namespace=$ARKOUDA_NAMESPACE \
            -p arkouda-log-level=LogLevel.DEBUG \
            -p metrics-polling-interval-seconds=$ARKOUDA_METRICS_POLLING_INTERVAL \
	    -p prometheus-match-label="$ARKOUDA_PROMETHEUS_MATCH_LABEL" \
	    -p launcher=$ARKOUDA_LAUNCHER \
            -p image-pull-policy=$ARKOUDA_IMAGE_PULL_POLICY \
            -p num-cpu-cores=$ARKOUDA_CPU_CORES \
            -p memory=$ARKOUDA_MEMORY \
            -p chpl-num-threads-per-locale=$CHPL_NUM_THREADS_PER_LOCALE \
            -p chpl-mem-max=$CHPL_MEM_MAX \
	    -p arkouda-serviceaccount-name=$ARKOUDA_SERVICEACCOUNT_NAME \
	    -p arkouda-serviceaccount-token-name=$ARKOUDA_SERVICEACCOUNT_TOKEN_NAME \
	    -p arkouda-user=$ARKOUDA_USER \
	    -p arkouda-uid="$ARKOUDA_UID" \
	    -p arkouda-group=$ARKOUDA_GROUP \
	    -p arkouda-gid="$ARKOUDA_GID"
