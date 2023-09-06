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

def get_event_loop() -> asyncio.AbstractEventLoop:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop

class AsyncGrpcChannel(Channel):

    def send_string_message(self, cmd: str, recv_binary: bool = False, args: str = None, 
                            size: int = -1) -> Union[str, memoryview]:
        loop = get_event_loop()

        task = loop.create_task(self._send_string_message(cmd, recv_binary, args, size, loop))
        
        loop.run_until_complete(task)
        
        response = task.result()

        logger.debug(f"send_string_message received response {response}")
        return response

    async def _send_string_message(self, cmd, recv_binary, args, size, loop) -> str:
        
        if not loop:
            loop = asyncio.get_event_loop()

        future = loop.run_in_executor(None,
                                      self.async_send_string_message,
                                      cmd,
                                      recv_binary,
                                      args,
                                      size)
            
        while not future.done():
            logger.debug("Awaiting response from Arkouda gRPC ...")
            await asyncio.sleep(5)

        logger.debug("Received future, generating response")
        response = future.result()
        logger.debug(f"Received response from Arkouda gRPC {response}")
            
        return response   

    def _generate_request(self, cmd: str, recv_binary: bool = False, args: str = None, 
                            size: int = -1) -> ArkoudaRequest:
        return ArkoudaRequest(user=self.user,
                              token=self.token,
                              cmd=cmd,
                              format='STRING',
                              size=size,
                              args=args)


    def async_send_string_message(self, cmd: str, recv_binary: bool = False, args: str = None, 
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
            response.message = json.dumps({"msg": f"Arkouda at the address {self.url} is unavailable"})
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

    channel = AsyncGrpcChannel(connect_url=args.arkouda_proxy_url, user=args.user)
    channel.send_string_message(args.cmd, recv_binary=False, args=args.args, size=args.size)
