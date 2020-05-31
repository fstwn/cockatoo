"""
Cockatoo module for automatic generation of knitting patterns based on
mesh or NURBS surface reference geometry.

Author: Max Eschenbach
License: Apache License 2.0
Version: 200530
"""

# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from Cockatoo import Environment
from Cockatoo import Exceptions
from Cockatoo.KnitConstraint import KnitConstraint
from Cockatoo.KnitNetworkBase import KnitNetworkBase
from Cockatoo.KnitNetwork import KnitNetwork
from Cockatoo.KnitDiNetwork import KnitDiNetwork
from Cockatoo.KnitMappingNetwork import KnitMappingNetwork

# AUTHORSHIP -------------------------------------------------------------------

__author__ = """Max Eschenbach (post@maxeschenbach.com)"""

# ALL LIST ---------------------------------------------------------------------
__all__ = [
    "Environment",
    "Exceptions",
    "KnitNetworkBase",
    "KnitNetwork",
    "KnitDiNetwork",
    "KnitMappingNetwork",
]

# MAIN -------------------------------------------------------------------------
if __name__ == '__main__':
    pass
