# PYTHON LIBRARY IMPORTS
from __future__ import division
import math
import operator
from collections import deque

# RHINO IMPORTS
import Rhino

# CUSTOM MODULE IMPORTS
import networkx as nx

# SUBMODULE IMPORTS
from KnitMeshNetworkBase import KnitMeshNetworkBase

class KnitMeshMappingNetwork(KnitMeshNetworkBase):

    """
    Class for representing a mapping network that facilitates the automatic
    generation of knitting patterns based on Rhino geometry.
    This is intended only to be instanced by fully initialized KnitMeshNetwork.
    """

    def ToString(self):
        name = "KnitMeshMappingNetwork"
        nn = len(self.nodes())
        ce = len(self.ContourEdges)
        wee = len(self.WeftEdges)
        wae = len(self.WarpEdges)
        data = ("({} Nodes, {} Segment Contours, {} Weft, {} Warp)")
        data = data.format(nn, ce, wee, wae)
        return name + data
