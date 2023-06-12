# arkouda-udp-locale

## Overview

The arkouda-udp-locale Helm chart deploys 1..n arkouda-udp-locale docker containers that, together with the arkouda-udp-server bootstrap server, compose the Arkouda-on-Kubernetes deployment. The arkouda-udp-locale Helm chart is deployed first and, once all of the arkouda-udp-locale pods are running, the arkouda-udp-server Helm chart is deployed. The arkouda-udp-server container uses ssh to establish a gasnet/udp-managed Arkouda multi-locale instance.

## Configuration

The arkouda-udp-server Helm deployment is configured within the [values.yaml](values.yaml) file.

### Server

The server configuration section sets the number of arkouda-locale containers to startup along with resources as shown below:

```
server:
  port: 5555
  numLocales: 2
  memTrack: true
  resources:
    limits:
      cpu: 2000m
      memory: 2048Mi
    requests:
      cpu: 2000m
      memory: 2048Mi
  threadsPerLocale: 4
```

### External System

The external section sets the persistence parameters that enable/disable writing to persistent storage:

```
external:
  persistence:
    enabled: true
    path: /arkouda-files
    hostPath: /mnt/data/arkouda
```

## Helm Install Command

```
helm install -n arkouda arkouda-locale arkouda-udp-locale/
```
