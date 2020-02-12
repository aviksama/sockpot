from __future__ import unicode_literals
from gevent import monkey
monkey.patch_all()

import sys
from socket import timeout
from types import GeneratorType
from io import StringIO

from gevent import socket
from gevent.socket import error
from gevent import signal
import gevent

from sockpot.conf.auth import AuthFlow
from sockpot.conf import config
from sockpot.conf.exc import ClientTerminated, ConfigurationError
from json.decoder import JSONDecodeError

try:
    import ujson as json
except ImportError:
    import json


class Server(object):
    _clients = {}
    call_to = None

    def __init__(self, host='0.0.0.0', port=9900, threads=5, call_to=None):
        self.sock_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_obj.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock_obj.bind((host, port))
        self.sock_obj.listen(threads)
        self.__class__.call_to = call_to

    def __call__(self, *args, **kwargs):
        signal.signal(signal.SIGINT, self.signal_handler)
        while True:
            c_socket, c_addr = self.sock_obj.accept()
            auth = AuthFlow(client_socket=c_socket)
            success = auth.start_server_operation()
            if not success:
                try:
                    c_socket.shutdown(socket.SHUT_RDWR)
                    c_socket.close()
                except error:
                    pass
                continue
            c_socket.settimeout(config.get('CONNECTION_TIMEOUT', 60))
            # todo: log the client address
            glet = gevent.spawn(self.listener, c_socket, c_addr, auth.boundary)
            glet.start()
            self._clients.update({c_socket: glet})

    def _exit(self):
        self.sock_obj.close()
        for sock, _ in self._clients.items():
            try:
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()
            except error:
                pass
        sys.exit()
        
    def exit(self):
        self._exit()

    def signal_handler(self, signal, frame):
        self.exit()

    @staticmethod
    def listener(client_socket, client_addr, boundary):
        try:
            if not Server.call_to or not callable(Server.call_to):
                raise ConfigurationError("No callable found for listener")
            try:
                func = Server.call_to.__func__  # staticmethod inside class
            except AttributeError:
                func = Server.call_to  # functions
            # Server.chunked_yield(client_socket, boundary, func)
            buffer = None
            reply = False
            while client_socket:
                chunk_size = 1024
                data = client_socket.recv(chunk_size)
                if not data:
                    Server._clients.pop(client_socket, None)
                    break
                data = data.decode('utf-8')
                try:
                    head, new_data = data.split(boundary, 1)
                    reply = json.loads(head).get('reply', False)
                    data = new_data
                except (ValueError, AttributeError, JSONDecodeError):
                    pass
                if buffer and not buffer.closed:
                    pre_data = buffer.read()
                    buffer.close()
                    body = pre_data + data
                else:
                    body = data
                body_parts = body.split(boundary)
                if len(body_parts) == 1:  # we are not ready to yield
                    buffer = StringIO(body_parts[0])  # tested for python 3.7 only
                    continue
                else:
                    yieldable = body_parts[:-1]
                    for y in yieldable:
                        response_data = func(y)
                        if reply is True:
                            assert (not isinstance(response_data, GeneratorType))
                            response_data = str(response_data)
                            response = response_data + boundary
                            if not isinstance(response, bytes):
                                response = response.encode('utf-8')
                            client_socket.send(response)
                        break
        except timeout:
            sys.stderr.write(str(client_addr) + ': Connection timeout')
        except(ClientTerminated, ConfigurationError):
            sys.stderr.write(str(client_addr) + ': Connection closed')
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
        except error:
            pass
