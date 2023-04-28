# prometheus-arkouda-exporter

## Configuration

### Arkouda Metrics Server Configuration

The arkouda.metrics section configures the Arkouda instance the prometheus-arkouda-exporter will pull metrics from:

```
arkouda:
  metrics:
    server:
      name: external-arkouda # maps to arkouda_server_name Prometheus label
      namespace: arkouda # Arkouda service deployment namespace
    service:
      name: # <Arkouda metrics service name>.<Arkouda deployment namespace>
      port: # Arkouda metrics port, defaults to 5556
```

### Prometheus Arkouda Exporter Configuration

```
exporter:
  server:
    appName: external-arkouda-metrics-server # prometheus-arkouda-exporter k8s app name
    pollingIntervalSeconds: 5 # polling interval
  service:
    name: # prometheus-arkouda-exporter k8s service name
    port: 5080 # prometheus-arkouda-exporter k8s service port
```

### Prometheus 

Prometheus is configured manually its prometheus.yaml file, the Prometheus [ServiceMonitor](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/getting-started.md#deploying-a-sample-application), or [PodMonitor](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/getting-started.md#using-podmonitors). ServiceMonitor and/or PodMonitor configuration(s) will be added soon to the arkouda-udp-server deployment.

In the meantime, adding the prometheus-arkouda-exporter as a scrape target to the prometheus.yaml is as follows:

Within the static\_config section, add an entry for the prometheus-arkouda-exporter container:

```
    scrape_configs:
      - job_name: # desired prometheus scrape target job name
        static_configs:
          - targets:
            - metricsExporter.service.name.metricsExporter.namespace:metricsExporter.service.port
            labels:
              arkouda_instance: # Arkouda target service name
              launch_method: # Arkouda launch method, either Slurm or Kubernetes
```


## Helm Install Command

An example helm install is as follows. Again, the namespace prometheus-arkouda-exporter is deployed to _must match the namespace the API secret is deployed in._

```
 helm install -n arkouda promethues-arkouda-exporter prometheus-arkouda-exporter/
```

