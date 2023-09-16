# arkouda_workflows

## Background


## Commands

### deploy arkouda workflow

```
argo submit -n arkouda arkouda-on-kubernetes/arkouda-on-kubernetes-deploy.yaml -p arkouda-release-version=v2023.09.06 \
            -p arkouda-ssl-secret=arkouda -p arkouda-ssh-secret=arkouda-ssh -p arkouda-number-of-locales=2 \
            -p arkouda-instance-name=arkouda-on-k8s -p arkouda-total-number-of-locales=3 \
            -p kubernetes-api-url=https://192.168.1.11:6443 -p arkouda-namespace=arkouda -p arkouda-server-name=arkouda-on-k8s \             
            -p arkouda-service-port=5555 -p arkouda-metrics-service-name=arkouda-on-k8s-metrics -p arkouda-metrics-service-port=5556 \
            -p arkouda-log-level=LogLevel.DEBUG -p arkouda-user=arkouda -p metrics-exporter-service-port=5080 \
            -p metrics-polling-interval-seconds=10 -p image-pull-policy=IfNotPresent
```

### delete arkouda workflow

```
argo submit -n arkouda arkouda-on-kubernetes-delete.yaml -p arkouda-ssl-secret=arkouda-tls \
            -p arkouda-instance-name=arkouda-on-k8s -p kubernetes-api-url=https://192.168.1.11:6443 -p arkouda-user=arkouda 
```
