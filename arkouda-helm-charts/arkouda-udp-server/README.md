# arkouda-udp-server

## Overview

The arkouda-udp-server Helm chart deploys the containerized Arkouda server (locale 0) instance that bootstraps a multi-locale Arkouda cluster that communicates via gasnet/udp. 

## Arkouda-on-Kubernetes API Pre-requisites

arkouda-udp-server generates GASNET udp connections with all previously-deployed arkouda-udp-locale pods, registers itself as a service, and creates a Prometheus scrape target via Kubernetes API CRUD operations. Accordingly, the following Kubernetes artifacts are required:

1. ServiceAccount that is bound to the Roles required to register Arkouda with Kubernetes
2. service-account-token secret used to authenticate ServiceAccount to Kubernetes API request
3. Roles with permissions to enable Kubernetes API requests
4. RoleBindings that bind the k8s Roles to the Arkouda ServiceAccount
5. SSH secret to enable GASNET UDP startup of all Arkouda locale pods

### ServiceAccount

The Arkouda ServiceAccount is bound to Roles required to register/deregister Arkouda with Kubernetes. An example ServiceAccount is as follows:

```
apiVersion: v1
kind: ServiceAccount
metadata:
  name: arkouda-sa
automountServiceAccountToken: false
```

The ServiceAccount is created in the namespace Arkouda is deployed to. An example kubectl command is as follows:

```
export NAMESPACE=arkouda

kubectl apply -f serviceacount.yaml -n $NAMESPACE
```

### service-account-token

The service-account-token is bound to the Arkouda ServiceAccount and is used to authenticate to the Kubernetes API. An example service-account-token is as follows:

```
apiVersion: v1
kind: Secret
metadata:
  name: arkouda-sa
  annotations:
    kubernetes.io/service-account.name: arkouda-sa # matches the ServiceAccount name defined in previous step
type: kubernetes.io/service-account-token
```

The service-acccount-token is created in the namespace Arkouda is deployed to. An example kubectl command is as follows:

```
export NAMESPACE=arkouda

kubectl apply -f serviceacount-token.yaml -n $NAMESPACE
```

### Roles

The Kubernetes API permissions are in the form of a Role (scoped to the arkouda-udp-locale/arkouda-udp-server deployment namespace). For the purposes of this demonstration, the Roles are as follows:

#### GASNET SSH Launcher

The arkouda-udp-server pod launches all Arkouda locales on startup via SSH to create the GASNET UDP connections between all Arkouda locales. The first step in the SSH locale launcher process is to discover the IP addresses of all arkouda-udp-locale pods. Accordingly, Arkouda requires Kubernetes pod list and get permissions. The corresponding Role is as follows:

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

This Role is bound to the Arkouda ServiceAccount as follows:

```
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: arkouda-pod-reader
subjects:
- kind: ServiceAccount
  name: {{ .Values.serviceaccount }}
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

This Role is bound to the Arkouda Kubernetes ServiceAccount as follows:

```
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: arkouda-service-endpoints-crud
subjects:
- kind: ServiceAccount
  name: {{ .Values.serviceaccount }}
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

An SSH key pair deployed within Kubernetes as a secret is required for all Arkouda locales to startup via the Chapel GASNET UDP comm substrate with the S (SSH) spawner. The key pair is generated as follows:

```
# Generate the SSH key pair
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

The resource request and limit parameters are specified in the resources element of the Pod Settings section. Note: the resource requests and limits parameters are the same because the compute resources allocated to Chapel processes is static.

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
  authenticate: # whether to require token authentication, defaults to false
  verbose: # enable verbose logging, defaults to false
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
  enabled: # indicates whether files can be written to/read from the host system, defaults to false
  containerPath: /arkouda-files # container directory for reading/writing Arkouda files
  hostPath: /mnt/data/arkouda-files/ # host directory for reading/writing Arkouda files
```

### metricsExporter

The metricsExporter section configures the embedded prometheus-arkouda-exporter which is deployed if server.metrics.collectMetrics = true.

```
metricsExporter:
  name: # Kubernetes app and server name for prometheus-arkouda-exporter
  releaseVersion: v2024.04.19 # bearsrus prometheus-arkouda-exporter image version
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
  enabled: # indicates whether to run Arkouda as a specified user, defaults to false
  name: # name of user running arkouda and CN for corresponding secret for rolebindings
  uid: # uid of user running Arkouda
```

### group

The name and gid corresponding the user Arkouda is running as. The gid is normally used to enable writing Arkouda files to common-use directories:

```
group:
  enabled: # indicates whether to run Arkouda as a specified user with corresponding group, defaults to false
  name: # name of group user needs to configured for to execute host commands
  gid: # gid of group user needs to configured for to execute host commands
```

### secrets

The name of the ServiceAccount bearer token secret used to access the Kubernetes API on startup is specified in the secrets.sa parameter while the name of the SSH cert used to launch Arkouda locales via the Chapel UDP launcher is specified in the secrets.ssh parameter:

```
secrets:
  ssh: # name of ssh secret used to launch Arkouda locales
  sa: # name of ServiceAccount bearer token secret used to access Kubernetes API
```

## Helm Install Command

An example Helm install command is shown below:

```
helm install -n arkouda arkouda-server arkouda-udp-server/
```

## Troubleshooting

### SSH Permission Denied 

The following error occurs when the user defined in the arkouda-udp-locale and arkouda-udp-server helm deployments differ:

```
Warning: Permanently added '10.42.3.59' (ED25519) to the list of known hosts.
Warning: Permanently added '10.42.3.77' (ED25519) to the list of known hosts.
Warning: Permanently added '10.42.2.5' (ED25519) to the list of known hosts.
Permission denied, please try again.
Permission denied, please try again.
ubuntu@10.42.3.59: Permission denied (publickey,password).
Permission denied, please try again.
Permission denied, please try again.
ubuntu@10.42.2.5: Permission denied (publickey,password).
```

To fix, check the user and group definition sections of the arkouda-udp-locale/values.yaml and arkouda-udp-server/values.yaml files and ensure they match. To run Arkouda as the default user, both values.yaml files must have the following configuration;

```
user:
  enabled: # indicates whether to run Arkouda as a specified user, defaults to false
  name: # name of user running arkouda and CN for corresponding secret for rolebindings
  uid: # uid of user running Arkouda

group:
  enabled: # indicates whether to run Arkouda as a specified user with corresponding group, defaults to false
  name: # name of group user needs to configured for to execute host commands
  gid: # gid of group user needs to configured for to execute host commands
```

To run Arkouda as a specific user in a specific group, both values.yaml files must have the following configuration:

```
user:
  enabled: true # indicates whether to run Arkouda as a specified user, defaults to false
  name: user # name of user running arkouda and CN for corresponding secret for rolebindings
  uid: 1005 # uid of user running Arkouda

group:
  enabled: true # indicates whether to run Arkouda as a specified user with corresponding group, defaults to false
  name: usergroup # name of group user needs to configured for to execute host commands
  gid: 1006  # gid of group user needs to configured for to execute host commands
```
