import argparse
from enum import Enum
from typing import List, Optional, Union

# Set client mode to API to prevent splash message print
import os
os.environ['ARKOUDA_CLIENT_MODE'] = 'API'

from kubernetes import client  # type: ignore
from kubernetes.client import (  # type: ignore
    V1ObjectMeta,
    V1Pod,
    V1Service,
    V1ServicePort,
    V1ServiceSpec,
)
from kubernetes.client.rest import ApiException  # type: ignore
from arkouda.logger import getArkoudaLogger

logger = getArkoudaLogger(name="Arkouda Integration Client")

class InvocationMethod(Enum):
    """
    The InvocationMethod enum provides controlled vocabulary
    for KubernetesDao methods called from scripts
    """
    GET_POD_IPS = 'GET_POD_IPS'
    GET_PODS = 'GET_PODS'

    def __str__(self) -> str:
        """
        Overridden method returns value, which is useful in outputting
        an object to JSON.
        """
        return self.value

    def __repr__(self) -> str:
        """
        Overridden method returns value, which is useful in outputting
        an object to JSON.
        """
        return self.value


class DaoError(Exception):
    """
    The DaoError class wraps tech-specific errors
    """
    pass


class KubernetesDao:
    """
    The KubernetesDao class encapsulates metadata and methods used to retrieve
    objects such as pods and services from Kubernetes.
    """
    __slots__ = ("core_client", "apps_client")

    core_client: client.CoreV1Api
    apps_client: client.AppsV1Api

    def __init__(self, cert_file : str, key_file : str, k8s_host : str):
        config = client.Configuration()

        config.cert_file = cert_file
        config.key_file = key_file
        config.host = k8s_host

        # used to disable non-verified cert warnings
        config.verify_ssl = False

        import urllib3  # type: ignore

        urllib3.disable_warnings()

        try:
            api_client = client.ApiClient(configuration=config)
            self.core_client = client.CoreV1Api(api_client=api_client)
            self.apps_client = client.AppsV1Api(api_client)
        except Exception as e:
            raise DaoError(e)

    def get_pods(self, namespace: str, app_name: Optional[str] = None) -> List[V1Pod]:
        """
        Retrieves a list of V1Pod objects corresponding to pods within a
        namespace. An app name is optionally provided to narrow the scope
        of pods returned.

        :param str namespace: namespace to be queried
        :param Optional[str] app_name: name of app corresponding to the pods
        :return: a list of pods
        :rtype: List[V1Pod]
        :raises: DaoError if there is an error in retrieving pods
        """
        try:
            if namespace:
                pods = self.core_client.list_namespaced_pod(namespace=namespace)
                if app_name:
                    filteredPods = []
                    for pod in pods.items:
                        if self._is_named_pod(pod, app_name):
                            filteredPods.append(pod)
                    return filteredPods
                else:
                    return [pod for pod in pods.items]
            else:
                return [pod in self.core_client.list_pod_for_all_namespaces().items]
        except ApiException as e:
            raise DaoError(e)

    def _is_named_pod(self, pod: V1Pod, app_name: str) -> bool:
        """
        Indicates where the pod has an app name.

        :return: boolean indicating if the pod has an app name
        :rtype: bool
        """
        return pod.metadata.labels.get("app") == app_name

    def get_pod_ips(
        self, namespace: str, app_name: str = None, pretty_print=False) -> Union[List[str], str]:
        """
        Retrieves the overlay network ip addresses for the pods within a
        namespace. An app name is optionally provided to narrow the scope
        of ip addresses returned.

        :param str namespace: namespace to be queried
        :param str app_name: name of the app corresponding to the pods
        :return: a list of ip addresses
        :rtype: Union[List[str],str]
        :raises: DaoError if there is an error in retrieving pods
        """
        try:
            ips = [pod.status.pod_ip for pod in self.get_pods(namespace, app_name)]

            if pretty_print:
                return str(ips).strip("[]").replace(",", "")
            else:
                return ips
        except ApiException as ae:
            raise DaoError(ae)
        except Exception as e:
            raise DaoError(e)

    def create_service(
        self,
        service_name: str,
        app_name: str,
        port: int,
        target_port: int,
        namespace: str = "default",
        protocol: str = "TCP",
    ) -> None:
        """
        Creates the Kubernetes service assigned to the specified application,
        ports, and namespace.

        :param str service_name: name of the service
        :param str app_name: application selector
        :param int port: port assigned to the service
        :param int target_port: target port assigned to the service
        :param str namespace: namespace to assign service, defaults to
               the default Kubernetes namespace
        :param str protocol: service protocol, defaults to TCP
        :return: None
        :raises: DaoError if there is an error in creating the service
        """
        service = V1Service()
        service.kind = "Service"
        service.metadata = V1ObjectMeta(name=service_name)

        spec = V1ServiceSpec()
        spec.selector = {"app": app_name}
        spec.ports = [
            V1ServicePort(protocol=protocol, port=port, target_port=target_port)
        ]
        service.spec = spec

        try:
            self.core_client.create_namespaced_service(
                namespace=namespace, body=service
            )
        except ApiException as ae:
            raise DaoError(ae)
        except Exception as e:
            raise DaoError(e)

    def delete_service(self, service_name: str, namespace: str = "default") -> None:
        """
        Deletes a service within the specified namespace

        :param str service_name: name of the service
        :param str namespace: the k8s namespace, defaults to default namespace
        :return: None
        :raises: DaoError if there is an error in deleting the service
        """
        try:

            self.core_client.delete_namespaced_service(
                name=service_name, namespace=namespace
            )
        except ApiException as e:
            raise DaoError(e)


