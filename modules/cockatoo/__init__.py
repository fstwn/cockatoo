"""
cockatoo module API
===================

Submodules
----------

cockatoo.environment module
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: cockatoo.environment
   :members:
   :undoc-members:
   :show-inheritance:

cockatoo.exception module
^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: cockatoo.exception
   :members:
   :undoc-members:
   :show-inheritance:

cockatoo.utilities module
^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: cockatoo.utilities
   :members:
   :undoc-members:
   :show-inheritance:


Classes
-------

.. autosummary::
    :nosignatures:

    cockatoo.KnitConstraint
    cockatoo.KnitNetworkBase
    cockatoo.KnitNetwork
    cockatoo.KnitDiNetwork
    cockatoo.KnitMappingNetwork

cockatoo.KnitConstraint
^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: cockatoo.KnitConstraint
   :members:
   :undoc-members:
   :show-inheritance:

cockatoo.KnitNetworkBase
^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: cockatoo.KnitNetworkBase
   :members:
   :undoc-members:
   :show-inheritance:

cockatoo.KnitNetwork
^^^^^^^^^^^^^^^^^^^^

.. autoclass:: cockatoo.KnitNetwork
   :members:
   :undoc-members:
   :show-inheritance:

cockatoo.KnitDiNetwork
^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: cockatoo.KnitDiNetwork
   :members:
   :undoc-members:
   :show-inheritance:

cockatoo.KnitMappingNetwork
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: cockatoo.KnitMappingNetwork
  :members:
  :undoc-members:
  :show-inheritance:
"""

# PYTHON STANDARD LIBRARY IMPORTS ---------------------------------------------
from __future__ import absolute_import

# LOCAL MODULE IMPORTS --------------------------------------------------------
from cockatoo import environment
from cockatoo import exception
from cockatoo import utilities
from cockatoo._knitconstraint import KnitConstraint
from cockatoo._knitnetworkbase import KnitNetworkBase
from cockatoo._knitnetwork import KnitNetwork
from cockatoo._knitdinetwork import KnitDiNetwork
from cockatoo._knitmappingnetwork import KnitMappingNetwork

# DUNDER ----------------------------------------------------------------------
__author__ = "Max Eschenbach (post@maxeschenbach.com)"
__copyright__ = "Copyright 2020 / Max Eschenbach"
__license__ = "Apache License 2.0"
__email__ = ['<post@maxeschenbach.com>']
__all__ = [
    "environment",
    "exception",
    "KnitConstraint",
    "KnitNetworkBase",
    "KnitNetwork",
    "KnitDiNetwork",
    "KnitMappingNetwork",
    "utilities"
]

# CHECK NETWORKX VERSION ------------------------------------------------------
if environment.NXVERSION != "1.5":
    errmsg = ("Could not verify NetworkX as version 1.5! Please make " +
              "sure NetworkX 1.5 is available to continue.")
    raise exception.NetworkXVersionError(errmsg)

# MAIN ------------------------------------------------------------------------
if __name__ == '__main__':
    pass
