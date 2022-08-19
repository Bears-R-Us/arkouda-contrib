import os
from prometheus_client import REGISTRY
import arkouda as ak
from arkouda_metrics_exporter.metrics import ArkoudaMetrics
from metrics.base_test import BaseTest

class MetricsExporterTest(BaseTest):  
      
    def setUp(self):
        BaseTest.setUp(self)
        self.metricsPort = int(os.getenv("ARKOUDA_METRICS_PORT", 5556))
        self._clearOutRegistry()
        self.metrics = ArkoudaMetrics(arkoudaMetricsHost=self.host,
                                      arkoudaMetricsPort=self.metricsPort)
        
    def _clearOutRegistry(self):
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            REGISTRY.unregister(collector)
    
    def testArkoudaMetricsState(self):
        self.assertEqual(self.host, self.metrics.arkoudaMetricsHost)
        self.assertEqual(self.metricsPort, self.metrics.arkoudaMetricsPort)
        self.assertEqual(5, self.metrics.pollingInterval)
        self.assertEqual(5080,  self.metrics.scrapePort)
    
    def testServerInfo(self):
        self.metrics.fetch()
        info = self.metrics.arkoudaServerInfo.collect()[0]
        sample = info.samples[0]
        self.assertEqual('arkouda_server_information_info', sample.name)
        self.assertEqual(1, int(sample.labels['arkouda_number_of_locales']))
        self.assertEqual('arkouda-metrics', sample.labels['arkouda_server_name'])
        self.assertEqual(4,len(sample.labels))
    
    def testTotalNumberOfRequests(self):
        self.metrics.fetch()
        metric = self.metrics.totalNumberOfRequests.collect()[0]
        firstValue = metric.samples[0].value

        ak.connect(self.host,self.port)
        ak.get_config()

        self.metrics.fetch()
        metric = self.metrics.totalNumberOfRequests.collect()[0]
        secondValue = metric.samples[0].value
        self.assertTrue(secondValue > firstValue)
        
    def testNumberOfRequestsPerCommand(self):
        self.metrics.fetch()
        metric = self.metrics.numberOfRequestsPerCommand.collect()[0]
        
        connectValue = 0
        
        for sample in metric.samples:
            self.assertEqual('arkouda_number_of_requests_per_command', sample.name)
            if 'connect' == sample.labels['command']:
                connectValue = sample.value

        ak.connect(self.host,self.port)
        self.metrics.fetch()
        metric = self.metrics.numberOfRequestsPerCommand.collect()[0]
        
        for sample in metric.samples:
            self.assertEqual('arkouda_number_of_requests_per_command', sample.name)
            if 'connect' == sample.labels['command']:
                self.assertTrue(sample.value >= connectValue+1)
                
        ak.connect(self.host,self.port)
        self.metrics.fetch()
        metric = self.metrics.numberOfRequestsPerCommand.collect()[0]
        
        for sample in metric.samples:
            self.assertEqual('arkouda_number_of_requests_per_command', sample.name)
            if 'connect' == sample.labels['command']:
                self.assertTrue(sample.value >= connectValue+2)