def main():
    dao = KubernetesDao()

    arg_parser = argparse.ArgumentParser(description="Arkouda Kubernetes client")

    required = arg_parser.add_argument_group("required arguments")
    optional = arg_parser.add_argument_group("optional arguments")

    optional.add_argument(
        "-a", "--app_name", type=str, help="the Kubernetes app name", required=False
    )
    optional.add_argument(
        "-n",
        "--namespace",
        type=str,
        help="the Kubernetes namespace, defaults to default",
        default="default",
        required=False,
    )
    optional.add_argument(
        "-s",
        "--service_name",
        type=str,
        help="the Kubernetes service name, required for CRUD operations",
        required=False,
    )
    optional.add_argument(
        "-pr",
        "--protocol",
        type=str,
        help="the Kubernetes service protocol, defaults to TCP",
        default="TCP",
        required=False,
    )
    optional.add_argument(
        "-p",
        "--port",
        type=int,
        help="the Kubernetes service port, defaults to 5555",
        default=5555,
        required=False,
    )
    optional.add_argument(
        "-tp",
        "--target_port",
        type=int,
        help="the Kubernetes target service port, defaults to 5555",
        default=5555,
        required=False,
    )
    required.add_argument(
        "-i",
        "--invocation_method",
        type=str,
        help="the KubernetesDao method to invoke",
        required=True,
    )

    args = arg_parser.parse_args()

    namespace = args.namespace
    app_name = args.app_name
    service_name = args.service_name
    port = args.port
    target_port = args.target_port
    protocol = args.protocol
    invocation_method = args.invocation_method

    if invocation_method == "get_pod_ips":
        print(
            dao.get_pod_ips(namespace=namespace, app_name=app_name, pretty_print=True)
        )
    elif invocation_method == "create_service":
        dao.create_service(
            service_name=service_name,
            namespace=namespace,
            app_name=app_name,
            port=port,
            target_port=target_port,
            protocol=protocol,
        )
    else:
        logger.error(
            "method {} is not supported from command line".format(invocation_method)
        )


if __name__ == "__main__":
    main()
