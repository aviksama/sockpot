import importlib


def import_by_path(path, module=False, silent=False):
    """
    :param path: Full non-relative path of the object in dotted form 
    :param silent: setting this to `True` will not throw any import error
    :param module: setting this to `True` will return the module instead of class
    :return: returns imported object
    """
    try:
        modulename, classname = path.rsplit('.', 1)
    except ValueError as e:
            if not silent:
                e.message = "%s doesn't look like a module path" % path
                raise e
            return
    else:
        try:
            mod = importlib.import_module(modulename)
        except ImportError as e:
            if not silent:
                raise e
            mod = None
        if module:
            return mod
        klass = None
        if hasattr(mod, classname):
            klass = getattr(mod, classname)
        return klass



