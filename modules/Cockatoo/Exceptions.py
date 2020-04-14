"""
Custom Exceptions for Cockatoo.
"""

# COCKATOO BASE EXCEPTION ------------------------------------------------------

class CockatooException(Exception):
    """Base class for exceptions in Cockatoo."""

# DEPENDENCY EXCEPTIONS --------------------------------------------------------

class RhinoNotPresentError(CockatooException):
    """Exception raised when import of Rhino fails."""

class KangarooNotPresentError(CockatooException):
    """Exception raised when import of Kangaroo fails."""

class PlanktonNotPresentError(CockatooException):
    """Exception raised when import of Plankton fails."""

# KNITNETWORK EXCEPTIONS -------------------------------------------------------

class KnitNetworkError(CockatooException):
    """Exception for a serious error in a KnitNetwork of Cockatoo."""

class NetworkXNotPresentError(KnitNetworkError):
    """Exception raised when import of NetworkX fails."""

class NetworkXVersionError(KnitNetworkError):
    """Exception raised when NetworkX version is not 1.5."""

class MappingNetworkError(KnitNetworkError):
    """
    Exception raised by methods relying on a mapping network if no mapping
    network has been assigned to the current KnitNetwork instance yet.
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