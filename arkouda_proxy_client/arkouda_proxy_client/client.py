from __future__ import print_function
import argparse
from typing import Union
import json

import asyncio
import grpc
from .arkouda_pb2_grpc import ArkoudaStub
from .arkouda_pb2 import ArkoudaRequest, ArkoudaResponse

from arkouda.client import Channel
from arkouda.logger import getArkoudaLogger, LogLevel

logger = getArkoudaLogger(name="Arkouda Client", logLevel=LogLevel.DEBUG)


class GrpcChannel(Channel):
    """
    The GrpcChannel class is the base gRPC implementation of the Arkouda Channel class. 
    GrpChannel supports blocking gRPC requests to the arkouda-proxy-server

    Attributes
    ----------
    url : str
        Channel url used to connect to the Arkouda server which is either set
        to the connect_url or generated from supplied server and port values
    user : str
        Arkouda user who will use the Channel to connect to the arkouda_server
    token : str, optional
        Token used to connect to the arkouda_server if authentication is enabled
    logger : ArkoudaLogger
        ArkoudaLogger used for logging
    """
    def send_string_message(self, cmd: str, recv_binary: bool = False, args: str = None, 
                            size: int = -1) -> Union[str, memoryview]:
        logger.debug("Sending request to Arkouda gRPC ...")

        response = asyncio.run(self._send_async_request(cmd, recv_binary, args, size))

        logger.debug(f"Arkouda gRPC client received response {response}")
        return response


    def _generate_request(self, cmd: str, recv_binary: bool = False, args: str = None, 
                            size: int = -1) -> ArkoudaRequest:
        return ArkoudaRequest(user=self.user,
                              token=self.token,
                              cmd=cmd,
                              format='STRING',
                              size=size,
                              args=args)


    def _send_request(self, cmd: str, recv_binary: bool = False, args: str = None, 
                            size: int = -1) -> Union[str, memoryview]:

        with grpc.insecure_channel(self.url) as channel:
            raw_response = self.handle_request(channel, 
                                               self._generate_request(cmd,
                                                                      recv_binary,
                                                                      args,
                                                                      size))
        return json.loads(raw_response.message)['msg']     


    async def _send_async_request(self, cmd: str, recv_binary: bool = False, args: str = None, 
                            size: int = -1) -> Union[str, memoryview]:
        async with grpc.aio.insecure_channel(self.url) as channel:
            raw_response = await self.handle_request(channel, 
                                                     self._generate_request(
                                                                            cmd,
                                                                            recv_binary,
                                                                            args,
                                                                            size))
        return json.loads(raw_response.message)['msg']     


    async def handle_request(self, channel, request: ArkoudaRequest):
        try:
            stub = ArkoudaStub(channel)
            raw_response = await stub.HandleRequest(request)
            return raw_response
        except Exception:
            response = ArkoudaResponse()
            response.message = json.dumps({"msg": 
                                        f"Arkouda at address {self.url} is unavailable"})
            return response

    def send_binary_message(self, cmd: str, payload: memoryview, recv_binary: bool=False, 
                            args: str=None, size:int = -1) -> Union[str, memoryview]:
        '''
        TODO: implement send_binary_message
        '''
        pass


    def connect(self, timeout:int=0) -> None:
        '''
        noop implementation
        '''
        pass
    

    def disconnect(self) -> None:
        '''
        noop implementation
        '''
        pass


class AsyncGrpcChannel(GrpcChannel):
    """
    The AsyncGrpcChannel class is a gRPC implementation of Arkouda Channel that
    supports polling asynchronous gRPC requests to the arkouda-proxy-server. 
    Specifically, AsyncGrpcChannel launches a gRPC request asynchronously, invokes
    asyncio.sleep for a configurable amount of time, rechecks the status of the 
    request, continuing this cycle until arkouda_server sends back the response.
    Consequently, it is clear if request is still being processed/waiting to be 
    processed and that the arkouda_server is still running.

    Attributes
    ----------
    url : str
        Channel url used to connect to the Arkouda server which is either set
        to the connect_url or generated from supplied server and port values
    user : str
        Arkouda user who will use the Channel to connect to the arkouda_server
    token : str, optional
        Token used to connect to the arkouda_server if authentication is enabled
    logger : ArkoudaLogger
        ArkoudaLogger used for logging
    """
    def send_string_message(self, cmd: str, recv_binary: bool = False, args: str = None, 
                            size: int = -1) -> Union[str, memoryview]:
        loop = asyncio.get_event_loop()

        task = loop.create_task(self._send_string_message(cmd, recv_binary, args, size, loop))
        
        loop.run_until_complete(task)
        
        response = task.result()

        logger.debug(f"send_string_message received response {response}")
        return response


    async def _send_string_message(self, cmd, recv_binary, args, size, loop) -> str:
        
        if not loop:
            loop = asyncio.get_event_loop()

        future = loop.run_in_executor(None,
                                      self._send_request,
                                      cmd,
                                      recv_binary,
                                      args,
                                      size)
            
        while not future.done():
            logger.info("Awaiting response from Arkouda...")
            await asyncio.sleep(5)

        response = future.result()
        return response   

    def _generate_request(self, cmd: str, recv_binary: bool = False, args: str = None, 
                            size: int = -1) -> ArkoudaRequest:
        return ArkoudaRequest(user=self.user,
                              token=self.token,
                              cmd=cmd,
                              format='STRING',
                              size=size,
                              args=args)


    def _send_request(self, cmd: str, recv_binary: bool = False, args: str = None, 
                            size: int = -1) -> Union[str, memoryview]:

        with grpc.insecure_channel(self.url) as channel:
            raw_response = self.handle_request(channel, self._generate_request(cmd,
                                                                          recv_binary,
                                                                          args,
                                                                          size))
        return json.loads(raw_response.message)['msg']     


    def handle_request(self, channel, request: ArkoudaRequest):
        try:
            stub = ArkoudaStub(channel)
            raw_response = stub.HandleRequest(request)
            return raw_response
        except Exception:
            response = ArkoudaResponse()
            response.message = json.dumps({"msg": f"Arkouda address {self.url} is unavailable"})
            return response


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

    channel = GrpcChannel(connect_url=args.arkouda_proxy_url, user=args.user)
    channel.send_string_message(args.cmd, recv_binary=False, args=args.args, size=args.size)
