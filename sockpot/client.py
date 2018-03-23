import json
import socket
from socket import error, timeout

from os import error as oserror
from six import string_types
from sockpot.conf import AuthFlow
from sockpot.conf import ConnectionError, MessageMalformed
from sockpot.conf import config


class Connection(object):

    JSON = 'json'
    BYTES = 'bytes'
    UNICODE = 'unicode'
    STRING = 'string'
    _connections = []

    def __init__(self, host='localhost', port=9900,):
        connection = socket.socket()
        try:
            connection.connect((host, port))
            auth = AuthFlow(client_socket=connection)
            auth.start_client_operation()
            connection.settimeout(config.get('CONNECTION_TIMEOUT', 10))
            self.connection = connection
            self.__class__._connections.append(connection)
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

    def send(self, body=None, json_body=None):
        # todo: json or message support should be taken from configurator
        message = None
        if json_body and isinstance(json_body, dict):
            message = json.dumps(json_body)
        elif body and isinstance(body, string_types) and not message:
            message = str(body)
        else:
            raise MessageMalformed("You must specify a supported message body")
        if message:
            self._send(message=message)

    def close(self):
        self._close()

    def _close(self):
        self.connection.close()

