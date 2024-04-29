# arkouda-udp-locale

## Overview

The arkouda-udp-locale Helm chart deploys 1..n arkouda-udp-locale docker containers that, together with the arkouda-udp-server bootstrap server, compose the Arkouda-on-Kubernetes deployment. The arkouda-udp-locale Helm chart is deployed first and, once all of the arkouda-udp-locale pods are running, the arkouda-udp-server Helm chart is deployed. The arkouda-udp-server container uses ssh to establish a gasnet/udp-managed Arkouda multi-locale instance.

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

### locale

The locale configuration section sets the number of arkouda-locale containers to startup along with other parameters as shown below:

```
locale: 
  numLocales: # number of arkouda-udp-locale pods
  memTrack: true
  name: # Kubernetes app name used by arkouda-udp-server for pod discovery
  threadsPerLocale: # number of cpu cores assigned to each Arkouda locale
```

### persistence

The persistence section configures the container and host paths that, if persistence is enabled, enables users to write out Arkouda arrays to files:

```
persistence: 
  enabled: false
  containerPath: /arkouda-files # container directory for reading/writing Arkouda files
  hostPath: /mnt/data/arkouda-files # host directory for reading/writing Arkouda files
```

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

The ServiceAccount bearer token and ssh secrets that enable Arkouda-on-Kubernetes to access the Kuberetes API on startup are encapsulated in the secrets.tls and secrets.ssh parameters:

```
secrets:
  ssh: # name of ssh secret used to launch Arkouda locales
  sa: # name of ServiceAccount bearer token secret used to access Kubernetes API
```

## Helm Install Command

```
helm install -n arkouda arkouda-locale arkouda-udp-locale/
```
