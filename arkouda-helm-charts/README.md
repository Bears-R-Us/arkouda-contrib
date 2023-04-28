# arkouda-helm-charts

## Overviews

The bears-r-us arkouda-helm-charts project provides two Helm charts that enable Arkouda to be deployed on Kubernetes as well as a Helm chart that enables Arkouda metrics to be captured in Prometheus.

## arkouda-udp-locale

The [arkouda-udp-locale](arkouda-udp-locale) Helm chart deploys 1..n arkouda-udp-locale docker containers that, together with the arkouda-udp-server bootstrap server, compose the Arkouda-on-Kubernetes deployment. The arkouda-udp-locale Helm chart is deployed first and, once all of the arkouda-udp-locale pods are running, the arkouda-udp-server Helm chart is deployed. The arkouda-udp-server container uses ssh to establish a gasnet/udp-managed Arkouda multi-locale instance.

## arkouda-udp-server

The [arkouda-udp-server](arkouda-udp-server) Helm chart deploys the containerized Arkouda server instance that bootstraps a multi-locale Arkouda cluster that communicates via gasnet/udp.

## prometheus-arkouda-exporter

The [prometheus-arkouda-exporter](prometheus-arkouda-exporter) Helm chart deploys a prometheus-arkouda-exporter that pulls metrics from Arkouda and serves as a Prometheus scrape target.
