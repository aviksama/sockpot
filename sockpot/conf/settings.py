from six import string_types

from .utils import import_by_path
from ._settings import config


class BuildSettings(object):

    def __init__(self, filename='settings'):
        if not filename or not isinstance(filename, string_types):
            return
        filename += '.'
        settings_module = import_by_path(filename, module=True, silent=True)
        if not settings_module:
            return
        _vars = {var: getattr(settings_module, var) for var in dir(settings_module) if not
                 var.startswith('_') and var.isupper()}
        config.update(_vars)
