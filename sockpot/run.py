import sys
import re
import os
from .server import Server, Dummy
from .conf.utils import import_by_path


def find_calee(*sysargs):
    args = ' '.join(sysargs)
    path_matcher = re.compile('--path\s*=\s*([a-zA-z0-9_\-./]+)')
    posix_path = path_matcher.search(args)
    if posix_path:
        posix_path = posix_path.groups()[0]
        os.environ['PYTHONPATH'] = posix_path + ':' + os.environ.get('PYTHONPATH', '').strip(':')
    module_matcher = re.compile('--callee\s*=\s*([a-zA-z0-9_\-.]+)')
    module_path = module_matcher.search(args)
    if not module_path:
        call_to = Dummy.writer
    else:
        module_path = module_path.groups()[0]
        try:
            call_to = import_by_path(module_path)
            if not call_to or not callable(call_to):
                raise ValueError
        except (ImportError, ValueError):
            raise ValueError("Invalid callable")
    return call_to


def find_serve_args(*sysargs):
    args = ' '.join(sysargs)
    # finding host
    host_matcher = re.compile('--host\s*=\s*([a-zA-z0-9_\-./]+)')
    host = host_matcher.search(args)
    host = host.groups()[0] if host else '0.0.0.0'

    # finding port
    port_matcher = re.compile('--port\s*=\s*([a-zA-z0-9_\-./]+)')
    port = port_matcher.search(args)
    port = int(port.groups()[0]) if port else 9900

    # finding number of threads
    thread_matcher = re.compile('--threads\s*=\s*([a-zA-z0-9_\-./]+)')
    threads = thread_matcher.search(args)
    threads = int(threads.groups()[0]) if threads else 5
    return host, port, threads


def serve():
    args = sys.argv[1:]
    call_to = find_calee(*args)
    host, port, threads = find_serve_args(*args)
    connection = Server(host=host, port=port, threads=threads, call_to=call_to)
    print('Press Ctrl+C to quit')
    connection()
