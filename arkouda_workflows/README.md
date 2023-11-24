# arkouda_workflows

## Background

[Argo Workflows](https://argoproj.github.io/argo-workflows/) is an ideal approach to manage all the dependencies involved in deploying Arkouda on Kubernetes (AoK) via [arkouda-udp-locale](https://github.com/Bears-R-Us/arkouda-contrib/tree/main/arkouda-helm-charts/arkouda-udp-locale) and [arkouda-udp-server](https://github.com/Bears-R-Us/arkouda-contrib/tree/main/arkouda-helm-charts/arkouda-udp-server) as well as the [prometheus-arkouda-exporter](https://github.com/Bears-R-Us/arkouda-contrib/tree/main/arkouda-helm-charts/prometheus-arkouda-exporter) deployment. Specifically, all arkouda-udp-locale pods must be up and running so that arkouda-udp-server can discover the locale pod ip addresses and launch the Arkouda cluster via the GASNET/UDP CHAPEL_COMM_SUBSTRATE.

## Workflows

There are four Arkouda argo workflows:

1. deploy-arkouda-on-kubernetes
2. delete-arkouda-on-kubernetes
3. deploy-prometheus-arkouda-exporter
4. delete-prometheus-arkouda-exporter

The first two workflows are for deploying/deleting AoK while the latter two are for deploying prometheus-arkouda-exporter that exports Arkouda metrics for non-AoK deployments such as Arkouda-on-Slurm.

In addition to Argo Workflows, there are two Arkouda [Argo Cron Workflows](https://argoproj.github.io/argo-workflows/cron-workflows/) that deploy and delete Arkouda at specific days and times via integration of Argo Workflows with [Unix/Linux crontab](https://www.techtarget.com/searchdatacenter/definition/crontab#:~:text=In%20Unix%20and%20Linux%2C%20cron,d%20scripts)

## Prerequisites

### Service Account and Role/Rolebinding

The [arkouda-workflows-service-account.yaml](arkouda-workflows-service-account.yaml) file encapsulates the following elements to enable the deploy-arkouda-on-kubernetes-workflow and deploy-arkouda-on-kubernetes-workflow to add/delete Kubernetes objects as needed to deploy and delete AoK:

1. arkouda-workflows-service-account: k8s ServiceAccount 
2. arkouda-workflows-role: Role encapsulating requisite permissions
3. arkouda-workflows-rolebinding: RoleBinding binding the arkouda-workflows-service-account to the arkouda-workflows-role

### Secrets

The following secrets are required to deploy AoK:

1. arkouda-ssh: encapsulates the SSH permissions required to launch AoK via the Chapel UDP substrate
2. arkouda-tls: encapsulates the arkouda user that is bound to the Arkouda Role that provides the arkouda-udp-server pod to create Kubernetes services as needed. 

Information regarding the Arkouda SSH and TLS secrets is [here](https://github.com/Bears-R-Us/arkouda-contrib/tree/main/arkouda-helm-charts/arkouda-udp-server#ssh-secret) and [here](https://github.com/Bears-R-Us/arkouda-contrib/tree/main/arkouda-helm-charts/arkouda-udp-server#tls-secret), respectively.

## Commands

### deploy arkouda workflow

The [deploy-arkouda-on-kubernetes-command.sh](deploy-arkouda-on-kubernetes-command.sh) script is used to deploy AoK utilizing several environment variables. An example is shown below:

```
export ARKOUDA_INSTANCE_NAME=arkouda-on-k8s
export ARKOUDA_NAMESPACE=arkouda
export ARKOUDA_VERSION=v2023.11.15
export ARKOUDA_SSH_SECRET=arkouda-ssh
export ARKOUDA_SSL_SECRET=arkouda-tls
export NUMBER_OF_LOCALES=2 # number of arkouda-locale instances 
export TOTAL_NUMBER_OF_LOCALES=3 # number of arkouda-locale instances + arkouda-server instance
export KUBERNETES_URL=https://localhost:6443 # result of kubectl cluster-info
export ARKOUDA_VERSION=v2023.11.15
export ARKOUDA_CPU_CORES=2000m
export ARKOUDA_MEMORY=2048Mi
export CHPL_MEM_MAX=1000000000
export CHPL_NUM_THREADS_PER_LOCALE=2
export ARKOUDA_USER=arkouda

sh deploy-arkouda-on-kubernetes-command.sh 
```

### delete arkouda workflow

The [delete-arkouda-on-kubernetes-command.sh](delete-arkouda-on-kubernetes-command.sh) script is used to delete AoK utilizing several environment variables. An example is shown below:

```
export ARKOUDA_USER=arkouda
export ARKOUDA_NAMESPACE=arkouda
export ARKOUDA_INSTANCE_NAME=arkouda-on-k8s
export ARKOUDA_SSL_SECRET=arkouda-tls
export KUBERNETES_URL=https://localhost:6443 # result of kubectl cluster-info

sh delete-arkouda-on-kubernetes-command.sh 
```

### deploy prometheus-arkouda-exporter workflow

The [deploy-prometheus-arkouda-exporter-command.sh](deploy-prometheus-arkouda-exporter-command.sh) script is used to deploy prometheus-arkouda-exporter, an example of which is shown below:

```
export ARKOUDA_EXPORTER_VERSION=v2023.11.15
export ARKOUDA_EXPORTER_SERVICE_NAME=arkouda-on-slurm-exporter
export ARKOUDA_EXPORTER_APP_NAME=arkouda-on-slurm-exporter
export ARKOUDA_EXPORTER_POLLING_INTERVAL=15
export ARKOUDA_EXPORTER_NAMESPACE=arkouda
export ARKOUDA_METRICS_SERVICE_HOST=arkouda-metrics.arkouda
export ARKOUDA_METRICS_SERVICE_PORT=5556
export ARKOUDA_SERVER_NAME=arkouda-on-slurm

sh deploy-prometheus-arkouda-exporter-command.sh
```

### delete prometheus-arkouda-exporter workflow

The [delete-prometheus-arkouda-exporter-command.sh](delete-prometheus-arkouda-exporter-command.sh) script is used to delete prometheus-arkouda-exporter, an example of which is shown below:

```
export ARKOUDA_EXPORTER_NAMESPACE=arkouda
export ARKOUDA_EXPORTER_SERVICE_NAME=arkouda-on-slurm-exporter
export ARKOUDA_EXPORTER_APP_NAME=arkouda-on-slurm-exporter

sh delete-prometheus-arkouda-exporter-command.sh
```

## CronWorkflows

The [deploy-arkouda-on-kubernetes-cronworkflow.sh](deploy-arkouda-on-kubernetes-cronworkflow.sh) script is used to deploy the deploy-arkouda-on-kubernetes CronWorkflow, which utilizes several environment variables to deploy AoK on a specific day and time. An example is shown below:

```
export ARKOUDA_INSTANCE_NAME=arkouda-on-k8s
export ARKOUDA_NAMESPACE=arkouda
export ARKOUDA_VERSION=v2023.11.15
export ARKOUDA_SSH_SECRET=arkouda-ssh
export ARKOUDA_SSL_SECRET=arkouda-tls
export NUMBER_OF_LOCALES=2 # number of arkouda-locale instances
export TOTAL_NUMBER_OF_LOCALES=3 # number of arkouda-locale instances + arkouda-server instance
export KUBERNETES_URL=https://localhost:6443 # result of kubectl cluster-info
export ARKOUDA_VERSION=v2023.11.15
export ARKOUDA_CPU_CORES=2000m
export ARKOUDA_MEMORY=2048Mi
export CHPL_MEM_MAX=1000000000
export CHPL_NUM_THREADS_PER_LOCALE=2
export ARKOUDA_USER=arkouda

sh deploy-arkouda-on-kubernetes-cronworkflow.sh
```

The default deploy-arkouda-on-kubernetes-cronworkflow configuration is to deploy arkouda-on-kubernetes daily at 0700 EST. The cron configuration can be changed in the spec.schedule section of the [deploy-arkouda-on-kubernetes-cronworkflow.yaml](deploy-arkouda-on-kubernetes-cronworkflow.yaml) file as shown below:

```
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  name: deploy-arkouda-on-kubernetes
spec:
  schedule: "* 07 * * *"
```

### delete arkouda cron workflow

The [delete-arkouda-on-kubernetes-cronworkflow.sh](delete-arkouda-on-kubernetes-cronworkflow.sh) script is used deploy the delete-arkouda-on-kubernetes CronWorkflow, which utilizes several environment variables to delete AoK on a specific day and time. An example is shown below:

```
export ARKOUDA_USER=arkouda
export ARKOUDA_NAMESPACE=arkouda
export ARKOUDA_INSTANCE_NAME=arkouda-on-k8s
export ARKOUDA_SSL_SECRET=arkouda-tls
export KUBERNETES_URL=https://localhost:6443 # result of kubectl cluster-info

sh delete-arkouda-on-kubernetes-cronworkflow.sh
```

The default delete-arkouda-on-kubernetes-cronworkflow configuration is to delete arkouda-on-kubernetes daily at 1700 EST. The cron configuration can be changed in the spec.schedule section of the [delete-arkouda-on-kubernetes-cronworkflow.yaml](delete-arkouda-on-kubernetes-cronworkflow.yaml) file as shown below:

```
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  name: delete-arkouda-on-kubernetes
spec:
  schedule: "* 17 * * *"
```
