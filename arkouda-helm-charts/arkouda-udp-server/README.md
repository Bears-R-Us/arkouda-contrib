# arkouda-udp-server

## Overview

The arkouda-udp-server Helm chart deploys the containerized Arkouda server (locale 0) instance that bootstraps a multi-locale Arkouda cluster that communicates via gasnet/udp. 

## Arkouda-on-Kubernetes API Pre-requisites

arkouda-udp-server generates GASNET udp connections with all previously-deployed arkouda-udp-locale pods, registers itself as a service, and creates a Prometheus scrape target via Kubernetes API CRUD operations. Accordingly, the following Kubernetes artifacts are required:

1. Kubernetes user that is to be bound to the requisite Roles
2. TLS secret composed of the .key and .crt files used to create the Kubernetes user and enable Kubernetes API requests
3. Roles with permissions to enable Kubernetes API requests
4. RoleBindings that bind the k8s Roles to the Kubernetes user
5. SSH secret to enable GASNET udp startup of all Arkouda locale pods

### Kubernetes User

The workflow for creating an a Kubernetes user that can be bound to Roles possessing the required Kubernetes API permissions is as follows:

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

The .key and .crt files created above are used to create a Kubernetes secret, which is used to connect to the Kubernetes API and load permissions from the Roles bound to the user. Important note: the secret must be deployed to the same namespace arkouda-udp-server and arkouda-udp-locale are deployed.

An example Kubernetes secret create command is as follows:

```
kubectl create secret tls arkouda-tls --cert=arkouda.crt --key=arkouda.key -n arkouda
```

### Roles

The Kubernetes API permissions are in the form of a Role (scoped to the arkouda-udp-locale/arkouda-udp-server deployment namespace). For the purposes of this demonstration, the Roles are as follows:

#### GASNET udp Integration

The arkouda-udp-server deployment discovers all arkouda-udp-locale pods on startup to create the GASNET udp connections between all Arkouda locales. Accordingly, Arkouda requires Kubernetes pod list and get permissions. The corresponding Role is as follows:

```
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: arkouda-pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
```

This Role is bound to the arkouda Kubernetes user as follows:

```
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: arkouda-pod-reader
subjects:
- kind: User
  name: {{ .Values.user }}
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

#### Service Integration

Arkouda-on-Kubernetes integrates with Kubernetes service discovery by creating a Kubernetes service upon arkouda-udp-server startup and deleting the Kubernetes service upon teardown. Consequently, Arkouda-on-Kubernetes requires full Kubernetes service CRUD permissions to enable service discovery. The corresponding Role is as follows:

```
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: arkouda-service-endpoints-crud
rules:
- apiGroups: [""]
  resources: ["services","endpoints"]
  verbs: ["get","watch","list","create","delete","update"]
```

This Role is bound to the arkouda Kubernetes user as follows:

```
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: arkouda-service-endpoints-crud
subjects:
- kind: User
  name: {{ .Values.user }}
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: arkouda-service-endpoints-crud
  apiGroup: rbac.authorization.k8s.io
```

#### Role and RoleBinding Files

While the Role and RoleBinding file contents are detailed above, all required Role and RoleBinding files are located in the [templates](templates) directory, and, consequently, are deployed with arkouda-udp-server.

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

The arkouda-udp-server Helm deployment is configured within the [values.yaml](values.yaml) file.

The releaseVersion parameter (Arkouda tag) and imagePullPolicy are set at the top of the Pod Settings section.

### resources

The resource request and limit parameters are specified in the resources element of the Pod Settings section:

```
resources:
  limits:
    cpu: 1000m
    memory: 2024Mi
  requests:
    cpu: 1000m
    memory: 2024Mi
```

### server

```
server: 
  numLocales: # total number of Arkouda locales = number of arkouda-udp-locale pods + 1
  authenticate: false # whether to require token authentication
  verbose: false # enable verbose logging
  memTrack: true # enable memory tracking (required for memMax and metrics export)
  memMax: # maximum bytes of RAM to be used per locale
  threadsPerLocale: # number of cpu cores to be used per locale
  logLevel: LogLevel.DEBUG # logging level
  name: # k8s app name
  service:
    type: ClusterIP
    port: 5555 # Arkouda k8s service port
    name: # k8s service name for Arkouda server
  metrics:
    collectMetrics: true # indicates whether to collecte metrcis
    service:
      name: # service name for Arkouda metrics service endpoint
      port: 5556
```

### locale

```
locale:
  name: # arkouda-udp-locale app name used to find locale IP addresses
  podMethod: GET_POD_IPS 
```

### external

The external section encapsulates the parameters for Arkouda registering with Kubernetes.

```
external:
  k8sHost: # Kubernetes API url used to register service(s)
  namespace: # namespace Arkouda will register service
```

### persistence

The persistence section configures the container and host paths that, if persistence is enabled, enables users to write out Arkouda arrays to files:

```
persistence:
  enabled: false # indicates whether files can be written to/read from the host system
  containerPath: /arkouda-files # container directory for reading/writing Arkouda files
  hostPath: /mnt/data/arkouda-files # host directory for reading/writing Arkouda files
```

### metricsExporter

The metricsExporter section configures the embedded prometheus-arkouda-exporter which is deployed if server.metrics.collectMetrics = true.

```
metricsExporter:
  name: # Kubernetes app and server name for prometheus-arkouda-exporter
  releaseVersion: v2024.02.02 # bearsrus prometheus-arkouda-exporter image version
  imagePullPolicy: IfNotPresent
  pollingIntervalSeconds: 10 # polling interval prometheus-arkouda-exporter willl pull metrics from Arkouda
  serviceMonitor:
    enabled: true # indicates if ServiceMonitor registration is to be used, defaults to true
    pollingInterval: 15s
    additionalLabels:
      launcher: kubernetes
    targetLabels:
      - arkouda_instance
      - launcher
```

The prometheus-arkouda-exporter registers as a Prometheus scrape target via the Prometheus [ServiceMonitor](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/getting-started.md).

### user

The name and the uid for the user running Arkouda if user-specific Arkouda is enabled. This setting is important if users wish to write Arkouda arrays out to Parquet or HDF5 as directory permissions require. 

```
user:
  enabled: false # indicates whether to run Arkouda as a specified user
  name: # name of user running arkouda and CN for corresponding secret for rolebindings
  uid: # uid of user running Arkouda
```

### group

The name and gid corresponding the user Arkouda is running as. The gid is normally used to enable writing Arkouda files to common-use directories:

```
group:
  enabled: false # indicates whether to run Arkouda as a specified user with corresponding group
  name: # name of group user needs to configured for to execute host commands
  gid: # gid of group user needs to configured for to execute host commands
```

### secrets

The tls and ssh secrets that enable Arkouda-on-Kubernetes to access the Kuberetes API on startup are encapsulated in the secrets.tls and secrets.ssh parameters:

```
secrets:
  tls: # name of tls secret used to access Kubernetes API
  ssh: # name of ssh secret used to launch Arkouda locales
```

## Helm Install Command

An example Helm install command is shown below:

```
helm install -n arkouda arkouda-server arkouda-udp-server/
```
