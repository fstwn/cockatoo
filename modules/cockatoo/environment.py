"""
Environment set-up functions and checks for Cockatoo.

Author: Max Eschenbach
License: Apache License 2.0
Version: 200603
"""

# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import print_function

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from cockatoo.exception import *

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
        errMsg = "Rhino could not be loaded! Please make sure the " + \
                 "RhinoCommon API is available to continue."
        raise RhinoNotPresentError(errMsg)

def is_rhino_inside():
    """
    Check if Rhino is running using rhinoinside.
    """
    return ISRHINOINSIDE == True

# CHECKING FOR NETWORKX DEPENDENCY AND VERSION ---------------------------------
try:
    import networkx
    NXVERSION = networkx.__version__
    if not NXVERSION == "1.5":
        errMsg = "Could not verify NetworkX as version 1.5! Please make " + \
                 "sure NetworkX 1.5 is available to continue."
        raise NetworkXVersionError(errMsg)
except ImportError:
    errMsg = "Could not load NetworkX. Please make sure the networkx " + \
             "module is available to continue."
    raise NetworkXNotPresentError(errMsg)

def networkx_version():
    """
    Return the version of the used networkx module.
    """
    return NXVERSION

# AUTHORSHIP -------------------------------------------------------------------

__author__ = """Max Eschenbach (post@maxeschenbach.com)"""

# ALL LIST ---------------------------------------------------------------------
__all__ = [
    "is_rhino_inside",
    "networkx_version"
]

# MAIN -------------------------------------------------------------------------
if __name__ == '__main__':
    pass
