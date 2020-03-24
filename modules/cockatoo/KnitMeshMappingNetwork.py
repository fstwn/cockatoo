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
    This is intended only to be instanced by a fully segmented instance of
    KnitMeshNetwork.
    """

    def ToString(self):
        """
        Return a textual description of the network.
        """

        name = "KnitMeshMappingNetwork"
        nn = len(self.nodes())
        ce = len(self.ContourEdges)
        wee = len(self.WeftEdges)
        wae = len(self.WarpEdges)
        data = ("({} Nodes, {} Segment Contours, {} Weft, {} Warp)")
        data = data.format(nn, ce, wee, wae)
        return name + data

    # SEGMENT CONTOUR EDGES PROPERTIES -----------------------------------------

    def _get_segment_contour_edges(self):
        """
        Get all contour edges of the network marked neither 'warp' nor 'weft'
        that have a 'segment' attribute assigned sorted by the 'segment'
        attribute.
        """

        # get all the edges
        SegmentContourEdges = [(f, t, d) for f, t, d in self.edges_iter(data=True) \
                        if d["weft"] == False and \
                           d["warp"] == False and \
                           d["segment"] != None]

        # sort them by their 'segment' attributes value
        SegmentContourEdges.sort(key=lambda x: x[2]["segment"])

        return SegmentContourEdges

    SegmentContourEdges = property(_get_segment_contour_edges, None, None,
                         "The edges of the network marked neither 'warp' "+
                         "nor 'weft' and which have a 'segment' attribute "+
                         "assigned to them.")
