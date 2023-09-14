# prometheus-arkouda-exporter

## Configuration

### Arkouda Metrics Server Configuration

The arkouda.metrics section configures the Arkouda target  the prometheus-arkouda-exporter will pull metrics from:

```
arkouda:
  metrics:
    server:
      name: arkouda-on-slurm # maps to arkouda_server_name Prometheus label
      namespace: arkouda # Arkouda service deployment namespace
    service:
      name: # <Arkouda metrics service name>.<Arkouda deployment namespace>
      port: # Arkouda metrics port
```

### Prometheus Arkouda Exporter Configuration

```
exporter:
  server:
    appName: arkouda-metrics-exporter # prometheus-arkouda-exporter k8s app name
    pollingIntervalSeconds: 5 # polling interval
  service:
    name: # prometheus-arkouda-exporter k8s service name
```

### Prometheus 

Prometheus is configured manually its prometheus.yaml file, the Prometheus [ServiceMonitor](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/getting-started.md#deploying-a-sample-application) scrapes the prometheus-arkouda-exporter.

## Helm Install Command

An example helm install is as follows. Again, the namespace prometheus-arkouda-exporter is deployed to _must match the namespace the API secret is deployed in._

```
 helm install -n arkouda promethues-arkouda-exporter prometheus-arkouda-exporter/
```

