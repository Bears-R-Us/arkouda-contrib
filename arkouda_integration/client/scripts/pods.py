import argparse
from arkouda_integration.k8s import KubernetesDao, InvocationMethod
from arkouda.logger import getArkoudaLogger

logger = getArkoudaLogger(name="Arkouda Integration pods script")

def main(cacert_file : str, token : str, k8s_host : str, invocation_method : str, 
         app_name : str, namespace : str='default'):
    dao = KubernetesDao(cacert_file, token, k8s_host)

    pod_method = InvocationMethod(invocation_method)

    if pod_method == InvocationMethod.GET_POD_IPS:
        print(
            dao.get_pod_ips(namespace=namespace, 
                        app_name=app_name, 
                        pretty_print=True))
    elif pod_method == InvocationMethod.GET_PODS:
        print(dao.get_pods(namespace=namespace, 
                           app_name=app_name, 
                           pretty_print=True))
    else:
        logger.error(f'{pod_method} is not supported from the command line')

if __name__ == "__main__":
    import os
    cacert_file = os.environ['CACERT_FILE']
    token = os.environ['SSL_TOKEN']
    k8s_host = os.environ['K8S_HOST']
    invocation_method = os.environ['POD_METHOD']
    app_name = os.environ['APP_NAME']
    namespace = os.environ['NAMESPACE']

    main(cacert_file=cacert_file,
         token=token,
         k8s_host=k8s_host,
         invocation_method=invocation_method,
         app_name=app_name,
         namespace=namespace
         )
