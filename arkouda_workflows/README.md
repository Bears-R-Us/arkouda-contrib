# arkouda_workflows

## Background

[Argo Workflows](https://argoproj.github.io/argo-workflows/) is an ideal approach to manage all the dependencies involved in deploying Arkouda on Kubernetes (AoK) via [arkouda-udp-locale](https://github.com/Bears-R-Us/arkouda-contrib/tree/main/arkouda-helm-charts/arkouda-udp-locale) and [arkouda-udp-server](https://github.com/Bears-R-Us/arkouda-contrib/tree/main/arkouda-helm-charts/arkouda-udp-server) deployments. Specifically, all arkouda-udp-locale pods _must be up and running_ so that the arkouda-udp-server pod can discover the locale pod ip addresses and launch the Arkouda cluster via the GASNET/UDP CHAPEL\_COMM\_SUBSTRATE.

In addition, Argo Workflows is a convenient means for deploying [prometheus-arkouda-exporter](https://github.com/Bears-R-Us/arkouda-contrib/tree/main/arkouda-helm-charts/prometheus-arkouda-exporter) deployment.

Argo Workflows also provides a more straightforward means of programatically launching AoK as well as prometheus-arkouda-exporter via the [Hera](https://hera-workflows.readthedocs.io/en/stable/) Argo Workflows-Argo Events python client.

## Workflows

There are four Arkouda Argo workflows:

1. deploy-arkouda-on-kubernetes
2. delete-arkouda-on-kubernetes
3. deploy-prometheus-arkouda-exporter
4. delete-prometheus-arkouda-exporter

The first two workflows are for deploying/deleting AoK while the latter two are for deploying prometheus-arkouda-exporter that exports Arkouda metrics for non-AoK deployments such as Arkouda-on-Slurm. Note: for AoK, prometheus-arkouda-exporter is bundled with the arkouda-udp-server pod.

## CronWorkflows

In addition to Argo Workflows, there are two Arkouda [Argo CronWorkflows](https://argoproj.github.io/argo-workflows/cron-workflows/) that deploy and delete Arkouda, respectively, at specific days and times via integration of Argo Workflows with [Unix/Linux crontab](https://www.techtarget.com/searchdatacenter/definition/crontab#:~:text=In%20Unix%20and%20Linux%2C%20cron,d%20scripts)

## WorkflowTemplates

Both the Arkouda Workflows and CronWorkflows are based upon the Arkouda [deploy](https://github.com/Bears-R-Us/arkouda-contrib/blob/main/arkouda_workflows/deploy-arkouda-on-kubernetes-workflow-template.yaml) and [delete](https://github.com/Bears-R-Us/arkouda-contrib/blob/main/arkouda_workflows/delete-arkouda-on-kubernetes-workflow-template.yaml) WorkflowTemplates, respectively. Similarly, the prometheus-arkouda-exporter workflows are based upon the corresponding [deploy](https://github.com/Bears-R-Us/arkouda-contrib/blob/main/arkouda_workflows/deploy-prometheus-arkouda-exporter-workflow-template.yaml) and [delete](https://github.com/Bears-R-Us/arkouda-contrib/blob/main/arkouda_workflows/delete-prometheus-arkouda-exporter-workflow-template.yaml) WorkflowTemplates.

## Prerequisites

### Overview

There are two sets of [ServiceAccounts](https://kubernetes.io/docs/concepts/security/service-accounts/) and [Roles](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#role-and-clusterrole)/[RoleBindings](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#rolebinding-and-clusterrolebinding) used for deploying Arkouda and prometheus-arkouda-exporter on Kubernetes:

1. Arkouda Argo Workflows: ServiceAccount and Role/RoleBinding for deploying the Arkouda Argo Workflows
2. Arkouda: ServiceAccount bound to Kubernetes roles required by the arkouda-udp-server pod to (1) discover all arkouda-udp-locale pods and (2) register an Arkouda Kubernetes service enabling service discovery. The Arkouda ServiceAccount is bound to the Arkouda [Pod](https://github.com/Bears-R-Us/arkouda-contrib/blob/e2e9640c677d62ffae8d0b37fea4e9cd41636342/arkouda_workflows/deploy-arkouda-on-kubernetes-workflow-template.yaml#L286) [Service](https://github.com/Bears-R-Us/arkouda-contrib/blob/e2e9640c677d62ffae8d0b37fea4e9cd41636342/arkouda_workflows/deploy-arkouda-on-kubernetes-workflow-template.yaml#L315), and [ServiceMonitor](https://github.com/Bears-R-Us/arkouda-contrib/blob/e2e9640c677d62ffae8d0b37fea4e9cd41636342/arkouda_workflows/deploy-arkouda-on-kubernetes-workflow-template.yaml#L345) roles and correesponding RoleBindings upon deployment. 

### Arkouda Argo Workflows ServiceAccount and Role/RoleBinding

The [arkouda-workflows-service-account.yaml](arkouda-workflows-service-account.yaml) file encapsulates the following elements to enable the deploy-arkouda-on-kubernetes-workflow and deploy-arkouda-on-kubernetes-workflow to add/delete Kubernetes objects as needed to deploy and delete AoK as well as prometheus-arkouda-exporter:

1. arkouda-workflows-service-account: k8s ServiceAccount 
2. arkouda-workflows-role: Role encapsulating requisite permissions
3. arkouda-workflows-rolebinding: RoleBinding that binds the arkouda-workflows-service-account to the arkouda-workflows-role

### Arkouda ServiceAccount

A ServiceAccount along with a corresponding bearer token Secret are prerequisites. An example ServiceAccount and bearer token create sequence is shown below:

An example ServiceAccount definition is as follows:

```
apiVersion: v1
kind: ServiceAccount
metadata:
  name: arkouda
automountServiceAccountToken: false
``` 

Create the ServiceAccount as follows:

```
export NAMESPACE=arkouda

kubectl apply -n arkouda -f arkouda-sa.yaml
```

Since the Arkouda ServiceAccount is bound to the Pod, Service, and ServiceMonitor roles at workflow deployment time as detailed above, _only the Arkouda ServiceAccount is a prerequisite._

### Secrets

The following secrets are required to deploy AoK:

1. arkouda-ssh: encapsulates the SSH permissions required to launch Arkouda locales deployed in Kubernetes pods via the Chapel UDP substrate
2. arkouda-token: encapsulates the bearer token used by the Arkouda ServiceAccount to authenticate to the Kubernetes API. Again, as detailed above, AoK accesses the Kubernetes API to (1) discover arkouda-udp-locale pods and (2) create/delete the Arkouda service used for Arkouda service discovery.

Information regarding the Arkouda SSH and bearer token secrets is [here](https://github.com/Bears-R-Us/arkouda-contrib/tree/main/arkouda-helm-charts/arkouda-udp-server#ssh-secret) and [here](https://github.com/Bears-R-Us/arkouda-contrib/tree/main/arkouda-helm-charts/arkouda-udp-server#serviceaccount), respectively.

### Prometheus

#### Prometheus Install

For metrics-enabled AoK as well as arkouda-prometheus-exporter, a Prometheus Server and [Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator) are required. The prometheus-community has an excellent [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack) Helm chart that's a convenient way to install 1..n elements of a Prometheus stack including Prometheus Server and Prometheus Operator.  

#### Prometheus Scrap Target Configuration

The prometheus-arkouda-exporter, which is deployed standalone or part of AoK, is rendered discoverable as a scrape target by the Prometheus ServiceMonitor, which is a custom resource definition (CRD) deployed by the Prometheus Operator. The target Prometheus instance has 1..n labels it uses to discover ServiceMonitors and their corresponding scrape targets in the namespace(s) Prometheus is configured to monitor.

##### Configuring serviceMonitorNamespaceSelector

The default Prometheus configuration is to monitor all namespaces as shown below:

```
spec:
  serviceMonitorNamespaceSelector: {}
``` 

The default can be overridden by specifying an array of 1..n namespaces:

```
spec: 
  serviceMonitorNamespaceSelector:
    matchExpressions:
      - key: kubernetes.io/metadata.name
        operator: In
        values: [ prometheus, default, arkouda ]
```

##### Configuring serviceMonitorSelector

The serviceMonitorSelector element of the Prometheus configuration specifies the label(s) Prometheus uses to discover ServiceMonitors. In the example below, Prometheus discovers and registers any ServiceMonitor with the ```release: kube-stack``` label: 

```
spec:
  serviceMonitorSelector:
    matchLabels:
      release: kube-stack
```

### prometheus-arkouda-exporter ServiceMonitor

The prometheus-arkouda-exporter is rendered discoverable via label matching one of the labels specified in the target Prometheus spec.serviceMonitorSelector.matchLabels elements. In the above example the ```release: kubestack```  label is defined. Accordingly, prometheus-arkouda-exporter would be discoverable via the following prometheus-arkouda-exporter ServiceMonitor configuration:

```
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  labels:
    release: kube-stack
  name: arkouda-on-k8s-servicemonitor
spec:
  endpoints:
  - interval: 15s
    path: /metrics
    port: http
  selector:
    matchLabels:
      instance: arkouda-on-k8s-metrics-exporter
``` 

## Commands

### deploy arkouda workflow

The [deploy-arkouda-on-kubernetes-command.sh](deploy-arkouda-on-kubernetes-command.sh) script is used to deploy AoK utilizing several environment variables. In the base configuration Arkouda runs as the default AoK user,  an example of which is shown below:

```
export KUBERNETES_URL=https://localhost:6443
export ARKOUDA_MEMORY=2048Mi
export ARKOUDA_CPU_CORES=2000m
export CHPL_NUM_THREADS_PER_LOCALE=2
export CHPL_MEM_MAX=1000000000
export ARKOUDA_SERVICEACCOUNT_NAME=arkouda-on-k8s 
export ARKOUDA_SERVICEACCOUNT_TOKEN_NAME=arkouda-on-k8s 
export ARKOUDA_SSH_SECRET=arkouda-ssh
export ARKOUDA_NAMESPACE=arkouda
export ARKOUDA_NUMBER_OF_LOCALES=2
export ARKOUDA_TOTAL_NUMBER_OF_LOCALES=3
export ARKOUDA_METRICS_SERVICE_PORT=5556
export ARKOUDA_VERSION=v2024.04.19
export ARKOUDA_IMAGE_POLICY=IfNotPresent
export ARKOUDA_INSTANCE_NAME=arkouda-on-k8s
export ARKOUDA_SERVER_NAME=arkouda-on-k8s
export ARKOUDA_LAUNCHER=kubernetes
export ARKOUDA_METRICS_POLLING_INTERVAL=15
export ARKOUDA_METRICS_SERVICE_HOST=arkouda-on-k8s-metrics
export ARKOUDA_EXPORTER_APP_NAME=arkouda-on-k8s-exporter
export ARKOUDA_EXPORTER_SERVICE_NAME=arkouda-on-k8s-exporter
export ARKOUDA_PROMETHEUS_MATCH_LABEL="release: kube-stack"

sh deploy-arkouda-on-kubernetes-command.sh 
```

Configuration parameters of note:

1. KUBERNETES\_API: URL for Kubernetes API, which is used to create/read pods, create services as well as servicemonitor
2. ARKOUDA\_SERVICEACCOUNT\_NAME: name of Kubernetes ServiceAccount used by Arkouda to register with Kubernetes and Prometheus
3. ARKOUDA\_SSH\_SECRET secret encapsulating SSH permissions required for deploying Arkouda via UDP
4. ARKOUDA\_PROMETHEUS\_MATCH\_LABEL: the label Prometheus matches and uses to discover prometheus-arkouda-exporter scrape endpoints. 

To run Arkouda as a specific  user and corresponding group, the primary purpose of which is to enable output of Arkouda files to locations with specific user and group permissions, the following env variables and Argo workflow parameters are added:

```
export ARKOUDA_USER=bearsrus
export ARKOUDA_UID=1009
export ARKOUDA_GROUP=bearsrus-arkouda-users
export ARKOUDA_GID=1019
```

### delete arkouda workflow

The [delete-arkouda-on-kubernetes-command.sh](delete-arkouda-on-kubernetes-command.sh) script is used to delete AoK utilizing several environment variables. An example is shown below:

```
export ARKOUDA_NAMESPACE=arkouda
export ARKOUDA_INSTANCE_NAME=arkouda-on-k8s
export KUBERNETES_URL=https://localhost:6443 # result of kubectl cluster-info

sh delete-arkouda-on-kubernetes-command.sh 
```

### deploy-prometheus-arkouda-exporter workflow

The [deploy-prometheus-arkouda-exporter-command.sh](deploy-prometheus-arkouda-exporter-command.sh) script is used to deploy prometheus-arkouda-exporter, an example of which is shown below:

```
export ARKOUDA_VERSION=v2024.04.19
export ARKOUDA_NAMESPACE=arkouda
export ARKOUDA_EXPORTER_SERVICE_NAME=arkouda-on-slurm-exporter
export ARKOUDA_EXPORTER_APP_NAME=arkouda-on-slurm-exporter
export ARKOUDA_EXPORTER_POLLING_INTERVAL=15
export ARKOUDA_METRICS_SERVICE_HOST=arkouda-metrics.arkouda
export ARKOUDA_METRICS_SERVICE_PORT=5556
export ARKOUDA_SERVER_NAME=arkouda-on-slurm
export ARKOUDA_PROMETHEUS_MATCH_LABEL="release: kube-stack"
export ARKOUDA_LAUNCHER=slurm

sh deploy-prometheus-arkouda-exporter-command.sh
```

### delete-prometheus-arkouda-exporter workflow

The [delete-prometheus-arkouda-exporter-command.sh](delete-prometheus-arkouda-exporter-command.sh) script is used to delete prometheus-arkouda-exporter, an example of which is shown below:

```
export ARKOUDA_EXPORTER_NAMESPACE=arkouda
export ARKOUDA_EXPORTER_SERVICE_NAME=arkouda-on-slurm-exporter
export ARKOUDA_EXPORTER_APP_NAME=arkouda-on-slurm-exporter

sh delete-prometheus-arkouda-exporter-command.sh
```

## CronWorkflows

### deploy-arkouda-on-kubernetes-cronworkflow

The [deploy-arkouda-on-kubernetes-cronworkflow.sh](deploy-arkouda-on-kubernetes-cronworkflow.sh) script is used to deploy the deploy-arkouda-on-kubernetes CronWorkflow, which utilizes several environment variables to deploy AoK on a specific day and time. An example is shown below:

```
export KUBERNETES_URL=https://localhost:6443
export ARKOUDA_MEMORY=2048Mi
export ARKOUDA_CPU_CORES=2000m
export CHPL_NUM_THREADS_PER_LOCALE=2
export CHPL_MEM_MAX=1000000000
export ARKOUDA_SERVICEACCOUNT_NAME=arkouda-on-k8s
export ARKOUDA_SERVICEACCOUNT_TOKEN_NAME=arkouda-on-k8s
export ARKOUDA_SSH_SECRET=arkouda-ssh
export ARKOUDA_NAMESPACE=arkouda
export ARKOUDA_NUMBER_OF_LOCALES=2
export ARKOUDA_TOTAL_NUMBER_OF_LOCALES=3
export ARKOUDA_METRICS_SERVICE_PORT=5556
export ARKOUDA_VERSION=v2024.04.19
export ARKOUDA_IMAGE_POLICY=IfNotPresent
export ARKOUDA_INSTANCE_NAME=arkouda-on-k8s
export ARKOUDA_SERVER_NAME=arkouda-on-k8s
export ARKOUDA_LAUNCHER=kubernetes
export ARKOUDA_METRICS_POLLING_INTERVAL=15
export ARKOUDA_METRICS_SERVICE_HOST=arkouda-on-k8s-metrics
export ARKOUDA_EXPORTER_APP_NAME=arkouda-on-k8s-exporter
export ARKOUDA_EXPORTER_SERVICE_NAME=arkouda-on-k8s-exporter
export ARKOUDA_PROMETHEUS_MATCH_LABEL="release: kube-stack"

sh deploy-arkouda-on-kubernetes-cronworkflow.sh
```

The default deploy-arkouda-on-kubernetes-cronworkflow configuration is to deploy arkouda-on-kubernetes daily at 0700 EST. The cron configuration can be changed in the [spec.schedule](https://github.com/hokiegeek2/arkouda-contrib/blob/62c099130d78ed523951aac11893298f3b9c752f/arkouda_workflows/deploy-arkouda-on-kubernetes-cronworkflow.yaml#L5) section of the deploy-arkouda-on-kubernetes-cronworkflow.yaml file as shown below:

```
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  name: deploy-arkouda-on-kubernetes
spec:
  schedule: "* 07 * * *"
```

### delete-arkouda-on-kubernetes-cronworkflow

The [delete-arkouda-on-kubernetes-cronworkflow.sh](delete-arkouda-on-kubernetes-cronworkflow.sh) script is used deploy the delete-arkouda-on-kubernetes CronWorkflow, which utilizes several environment variables to delete AoK on a specific day and time. An example is shown below:

```
export ARKOUDA_NAMESPACE=arkouda
export ARKOUDA_INSTANCE_NAME=arkouda-on-k8s
export KUBERNETES_URL=https://localhost:6443 # result of kubectl cluster-info

sh delete-arkouda-on-kubernetes-cronworkflow.sh
```

The default delete-arkouda-on-kubernetes-cronworkflow configuration is to delete arkouda-on-kubernetes daily at 1700 EST. The cron configuration can be changed in the [spec.schedule](https://github.com/hokiegeek2/arkouda-contrib/blob/62c099130d78ed523951aac11893298f3b9c752f/arkouda_workflows/delete-arkouda-on-kubernetes-cronworkflow.yaml#L6) section of the delete-arkouda-on-kubernetes-cronworkflow.yaml file as shown below:

```
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  name: delete-arkouda-on-kubernetes
spec:
  schedule: "* 17 * * *"
```
