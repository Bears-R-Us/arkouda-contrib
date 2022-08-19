import os, subprocess, unittest
import arkouda as ak

class BaseTest(unittest.TestCase):
    
    def setUp(self):
        self.port = int(os.getenv("ARKOUDA_SERVER_PORT", 5555))
        self.host = os.getenv("ARKOUDA_SERVER_HOST", "localhost")
        self.mode = os.getenv("ARKOUDA_RUNNING_MODE", "FULL_STACK")
        
        if self.mode == "FULL_STACK":
            self.startup()

    def startup(self):
        path = os.environ["ARKOUDA_HOME"]
        if not path:
            raise EnvironmentError('ARKOUDA_HOME must be set')

        arkoudaPath = f'{path}/arkouda_server'
        self.process = subprocess.Popen([arkoudaPath,'-nl 1',
                '--ServerDaemon.daemonTypes=ServerDaemonType.DEFAULT,ServerDaemonType.METRICS'])
        ak.connect(self.host,self.port)        
    
    def shutdown(self):
        self.process.kill()
    
    def tearDown(self):
        if self.mode == "FULL_STACK":
            self.shutdown()