import pkg_resources
from pkg_resources import DistributionNotFound

try:
    __version__ = pkg_resources.get_distribution('sockpot').version
    __about__ = str(pkg_resources.get_distribution('sockpot').extras)+'\n'
except DistributionNotFound:
    __version__ = __about__ ='package not insalled'
__all__ = ['conf']