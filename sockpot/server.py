from gevent import monkey
monkey.patch_all()

import sys
import json
from socket import timeout
from types import GeneratorType
from io import BytesIO

from gevent import socket
from gevent.socket import error
from gevent import signal
import gevent
import six

from .conf.auth import AuthFlow
from .conf import config
from .conf.exc import ClientTerminated, ConfigurationError


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
            initial = True
            dataset = BytesIO()
            if not Server.call_to or not callable(Server.call_to):
                raise ConfigurationError("No callable found for listener")
            while client_socket:
                data = client_socket.recv(1024)
                if not data:
                    Server._clients.pop(client_socket, None)
                    raise ClientTerminated("Connection closed")
                if initial is False:
                    body = data
                else:
                    try:
                        head, body = data.split(boundary, 1)
                        reply = json.loads(head).get('reply')
                    except (ValueError, AttributeError):
                        raise ClientTerminated("Malformed buffer")
                    initial = False
                body_parts = body.rsplit(boundary, 1)
                body = body_parts[0]
                if six.PY3 and not isinstance(body, bytes):
                    body = bytes(body, encoding='utf-8')
                dataset.write(body)
                if len(body_parts) == 1:
                    loopexit = False
                else:
                    loopexit = True

                if loopexit:
                    try:
                        func = Server.call_to.__func__  # staticmethod inside class
                    except AttributeError:
                        func = Server.call_to  # functions
                    dataset.seek(0)
                    response_data = func(dataset.read())
                    dataset = BytesIO()
                    initial = True
                    if reply is True:
                        # todo: support for  GeneratorType for stream of data
                        assert (not isinstance(response_data, GeneratorType))
                        response_data = str(response_data)
                        response = response_data + boundary + 'end'
                        if not isinstance(response, bytes):
                            response.encode('utf-8')
                        client_socket.send(response)

        except timeout:
            sys.stderr.write(str(client_addr) + ': Connection timeout')
        except(ClientTerminated, ConfigurationError):
            sys.stderr.write(str(client_addr) + ': Connection closed')
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
        except error:
            pass
