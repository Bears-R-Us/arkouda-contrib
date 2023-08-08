# arkouda-udp-server

## Overview

The arkouda-udp-server Helm chart deploys the containerized Arkouda server (locale 0) instance that bootstraps a multi-locale Arkouda cluster that communicates via gasnet/udp. 

## Arkouda-on-Kubernetes API Pre-requisites

arkouda-udp-server generates GASNET udp connections with all previously-deployed arkouda-udp-locale pods, registers itself as a service, and creates a Prometheus scrape target via Kubernetes API CRUD operations. Accordingly, the following Kubernetes artifacts are required:

1. Kubernetes user that is to be bound to the requisite ClusterRoles
2. TLS secret composed of the .key and .crt files used to create the Kubernetes user and enable Kubernetes API requests
3. ClusterRoles with permissions to enable Kubernetes API requests
4. ClusterRoleBindings that bind the ClusterRoles to the Kubernetes user
5. SSH secret to enable GASNET udp startup of all Arkouda locale pods

### Kubernetes User

The workflow for creating an a Kubernetes user that can be bound to Roles/ClusterRoles possessing the required Kubernetes API permissions is as follows:

```
# Generate base key file
openssl genrsa -out arkouda.key 2048
 
# User and password generated in this step
openssl req -new -key arkouda.key -out arkouda.csr
 
# sign with the configured k8s CA
sudo openssl x509 -req -in arkouda.csr -CA /etc/kubernetes/pki/ca.crt -CAkey /etc/kubernetes/pki/ca.key -CAcreateserial -out arkouda.crt -days 730

# Create the arkouda user with the generated credentials
kubectl config set-credentials arkouda --client-certificate=arkouda.crt --client-key=arkouda.key

```

Note: the cert CN is the Kubernetes user name

### TLS Secret

The .key and .crt files created above are used to create a Kubernetes secret, which is used to connect to the Kubernetes API and load permissions from the Roles and/or ClusterRoles bound to the user. Important note: the secret must be deployed to the same namespace arkouda-udp-server and arkouda-udp-locale are deployed.

An example Kubernetes secret create command is as follows:

```
kubectl create secret tls arkouda-tls --cert=arkouda.crt --key=arkouda.key -n arkouda
```

### ClusterRoles

The Kubernetes API permissions are in the form of a ClusterRole (scoped to all namespaces). For the purposes of this demonstration, the ClusterRoles are as follows. Corresponding Role definitions only differ in that that the Kind field is Role and metadata has a namespace element.

#### GASNET udp Integration

The arkouda-udp-server deployment discovers all arkouda-udp-locale pods on startup to create the GASNET udp connections between all Arkouda locales. Accordingly, Arkouda requires Kubernetes pod list and get permissions. The corresponding ClusterRole is as follows:

```
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: arkouda-pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
```

This ClusterRole is bound to the arkouda Kubernetes user as follows:

```
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: arkouda-pod-reader-binding
subjects:
- kind: User
  name: arkouda
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

#### Service Integration

Arkouda-on-Kubernetes integrates with Kubernetes service discovery by creating a Kubernetes service upon arkouda-udp-server startup and deleting the Kubernetes service upon teardown. Consequently, Arkouda-on-Kubernetes requires full Kubernetes service CRUD permissions to enable service discovery. The corresponding ClusterRole is as follows:

```
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: service-endpoints-crud
rules:
- apiGroups: [""]
  resources: ["services","endpoints"]
  verbs: ["get","watch","list","create","delete","update"]
```

This ClusterRole is bound to the arkouda Kubernetes user as follows:

```
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: arkouda-service-endpoints-crud
subjects:
- kind: User
  name: arkouda
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: service-endpoints-crud
  apiGroup: rbac.authorization.k8s.io
```

### SSH Secret

An SSH key pair deployed within Kubernetes as a secret is required for all Arkouda locales to startup via the GASNET udp with the S (SSH) spawner. _Since the arkouda pods launch as the ubuntu user, the SSH key pair must be generated as the ubuntu user._ The key pair can be generated as the ubuntu user either on a host system that is running ubuntu or within one of the bearsrus Arkouda docker images 

An example SSH key on a host system is as follows:

```
# Generate the SSH key pair
sudo su ubuntu
ssh-keygen

Generating public/private rsa key pair.
Enter file in which to save the key (/home/ubuntu/.ssh/id_rsa): 
Enter passphrase (empty for no passphrase): 
Enter same passphrase again: 
Your identification has been saved in /home/ubuntu/.ssh/id_rsa.
Your public key has been saved in /home/ubuntu/.ssh/id_rsa.pub.
The key fingerprint is:
SHA256:WlMCThVDnCzqz5n/dCDVHW0h4grCt/nJbBwHpOSEQ78 ubuntu@ace
The key's randomart image is:
+---[RSA 2048]----+
|    ..+B=+ . ..o.|
|    .=*.*.......o|
|     +oB..o.. .. |
|    . o =+o      |
|   .   ESo..     |
|    .  o=o+.     |
|     o.o B. .    |
|      = .. .     |
|       ....      |
+----[SHA256]-----+

# Mount the SSH key pair as the arkouda-ssh secret
kubectl create secret generic arkouda-ssh --from-file=~/.ssh/id_rsa --from-file=~/.ssh/id_rsa.pub -n arkouda
```

## Configuration

The arkouda-udp-server Helm deployment is configured within the [values.yaml](values.yaml).

### values.yaml

#### server

```
server:
  totalNumLocales: # totalNumLocales = number of arkouda-udp-locale pods + 1 (arkouda-udp-server pod)
  authenticate: # whether to require token authentication
  verbose: # enable verbose logging
  memTrack: true
  threadsPerLocale: # number of cpu cores to be used per locale
  memMax: # maximum bytes of RAM to be used per locale
  logLevel: LogLevel.INFO
  service:
    type: # k8s service type, usually ClusterIP, NodePort, or LoadBalancer
    port: # service port Arkouda is listening on, defaults to 5555
    nodeport: # if service type is Nodeport
    name: # service name
  metrics:
    collectMetrics: # whether to collect metrics and make them available via  k8s service
    service:
      name: # k8s service name for the Arkouda metrics service endpoint
      port: # k8s service port for the Arkouda metrics service endpoint, defaults to 5556
```

#### external

```
external:
  persistence:
    enabled: false
    path: /opt/locale # pod directory path DO NOT CHANGE
    hostPath: # host machine path
  k8sHost:
  namespace: # namespace Arkouda will register service
  service:
    name: # k8s service name Arkouda will register
    port: # k8s service port Arkouda will register, defaults to 5555
```

#### metricsExporter

The metricsExporter section configures the embedded prometheus-arkouda-exporter which is deployed if server.metrics.collectMetrics = true.

```
metricsExporter:
  imageRepository: bearsrus
  releaseVersion: # prometheus-arkouda-exporter release version
  imagePullPolicy: IfNotPresent
  service:
    name: # prometheus-arkouda-exporter service name
    port: # prometheus-arkouda-exporter service port, defaults to 5080
  pollingIntervalSeconds: 5
```

The prometheus-arkouda-exporter registers as a Prometheus scrape target via the Prometheus [ServiceMonitor](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/getting-started.md).

## Helm Install Command

An example Helm install command is shown below:

```
helm install -n arkouda arkouda-server arkouda-udp-server/
```
