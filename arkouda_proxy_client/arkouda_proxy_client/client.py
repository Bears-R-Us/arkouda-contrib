from __future__ import print_function
import argparse
from typing import Union
import json

import asyncio
import grpc
import arkouda_pb2_grpc
from arkouda_pb2 import ArkoudaRequest, ArkoudaResponse

from arkouda.client import Channel
from arkouda.logger import getArkoudaLogger, LogLevel

logger = getArkoudaLogger(name="Arkouda Client", logLevel=LogLevel.DEBUG)

class GrpcChannel(Channel):
    
    def send_string_message(self, cmd: str, recv_binary: bool = False, args: str = None, 
                            size: int = -1) -> Union[str, memoryview]:
        logger.debug("Sending request to Arkouda gRPC ...")

        response = asyncio.run(self.async_send_string_message(cmd, recv_binary, args, size))

        logger.debug(f"Arkouda gRPC client received response {response}")
        return response


    def _get_request(self, cmd: str, recv_binary: bool = False, args: str = None, 
                            size: int = -1) -> ArkoudaRequest:
        return ArkoudaRequest(user=self.user,
                              token=self.token,
                              cmd=cmd,
                              format='STRING',
                              size=size,
                              args=args)


    async def async_send_string_message(self, cmd: str, recv_binary: bool = False, args: str = None, 
                            size: int = -1) -> Union[str, memoryview]:
        async with grpc.aio.insecure_channel(self.url) as channel:
            raw_response = await self.handle_request(channel, self._get_request(
                                                                        cmd,
                                                                        recv_binary,
                                                                        args,
                                                                        size))
        return json.loads(raw_response.message)['msg']     


    async def handle_request(self, channel, request: ArkoudaRequest):
        try:
            stub = arkouda_pb2_grpc.ArkoudaStub(channel)
            raw_response = await stub.HandleRequest(request)
            return raw_response
        except Exception:
            response = ArkoudaResponse()
            response.message = '{"msg": "Arkouda is unavailable"}'
            return response

    def send_binary_message(self, cmd: str, payload: memoryview, recv_binary: bool=False, 
                            args: str=None, size:int = -1) -> Union[str, memoryview]:
        pass
    
    def connect(self, timeout:int=0) -> None:
        pass
    
    def disconnect(self) -> None:
        pass


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

    channel = GrpcChannel(server='localhost', port=5555, connect_url=args.arkouda_proxy_url, user=args.user)
    channel.send_string_message(args.cmd, recv_binary=False, args=args.args, size=args.size)
