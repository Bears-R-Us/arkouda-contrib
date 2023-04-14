# arkouda-helm-charts

## Background

The arkouda-helm-charts project provides Helm charts for deploying containerized Arkouda to Kubernetes. The complete Arkouda-on-Kubernetes set of Helm charts includes the [arkouda-udp-server](arkouda-udp-server), [arkouda-udp-locale](arkouda-udp-locale), and [prometheus-arkouda-exporter](prometheus-arkouda-exporter) Helm charts.

## Arkouda-on-Kubernetes Helm Charts

### arkouda-udp-locale

The [arkouda-udp-locale](arkouda-udp-locale) Helm chart deploys 1..n [arkouda-udp-server](https://github.com/Bears-R-Us/arkouda-contrib/blob/main/arkouda-docker/arkouda-udp-server) containers that correspond to Arkouda locales 1..(n-1). The arkouda-udp-locale Helm chart is deployed first, which enables the arkouda-udp-server (see further explanation below) to discover the pods corresponding to locales 1..(n-1) via pod IP lookup.

### arkouda-udp-server

The [arkouda-udp-server](arkouda-udp-server) Helm chart deploys the containerized Arkouda locale 0 instance that bootstraps a multi-locale Arkouda cluster that communicates via gasnet/udp. Specifically, the [arkouda-driver](arkouda-udp-server/templates/arkouda-driver.yaml) Pod discovers the [arkouda-locale](arkouda-udp-locale/templates/arkouda-locale.yaml) pods, adds those IP addresses to the GASNET SSH\_SERVERS environment variable, and then starts up the Arkouda cluster via the GASNET udp launcher. Accordingly, as noted above, _the arkouda-udp-server must be deployed after arkouda-udp-locale is deployed and the corresponding pods are running_. 

