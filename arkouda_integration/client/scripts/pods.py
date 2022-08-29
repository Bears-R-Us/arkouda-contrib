import argparse
from arkouda_integration.k8s import KubernetesDao, InvocationMethod
from arkouda.logger import getArkoudaLogger

logger = getArkoudaLogger(name="Arkouda Integration pods script")

def main(crt_file : str, key_file : str, k8s_host : str, invocation_method : str, 
                         app_name : str, namespace : str='default'):
    dao = KubernetesDao(crt_file,key_file,k8s_host)

    pod_method = InvocationMethod(invocation_method)

    if pod_method == InvocationMethod.GET_POD_IPS:
        print(
            dao.get_pod_ips(namespace=namespace, 
                        app_name=app_name, 
                        pretty_print=True)
        )
    elif pod_method == InvocationMethod.GET_PODS:
        print(
            dao.get_pods(namespace=namespace, 
                         app_name=app_name, 
                         pretty_print=True)
        )
    else:
        logger.error(
            "{} is not supported from the command line".format(pod_method)
        )

if __name__ == "__main__":
    import os
    crt_file = os.environ['CERT_FILE']
    key_file = os.environ['KEY_FILE']
    k8s_host = os.environ['K8S_HOST']
    invocation_method = os.environ['POD_METHOD']
    app_name = os.environ['APP_NAME']
    namespace = os.environ['NAMESPACE']

    main(crt_file=crt_file,
         key_file=key_file,
         k8s_host=k8s_host,
         invocation_method=invocation_method,
         app_name=app_name,
         namespace=namespace
         )
