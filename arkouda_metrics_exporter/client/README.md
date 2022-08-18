# arkouda_metrics_exporter

The arkouda_metrics_exporter project provides a Prometheus metrics export capability to Arkouda via the ArkoudaMetrics class, which does the following:

1. Polls the Arkouda metrics socket for metrics
2. Updates corresponding Prometheus data structures
3. Provides a Prometheus scrape target

The arkouda_metrics_exporter project leverages the Prometheus [prometheus-client](https://github.com/prometheus/client_python) for all Prometheus metrics as well as the embedded http_server to deliver the Prometheus scrape target.


## Installation

arkouda_metrics_exporter depends upon [arkouda](https://github.com/Bears-R-Us/arkouda) and [prometheus_client](https://pypi.org/project/prometheus-client/). Since there currently is no pypi Arkouda installer, an arkouda clone/code download followed by pip install precedes installing arkouda_metrics_exporter:

```
git clone git@github.com:Bears-R-Us/arkouda.git
cd arkouda
pip3 install -e .
```

From the arkouda_metrics_server client folder, execute the following command:

```
pip3 install -e .
```

## Usage

### Configuring arkouda_metrics_exporter

The following env variables are set to configure the arkouda_metrics_server:

1. ARKOUDA_METRICS_SERVICE_HOST: Arkouda server host (ip address, hostname, or Kubernetes service name), defaults to localhost
2. ARKOUDA_METRICS_SERVICE_PORT: Port number for Arkouda metrics service endpoint, defaults to 5556
3. ARKOUDA_METRICS_SERVER_NAME: Name of Arkouda metrics server endpoint, defaults to arkouda-metrics
4. METRICS_POLLING_INTERVAL: Polling interval in seconds for retrieving Arkouda metrics, defaults to 5
5. METRICS_SCRAPE_PORT: Port number for the Prometheus scrape target, defaults to 5080

### Running arkouda_metrics_exporter

```
python3 -c "from arkouda_metrics_exporter import metrics; metrics.main()"
```

Example output from arkouda_metrics_exporter is as follows:

```
python -c "from arkouda_metrics_exporter import metrics; metrics.main()"
    _         _                   _       
   / \   _ __| | _____  _   _  __| | __ _ 
  / _ \ | '__| |/ / _ \| | | |/ _` |/ _` |
 / ___ \| |  |   < (_) | |_| | (_| | (_| |
/_/   \_\_|  |_|\_\___/ \__,_|\__,_|\__,_|
                                          

Client Version: v2022.07.28+42.g3e299b22.dirty
Starting Prometheus scrape endpoint
Started Prometheus scrape endpoint
connected to arkouda metrics server tcp://*:5556
Completed Initialization of Arkouda Metrics Exporter
Instantiated ArkoudaMetrics and connected to Arkouda
UPDATED METRIC Metric(name='total', category=NUM_REQUESTS, scope=GLOBAL, value=0.0, timestamp=datetime.datetime(2022, 8, 15, 6, 52, 33, 745847), labels=None)
UPDATED METRIC Metric(name='arkouda_memory_used_per_locale', category=SYSTEM, scope=LOCALE, value=0.0, timestamp=datetime.datetime(2022, 8, 15, 6, 52, 33, 745940), labels=[Label(name='locale_name', value='hokiegeek.local'), Label(name='locale_num', value=0), Label(name='locale_hostname', value='hokiegeek.local')])
UPDATED METRIC Metric(name='arkouda_percent_memory_used_per_locale', category=SYSTEM, scope=LOCALE, value=0.0, timestamp=datetime.datetime(2022, 8, 15, 6, 52, 33, 745944), labels=[Label(name='locale_name', value='hokiegeek.local'), Label(name='locale_num', value=0), Label(name='locale_hostname', value='hokiegeek.local')])
UPDATED METRIC Metric(name='total', category=NUM_REQUESTS, scope=GLOBAL, value=0.0, timestamp=datetime.datetime(2022, 8, 15, 6, 52, 38, 751766), labels=None)
UPDATED METRIC Metric(name='arkouda_memory_used_per_locale', category=SYSTEM, scope=LOCALE, value=0.0, timestamp=datetime.datetime(2022, 8, 15, 6, 52, 38, 751847), labels=[Label(name='locale_name', value='hokiegeek.local'), Label(name='locale_num', value=0), Label(name='locale_hostname', value='hokiegeek.local')])
```

Corresponding example output from the Arkouda side is as follows:

```
2022-08-15:06:52:33 [ServerDaemon] run Line 585 DEBUG [Chapel] awaiting message on port 5556
2022-08-15:06:52:33 [MetricsMsg] metricsMsg Line 405 DEBUG [Chapel] category: SERVER_INFO
2022-08-15:06:52:33 [MetricsMsg] metricsMsg Line 431 DEBUG [Chapel] metrics {"hostname":"hokiegeek.local", "version":"v2022.07.28+42.g3e299b22.dirty", "server_port":5555, "locales":[{"name":"hokiegeek.local", "id":"0", "hostname":"hokiegeek.local", "number_of_processing_units":6, "physical_memory":34359738368, "max_number_of_tasks":6}], "number_of_locales":1}
2022-08-15:06:52:33 [ServerDaemon] run Line 585 DEBUG [Chapel] awaiting message on port 5556
2022-08-15:06:52:33 [MetricsMsg] metricsMsg Line 405 DEBUG [Chapel] category: ALL
2022-08-15:06:52:33 [MetricsMsg] getSystemMetrics Line 275 DEBUG [Chapel] memoryUsed: 0 physicalMemory: 34359738368
2022-08-15:06:52:33 [MetricsMsg] metricsMsg Line 431 DEBUG [Chapel] metrics [{"name":"total", "category":"NUM_REQUESTS", "scope":"GLOBAL", "timestamp":"2022-08-15T06:52:33.745847", "value":0.000000e+00}, {"name":"arkouda_memory_used_per_locale", "category":"SYSTEM", "scope":"LOCALE", "timestamp":"2022-08-15T06:52:33.745940", "value":0.000000e+00, "locale_num":0, "locale_name":"hokiegeek.local", "locale_hostname":"hokiegeek.local"}, {"name":"arkouda_percent_memory_used_per_locale", "category":"SYSTEM", "scope":"LOCALE", "timestamp":"2022-08-15T06:52:33.745944", "value":0.000000e+00, "locale_num":0, "locale_name":"hokiegeek.local", "locale_hostname":"hokiegeek.local"}]
2022-08-15:06:52:33 [ServerDaemon] run Line 585 DEBUG [Chapel] awaiting message on port 5556
```

## Tests

### Environment Variables

The vast majority of the default env variables contained in the [pytest.ini](./pytest.ini) file are fine with the exception of ARKOUDA_HOME, which needs to be set for the specific user environment.

The default arkouda_metrics_exporter unit test mode is FULL_STACK, meaning that an arkouda server is started up and torn down for each unit test. If it is preferred to execute unit tests against an existing Arkouda instance, set ARKOUDA_RUNNING_MODE to CLIENT. Important note: the arkouda_server startup command with metrics enabled, which is required to run the test harness, is as follows;

```
./arkouda_server --ServerDaemon.daemonTypes=ServerDaemonType.DEFAULT,ServerDaemonType.METRICS
```

### Running Unit Tests

The arkouda_metrics_exporter unit tests are executed from the arkouda_metrics_exporter project home as follows:

```
pytest
```