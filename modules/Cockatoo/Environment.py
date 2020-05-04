"""
Environment set-up functions and checks for Cockatoo.

Author: Max Eschenbach
License: Apache License 2.0
Version: 200503
"""

# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import print_function

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from . import Exceptions

# CHECKING FOR RHINO DEPENDENCY AND ENVIRONMENT --------------------------------
try:
    import Rhino
    ISRHINOINSIDE = False
except ImportError:
    try:
        import rhinoinside
        rhinoinside.load()
        import Rhino
        ISRHINOINSIDE = True
    except:
        raise Exceptions.RhinoNotPresentError()

def IsRhinoInside():
    """
    Check if Rhino is running using rhinoinside.
    """
    return ISRHINOINSIDE == True

# CHECKING FOR NETWORKX DEPENDENCY AND VERSION ---------------------------------
try:
    import networkx
    NXVERSION = networkx.__version__
    if not NXVERSION == "1.5":
        raise Exceptions.NetworkXVersionError()
except ImportError:
    raise Exceptions.NetworkXNotPresentError()

def NetworkXVersion():
    """
    Return the version of the used networkx module.
    """
    return NXVERSION

# AUTHORSHIP -------------------------------------------------------------------

__author__ = """Max Eschenbach (post@maxeschenbach.com)"""

# ALL DICTIONARY ---------------------------------------------------------------
__all__ = [
    "IsRhinoInside",
    "NetworkXVersion"
]

# MAIN -------------------------------------------------------------------------
if __name__ == '__main__':
    pass
