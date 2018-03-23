import hashlib
from socket import socket
from socket import error, timeout
from datetime import datetime, timedelta

from . import config
from .exc import AuthenticationError


class Credentials(object):
    CLIENT_TYPE = 1
    SERVER_TYPE = 2

    def __init__(self, passkey=None, auth_type=CLIENT_TYPE):
        self.passkey = passkey
        if not passkey:
            assert (auth_type in [self.CLIENT_TYPE, self.SERVER_TYPE])
            if auth_type == self.CLIENT_TYPE:
                self.timeformat = '%d(%a)%m(%B)%Y-%H%M'
            else:
                self.timeformat = '%H%M-%m(%B)%d(%a)%Y'
            self.auth_type = auth_type

    @property
    def digest(self):
        salt = str(config.get('SECRET_KEY'))
        passkey = self.passkey
        if not self.passkey:
            passkey = datetime.utcnow().strftime(self.timeformat)
        digest = hashlib.md5(str(passkey+salt).encode('utf-8')).hexdigest()
        return digest

    def is_valid_digest(self, digest, flexibility=3):
        assert(isinstance(flexibility, int) and flexibility % 2 != 0)
        salt = str(config.get('SECRET_KEY'))
        if not self.passkey:
            hash_range = sorted(list(map(lambda x: x - flexibility/2, range(flexibility))),
                                key=lambda x: abs(x))
            for i in hash_range:
                passkey = (datetime.utcnow()-timedelta(minutes=i)).strftime(self.timeformat)
                new_digest = hashlib.md5(str(passkey + salt).encode('utf-8')).hexdigest()
                if new_digest == digest:
                    return True
        else:
            new_digest = hashlib.md5(str(self.passkey + salt).encode('utf-8')).hexdigest()
            if new_digest == digest:
                return True
        return False


class AuthFlow(object):

    def __init__(self, client_socket=None, auth=None):
        if not client_socket or not isinstance(client_socket, socket):
            raise AuthenticationError("missing client socket")
        if auth and not isinstance(auth, Credentials):
            raise AuthenticationError("invalid credential")
        client_socket.settimeout(config.get('AUTH_TIMEOUT', 5))
        self.socket = client_socket
        self.auth = auth

    def start_client_operation(self):
        if not self.auth:
            self.auth = Credentials(auth_type=Credentials.CLIENT_TYPE)
        digest = self.auth.digest
        try:
            self.socket.send(("CLIENT_AUTH:" + digest).encode('utf-8'))
            data = self.socket.recv(44)
            data = data.decode('utf-8')
            server_token = data.rsplit(':', -1)[1]
            assert(Credentials(auth_type=Credentials.SERVER_TYPE).is_valid_digest(server_token))
        except (error, timeout, IndexError, AssertionError):
            self.socket.close()
            raise AuthenticationError("unable to authenticate the request")

    def start_server_operation(self):
        try:
            data = self.socket.recv(44)
            data.decode('utf-8')
            client_token = data.rsplit(":", -1)[1]
            assert (Credentials(auth_type=Credentials.CLIENT_TYPE).is_valid_digest(client_token))
            if not self.auth:
                self.auth = Credentials(auth_type=Credentials.SERVER_TYPE)
            digest = self.auth.digest
            self.socket.send(("SERVER_AUTH:"+digest).encode('utf-8'))
            return True
        except (error, timeout, IndexError, AssertionError):
            self.socket.send("Invalid Auth")
            self.socket.close()
            return False





