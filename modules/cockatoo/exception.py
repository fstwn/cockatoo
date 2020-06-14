"""
.. currentmodule:: cockatoo.exception

.. autosummary::
    :nosignatures:

    CockatooException
    CockatooImportException
    RhinoNotPresentError
    SystemNotPresentError
    NetworkXNotPresentError
    NetworkXVersionError
    KnitNetworkError
    KnitNetworkGeometryError
    MappingNetworkError
    KnitNetworkTopologyError
    NoWeftEdgesError
    NoWarpEdgesError
    NoEndNodesError
"""

# DUNDER -----------------------------------------------------------------------
__all__ = [
    "CockatooException",
    "CockatooImportException",
    "RhinoNotPresentError",
    "SystemNotPresentError",
    "NetworkXNotPresentError",
    "NetworkXVersionError",
    "KnitNetworkError",
    "KnitNetworkGeometryError",
    "MappingNetworkError",
    "KnitNetworkTopologyError",
    "NoWeftEdgesError",
    "NoWarpEdgesError",
    "NoEndNodesError"
]

# COCKATOO BASE EXCEPTION ------------------------------------------------------

class CockatooException(Exception):
    """Base class for exceptions in Cockatoo."""

class CockatooImportException(ImportError):
    """Base class for import errors in Cockatoo."""

# DEPENDENCY EXCEPTIONS --------------------------------------------------------

class RhinoNotPresentError(CockatooImportException):
    """Exception raised when import of Rhino fails."""

class SystemNotPresentError(CockatooImportException):
    """Exception raised when import of System fails."""

class NetworkXNotPresentError(CockatooImportException):
    """Exception raised when import of NetworkX fails."""

class NetworkXVersionError(CockatooException):
    """Exception raised when NetworkX version is not 1.5."""

# CALLBACK EXCEPTIONS ----------------------------------------------------------

class CockatooCallbackError(CockatooException):
    """Exception raised when a supplied callback is not callable."""

# KNITNETWORK EXCEPTIONS -------------------------------------------------------

class KnitNetworkError(CockatooException):
    """Exception for a serious error in a KnitNetwork of Cockatoo."""

class KnitNetworkGeometryError(KnitNetworkError):
    """Exception raised when vital geometry operations fail."""

class MappingNetworkError(KnitNetworkError):
    """
    Exception raised by methods relying on a mapping network if no mapping
    network has been assigned to the current KnitNetwork instance yet.
    """

class KnitNetworkTopologyError(KnitNetworkError):
    """
    Exception raised by methods which rely on a certain topology of a network if
    that topology could not be verified.
    """

class NoWeftEdgesError(KnitNetworkError):
    """
    Exception raised by methods relying on 'weft' edges if there are no 'weft'
    edges in the network.
    """

class NoWarpEdgesError(KnitNetworkError):
    """
    Exception raised by methods relying on 'warp' edges if there are no 'warp'
    edges in the network.
    """

class NoEndNodesError(KnitNetworkError):
    """
    Exception raised by methods relying on 'end' nodes if there are no 'end'
    nodes in the network.
    """

# MAIN -------------------------------------------------------------------------
if __name__ == '__main__':
    pass
