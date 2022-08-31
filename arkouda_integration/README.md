# arkouda\_integration

## Overview 

The arkouda\_integration project provides a Python API for integrating Arkouda with external systems such as Kubernetes. 

## Installation

arkouda\_integration depends upon [Arkouda](https://github.com/Bears-R-Us/arkouda) and install instructions are located [here](https://github.com/Bears-R-Us/arkouda/blob/master/INSTALL.md)

With Arkouda installed, cd to the arkouda\_integration/client folder and execute the following command:

```
pip3 install -e .
```

## Usage

The arkouda\_integration project can be used via the Python REPL, via project [scripts](client/scripts), or within other applications.

### arkouda\_integration via Python REPL

#### get\_pods

```
dao.get_pods(namespace='arkouda')
```

#### get\_pod\_ips

```
dao.get_pod_ips(namespace='arkouda', app_name='arkouda-locale', pretty_print=True)
"'10.42.1.128' '10.42.2.83'"
```

#### create\_service

```
dao.create_service(service_name='arkouda-k8s', app_name='arkouda-single-locale', port=6555, target_port=5555, namespace='arkouda')
```

#### delete\_service

```
dao.delete_service(service_name='arkouda-k8s', namespace='arkouda')
```

### arkouda\_integration Scripts

#### [pods.py](client/scripts/pods.py)

```
export KEY_FILE=/home/ubuntu/development/arkouda.key
export CERT_FILE=/home/ubuntu/development/arkouda.crt
export K8S_HOST=https://localhost:6443
export POD_METHOD=GET_POD_IPS
export APP_NAME='arkouda-locale'
export NAMESPACE='arkouda'
python client/scripts/pods.py 
'10.42.1.128' '10.42.2.83'
```

## Tests

The arkouda\_integration unit tests are executed from the arkouda\_integration home directory as follows:

```
pytest
```
