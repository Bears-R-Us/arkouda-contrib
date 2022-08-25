# arkouda_integration

## Overview 

The arkouda_integration project provides a Python API for integrating Arkouda with external systems such as Kubernetes. 

## Installation

arkouda_integration depends upon [Arkouda](https://github.com/Bears-R-Us/arkouda) and install instructions are located [here](https://github.com/Bears-R-Us/arkouda/blob/master/INSTALL.md)

With Arkouda installed, cd to the arkouda_integration/client folder and execute the following command:

```
pip3 install -e .
```

## Usage

### Configuring arkouda_metrics_exporter

The following env variables are set to configure the arkouda_metrics_exporter:

1. ARKOUDA_METRICS_SERVICE_HOST: Arkouda server host (ip address, hostname, or Kubernetes service name), defaults to localhost
2. ARKOUDA_METRICS_SERVICE_PORT: Port number for Arkouda metrics service endpoint, defaults to 5556
3. ARKOUDA_METRICS_SERVER_NAME: Name of Arkouda metrics server endpoint, defaults to arkouda-metrics
4. METRICS_POLLING_INTERVAL: Polling interval in seconds for retrieving Arkouda metrics, defaults to 
5. METRICS_SCRAPE_PORT: Port number for the Prometheus scrape target, defaults to 5080

### Running arkouda_metrics_exporter

```
python3 -c "from arkouda_metrics_exporter import metrics; metrics.main()"
```
