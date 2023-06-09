from __future__ import print_function
import argparse
import logging

import grpc
import arkouda_pb2
import arkouda_pb2_grpc

#$'localhost:50053
def run(url: str, user: str, token: str, cmd: str, format: str, size: int, args: str):
    print("Sending request to Arkouda gRPC ...")
    with grpc.insecure_channel(url) as channel:
        stub = arkouda_pb2_grpc.ArkoudaStub(channel)
        response = stub.HandleRequest(arkouda_pb2.ArkoudaRequest(user=user,
                                                                 token=token,
                                                                 cmd=cmd,
                                                                 format=format,
                                                                 size=size,
                                                                 args=args))
    print(f"Arkouda gRPC client received response {response}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test arkouda_proxy_server')

    parser.add_argument('--arkouda_proxy_url', type=str, required=True,
                        help='the arkouda_proxy_server url in the host:port format')
    parser.add_argument('--user', type=str, required=True,
                        help='the arkouda user')
    parser.add_argument('--token', type=str,
                        help='token if token authentication is enabled')
    parser.add_argument('--cmd', type=str, default='connect', required=True,
                        help='the arkouda command request, defaults to connect')
    parser.add_argument('--format', type=str, default='STRING',
                        help='the arkouda request format, defaults to STRING')
    parser.add_argument('--size', type=str, default=-1,
                        help='number of args, defaults to -1')
    parser.add_argument('--args', type=str,
                        help='space-delimited list of args for the cmd')

    args = parser.parse_args()
    run(url=args.arkouda_proxy_url, 
        user=args.user,
        token=args.token,
        cmd=args.cmd,
        format=args.format,
        size=args.size,
        args=args.args)                                                                                                                                                                                

