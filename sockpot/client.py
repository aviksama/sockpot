from __future__ import unicode_literals
import json
import socket
from socket import error, timeout
import random
import string
from os import error as oserror

from six import string_types

from .conf.auth import AuthFlow
from .conf.exc import ConnectionError, MessageMalformed
from .conf import config

try:
    import ujson as json
except ImportError:
    import json


class Connection(object):

    JSON = 'json'
    BYTES = 'bytes'
    UNICODE = 'unicode'
    STRING = 'string'
    _connections = []

    def __init__(self, host='localhost', port=9900):
        connection = socket.socket()
        try:
            connection.connect((host, port))
            boundary = self._create_boundary()
            auth = AuthFlow(client_socket=connection, boundary=boundary)
            auth.start_client_operation()
            connection.settimeout(config.get('CONNECTION_TIMEOUT', 10))
            self.connection = connection
            self.__class__._connections.append(connection)
            self._boundary = boundary
        except timeout:
            connection.close()
            raise ConnectionError("connection timed out")
        except error:
            connection.close()
            raise ConnectionError("connection refused")

    def _send(self, message=None, encoding=None):
        if isinstance(message, string_types):
            encoding = encoding or 'utf-8'
            try:
                if not isinstance(message, bytes):
                    message = message.encode(encoding)
                self.connection.send(message)
            except oserror:
                self.connection.close()
                raise ConnectionError("broken pipe")
            except (TypeError, LookupError) as e:
                raise ValueError(e.message)
        else:
            raise MessageMalformed("only string object supported")

    def _listen(self):
        dataset = ''
        while self.connection:
            data = self.connection.recv(1024)
            if not data:
                break
            data = data.decode('utf-8')
            if dataset:
                data = dataset + data
            body_parts = data.split(self._boundary)
            if len(body_parts) == 1:
                dataset = body_parts[0]
                continue
            else:
                yieldable = body_parts[:-1]
                if len(yieldable) > 1:
                    return yieldable
                return yieldable[0]

    def send(self, body=None, wait_for_reply=False, timeout_secs=10):
        # todo: json or message support should be taken from configurator
        retval = None
        message = None
        if body and isinstance(body, string_types) and not message:
            message = str(body)
        else:
            raise MessageMalformed("You must specify a supported message body")
        if message:
            existing_timeout = self.connection.gettimeout()
            self.connection.settimeout(timeout_secs)
            head = json.dumps({'reply': wait_for_reply})
            message = head+self._boundary+message+self._boundary
            self._send(message=message)
            if wait_for_reply is True:
                retval = self._listen()
            self.connection.settimeout(existing_timeout)
            return retval

    def close(self):
        self._close()

    def _close(self):
        self.connection.close()

    @staticmethod
    def _create_boundary():
        # max length 96
        charlength = random.randint(11, 18)
        part = lambda: ''.join(random.sample(string.ascii_letters+string.digits+'~!@#$%^&*',
                                             charlength))
        return '---' + part() + '_' * charlength * 3 + part() + '---'
