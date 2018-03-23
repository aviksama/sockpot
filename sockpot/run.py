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
    module_matcher = re.compile('--call_to\s*=\s*([a-zA-z0-9_\-.]+)')
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


def serve():
    args = sys.argv[1:]
    call_to = find_calee(*args)
    connection = Server(call_to=call_to)
    print('Press Ctrl+C to quit')
    connection()


if __name__ == '__main__':
    args = sys.argv[1:]
    call_to = find_calee(*args)
    connection = Server(call_to=call_to)
    print('Press Ctrl+C to quit')
    connection()
