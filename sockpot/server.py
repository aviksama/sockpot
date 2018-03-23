from gevent import monkey
monkey.patch_all()

import sys
from socket import timeout

from gevent import socket
from gevent.socket import error
from gevent import signal
import gevent

from .conf.auth import AuthFlow
from .conf import config
from .conf.exc import ClientTerminated


class Dummy(object):
    @staticmethod
    def writer(data):
        with open('testfile.in', 'a') as fp:
            fp.write("received: " + data + "\n")

class Asa(object):
    def __init__(self):
        self.__class__.func=Dummy.writer
    @staticmethod
    def some_func():
        Asa.func('asdasd in asa')


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
            glet = gevent.spawn(self.listener, c_socket, c_addr)
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
    def listener(client_socket, client_addr):
        try:
            while client_socket:
                data = client_socket.recv(100)
                if not data:
                    Server._clients.pop(client_socket, None)
                    raise ClientTerminated("Connection closed")
                if Server.call_to is not None:
                    Server.call_to.__func__(data)
                continue
        except timeout:
            sys.stderr.write(str(client_addr) + ': Connection timeout')
        except ClientTerminated:
            sys.stderr.write(str(client_addr) + ': Connection closed')
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
        except error:
            pass
