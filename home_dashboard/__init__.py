"""Home Dashboard API App"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("home-dashboard")
except PackageNotFoundError:
    __version__ = "dev"
