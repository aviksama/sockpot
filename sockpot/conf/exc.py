class ErrorBase(Exception):
    errno = 400

    def __init__(self, message, *args, **kwargs):
        self.message = self.__class__.message + " errno(%s): " % self.errno + str(message)

    def __str__(self):
        return self.message


class ClientError(ErrorBase):
    message = ''


class ConnectionError(ClientError):
    errno = 401
    message = "Couldn't connect to host"


class AuthenticationError(ClientError):
    errno = 403
    message = "Authentication failed"


class MessageMalformed(ClientError):
    errno = 402
    message = "Couldn't read message"


class CredentialError(ErrorBase):
    errno = 300
    message = "Credential malformed"


class ServerError(ErrorBase):
    message = ''


class ClientTerminated(ServerError):
    errno = 411
    message = 'client termination'


class ConfigurationError(ServerError):
    errno = 412
    message = 'invalid callable'
