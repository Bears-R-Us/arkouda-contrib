# arkouda_workflows

## Background

[Argo Workflows](https://argoproj.github.io/argo-workflows/) is an ideal approach to manage all the dependencies involved in deploying Arkouda on Kubernetes (AoK) via [arkouda-udp-locale](https://github.com/Bears-R-Us/arkouda-contrib/tree/main/arkouda-helm-charts/arkouda-udp-locale) and [arkouda-udp-server](https://github.com/Bears-R-Us/arkouda-contrib/tree/main/arkouda-helm-charts/arkouda-udp-server) as well as the [prometheus-arkouda-exporter](https://github.com/Bears-R-Us/arkouda-contrib/tree/main/arkouda-helm-charts/prometheus-arkouda-exporter) deployment.

## Workflows

There are four Arkouda argo workflows:

1. deploy-arkouda-on-kubernetes
2. delete-arkouda-on-kubernetes
3. deploy-prometheus-arkouda-exporter
4. delete-prometheus-arkouda-exporter

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

The [deploy-arkouda-on-kubernetes-command.sh](deploy-arkouda-on-kubernetes-command.sh) script is used to deploy  Arkouda-on-Kubernetes, an example of which is shown below:

```
export ARKOUDA_USER=arkouda
export ARKOUDA_NAMESPACE=arkouda
export ARKOUDA_INSTANCE_NAME=arkouda-on-k8s
ARKOUDA_SSH_SECRET=arkouda-ssh
ARKOUDA_SSL_SECRET=arkouda-tls
ARKOUDA_VERSION=v2023.09.06

sh deploy-arkouda-on-kubernetes-command.sh 
```

### delete arkouda workflow

```
export ARKOUDA_USER=arkouda
export ARKOUDA_NAMESPACE=arkouda
export ARKOUDA_INSTANCE_NAME=arkouda-on-k8s
ARKOUDA_SSL_SECRET=arkouda-tls

sh delete-arkouda-on-kubernetes-command.sh 
```
