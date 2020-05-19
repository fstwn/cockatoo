"""
Base class for graph representation of knitting data.

Author: Max Eschenbach
License: Apache License 2.0
Version: 200503
"""

# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from collections import OrderedDict

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from Cockatoo.Environment import IsRhinoInside
from Cockatoo.Exceptions import *

# RHINO IMPORTS ----------------------------------------------------------------
if IsRhinoInside():
    import rhinoinside
    rhinoinside.load()
    from Rhino.Geometry import Curve as RhinoCurve
    from Rhino.Geometry import Line as RhinoLine
    from Rhino.Geometry import LineCurve as RhinoLineCurve
    from Rhino.Geometry import Polyline as RhinoPolyline
else:
    from Rhino.Geometry import Curve as RhinoCurve
    from Rhino.Geometry import Line as RhinoLine
    from Rhino.Geometry import LineCurve as RhinoLineCurve
    from Rhino.Geometry import Polyline as RhinoPolyline

# THIRD PARTY MODULE IMPORTS ---------------------------------------------------
import networkx as nx

# AUTHORSHIP -------------------------------------------------------------------

__author__ = """Max Eschenbach (post@maxeschenbach.com)"""

# ALL LIST ---------------------------------------------------------------------
__all__ = [
    "KnitNetworkBase"
]

# ACTUAL CLASS -----------------------------------------------------------------
class KnitNetworkBase(nx.Graph):
    """
    Base class for representing a network that facilitates the automatic
    generation of knitting patterns based on Rhino geometry.
    """

    # REPRESENTATION OF NETWORK ------------------------------------------------

    def __str__(self):
        """
        Return the graph name if it is set, otherwise return a textual
        description of the network.

        Returns
        -------
        name : str
            The name of the graph or a textual description of the network.
        """
        if self.name != '':
            return self.name
        else:
            return self.ToString()

    def ToString(self):
        """
        Return a textual description of the network.

        Returns
        -------
        stringrep : str
            String describing the contents of the network.
        """

        name = "KnitNetworkBase"
        nn = len(self.nodes())
        ce = len(self.ContourEdges)
        wee = len(self.WeftEdges)
        wae = len(self.WarpEdges)
        data = ("({} Nodes, {} Contours, {} Weft, {} Warp)")
        data = data.format(nn, ce, wee, wae)
        return name + data

    def MakeRenderGraph(self, allcircles=False):
        """
        Creates a new graph with attributes for visualising this networkx
        using GraphViz.

        Based on code by Anders Holden Deleuran
        """

        # Set render variables
        nodeFontSize = 10
        edgeFontSize = 3.75
        arrowSize = 0.4

        # colors
        black = "black"
        white = "white"
        grey = "grey"
        blue = "blue"
        red = "red"
        green = "green"
        orange = "orange"

        # node shapes
        circle = "circle"
        trapez = "trapezium"
        triangle = "triangle"
        invtriangle = "invtriangle"
        square = "square"
        parallelogram = "parallelogram"
        diamond = "diamond"

        font = "Lato"

        if isinstance(self, nx.MultiGraph):
            RenderGraph = nx.MultiDiGraph()
        else:
            RenderGraph = nx.DiGraph()

        kmn_nodes = self.nodes(data=True)
        kmn_edges = self.edges(data=True)

        # add all nodes to the render graph
        for node in kmn_nodes:
            if node[1]["end"] and not node[1]["leaf"]:
                nType = "E"
                nCol = red
                nFCol = black
                if allcircles:
                    nodeShape = circle
                else:
                    nodeShape = triangle
            elif node[1]["leaf"] and not node[1]["end"]:
                nType = "L"
                nCol = green
                nFCol = black
                if allcircles:
                    nodeShape = circle
                else:
                    nodeShape = invtriangle
            elif node[1]["leaf"] and node[1]["end"]:
                nType = "EL"
                nCol = orange
                nFCol = black
                if allcircles:
                    nodeShape = circle
                else:
                    nodeShape = diamond
            else:
                nType = ""
                nCol = black
                nFCol = white
                if allcircles:
                    nodeShape = circle
                else:
                    nodeShape = square

            if node[1]["segment"]:
                nLabel = str(node[0]) + nType + "\n" + str(node[1]["segment"])
            else:
                nLabel = str(node[0]) + nType

            RenderGraph.add_node(node[0],
                                 label=nLabel,
                                 shape=nodeShape,
                                 fontname=font,
                                 style="filled",
                                 fillcolor=nCol,
                                 fontcolor=nFCol,
                                 fontsize=nodeFontSize,
                                 margin=0.0001)

        # ad all edges to the render graph
        for edge in kmn_edges:
            padding = "  "
            if edge[2]["weft"]:
                eType = "WFT"
                eCol = blue
            elif edge[2]["warp"]:
                eType = "WRP"
                eCol = red
            elif not edge[2]["weft"] and not edge[2]["warp"]:
                eType = "C"
                eCol = black

            eInfo = str(edge[0]) + ">" + str(edge[1])
            eLabel = eInfo + eType + "\n" + str(edge[2]["segment"])

            RenderGraph.add_edge(edge[0], edge[1],
                                 label=eLabel,
                                 fontname=font,
                                 fontcolor=black,
                                 color=eCol,
                                 fontsize=edgeFontSize,
                                 arrowsize=arrowSize)

        return RenderGraph

    def MakeGephiGraph(self):
        """
        Creates a new graph with attributes for visualising this networkx
        using Gephi.

        Based on code by Anders Holden Deleuran
        """

        # colors
        black = "black"
        white = "white"
        blue = "blue"
        red = "red"
        green = "green"
        orange = "orange"

        # node shapes
        circle = "circle"

        if isinstance(self, nx.MultiGraph):
            GephiGraph = nx.MultiDiGraph()
        else:
            GephiGraph = nx.DiGraph()

        kmn_nodes = self.nodes(data=True)
        kmn_edges = self.edges(data=True)

        # add all nodes to the render graph
        for node in kmn_nodes:
            if node[1]["end"] and not node[1]["leaf"]:
                nType = "end"
                nCol = red
                nodeShape = circle

            elif node[1]["leaf"] and not node[1]["end"]:
                nType = "leaf"
                nCol = green
                nodeShape = circle

            elif node[1]["leaf"] and node[1]["end"]:
                nType = "end leaf"
                nCol = orange
                nodeShape = circle

            else:
                nType = "regular"
                nCol = black
                nodeShape = circle

            nodeAttrs = {"color": nCol,
                         "shape": nodeShape,
                         "type": nType}

            GephiGraph.add_node(node[0], attr_dict=nodeAttrs)

        # ad all edges to the render graph
        for edge in kmn_edges:
            if edge[2]["weft"]:
                eType = "weft"
                eWeight = 1
                eCol = blue
            elif edge[2]["warp"]:
                eType = "warp"
                eWeight = 10
                eCol = red
            elif not edge[2]["weft"] and not edge[2]["warp"]:
                continue

            edgeAttrs = {"weight": eWeight,
                         "color": eCol,
                         "type": eType}

            GephiGraph.add_edge(edge[0], edge[1], attr_dict=edgeAttrs)

        return GephiGraph

    # NODE CREATION ------------------------------------------------------------

    def NodeFromPoint3d(self, node_index, pt, position=None, num=None, leaf=False, end=False, segment=None, increase=False, decrease=False):
        """
        Creates a network node from a Rhino Point3d and attributes.

        Parameters
        ----------
        node_index : int
            The index of the node in the network. Usually an integer is used.

        pt : :class:`Rhino.Geometry.Point3d`
            A RhinoCommon Point3d object.

        position : int
            The 'position' attribute of the node identifying the underlying
            contour edge of the network.
            Defaults to None.

        num : int
            The 'num' attribute of the node representing its index in the
            underlying contour edge of the network.
            Defaults to None.

        leaf : bool
            The 'leaf' attribute of the node identifying it as a node on the
            first or last course of the knitting pattern.
            Defaults to False.

        end : bool
            The 'end' attribute of the node identifying it as the start or end
            of a segment.
            Defaults to False.

        segment : :obj:`tuple` of :obj:`int`
            The 'segment' attribute of the node identifying its position between
            two 'end' nodes.
            Defaults to None.

        crease : bool
            The 'crease' attribute identifying the node as an increase or
            decrease (needed for translation from dual to 2d knitting pattern).
            Defaults to False.
        """

        # extract node coordinates
        nodeX = pt.X
        nodeY = pt.Y
        nodeZ = pt.Z

        # compile node attributes
        node_attributes = {"x": nodeX,
                           "y": nodeY,
                           "z": nodeZ,
                           "position": position,
                           "num": num,
                           "leaf": leaf,
                           "end": end,
                           "segment": segment,
                           "increase": increase,
                           "decrease": decrease,
                           "geo": pt}

        # add the node to the network instance
        self.add_node(node_index, attr_dict=node_attributes)

    # NODE GEOMETRY ------------------------------------------------------------

    def NodeGeometry(self, node_index):
        """
        Returns the 'geo' attribute of the specified node.
        """
        try:
            return self.node[node_index]["geo"]
        except KeyError:
            return None

    def NodeCoordinates(self, node_index):
        """
        Returns the XYZ coordinates of the node as a tuple.
        """
        try:
            node_data = self.node[node_index]
            NodeX = node_data["x"]
            NodeY = node_data["y"]
            NodeZ = node_data["z"]
            return (NodeX, NodeY, NodeZ)
        except KeyError:
            return None

    # PROPERTIES ---------------------------------------------------------------

    def _get_total_positions(self):
        """
        Gets the number of total positions (i.e. contours) inside the network.
        """

        total = max([d["position"] for n, d in self.nodes_iter(data=True)])+1
        return total

    TotalPositions = property(_get_total_positions, None, None,
                              "The total number of positions (i.e. contours) " +
                              "inside the network")

    # NODES ON POSITION CONTOURS -----------------------------------------------

    def NodesOnPosition(self, pos, data=False):
        """
        Returns the nodes on a given position (i.e. contour).

        Parameters
        ----------
        pos : int
            The index of the position

        data : bool
            If True, found nodes will be returned with their attribute data.
            Defaults to False.
        """

        nodes = [(n, d) for n, d in self.nodes_iter(data=True) \
                 if d["position"] == pos]

        nodes.sort(key=lambda x: x[1]["num"])

        if not data:
            nodes = [n[0] for n in nodes]

        return nodes

    def AllNodesByPosition(self, data=False):
        """
        Returns all the nodes of the network ordered by position.
        """

        allPositionNodes = sorted(
                            [(n, d) for n, d in self.nodes_iter(data=True) \
                            if d["position"] != None],
                            key=lambda x: x[1]["position"])

        posdict = OrderedDict()
        for n in allPositionNodes:
            if n[1]["position"] not in posdict:
                posdict[n[1]["position"]] = [n]
            else:
                posdict[n[1]["position"]].append(n)

        anbp = []
        for key in posdict:
            posnodes = sorted(posdict[key], key=lambda x: x[1]["num"])
            if data:
                anbp.append(posnodes)
            else:
                anbp.append([pn[0] for pn in posnodes])

        return anbp

    # NODES ON SEGMENT CONTOURS ------------------------------------------------

    def NodesOnSegment(self, segment, data=False):
        """
        Returns all nodes on a given segment ordered by 'num' attribute.
        """

        nodes = [(n, d) for n, d in self.nodes_iter(data=True) \
                 if d["segment"] == segment]

        nodes.sort(key=lambda x: x[1]["num"])

        if data:
            return nodes
        else:
            return [n[0] for n in nodes]

    # LEAF NODES ---------------------------------------------------------------

    def _get_leaf_nodes(self):
        """
        Gets all 'leaf' nodes of the network.
        """

        leaves = [(n, d) for n, d in self.nodes_iter(data=True) \
                  if d["leaf"] == True]

        return leaves

    LeafNodes = property(_get_leaf_nodes, None, None,
                         "All 'leaf' nodes of the network.")

    def LeavesOnPosition(self, pos, data=False):
        """
        Gets all 'leaf' vertices on a given position.
        """

        leaves = [(n, d) for n, d in self.NodesOnPosition(pos, data=True) \
                  if d["leaf"]]
        if not data:
            leaves = [n[0] for n in leaves]
        return leaves

    def AllLeavesByPosition(self, data=False):
        """
        Gets all 'leaf' nodes ordered by 'position' attribute.
        """

        allPositionLeaves = sorted(
                            [(n, d) for n, d in self.nodes_iter(data=True) \
                            if d["position"] != None and d["leaf"]],
                            key=lambda x: x[1]["position"])

        posdict = OrderedDict()
        for n in allPositionLeaves:
            if n[1]["position"] not in posdict:
                posdict[n[1]["position"]] = [n]
            else:
                posdict[n[1]["position"]].append(n)

        albp = []
        for key in posdict:
            posleaves = sorted(posdict[key], key=lambda x: x[1]["num"])
            if data:
                albp.append(posleaves)
            else:
                albp.append([pl[0] for pl in posleaves])

        return albp

    # END NODES ----------------------------------------------------------------

    def _get_end_nodes(self):
        """
        Gets all 'end' nodes of the network.
        """

        ends = [(n, d) for n, d in self.nodes_iter(data=True) \
                if d["end"]]

        return ends

    EndNodes = property(_get_end_nodes, None, None,
                        "All 'end' nodes of the network")

    def EndsOnPosition(self, pos, data=False):
        """
        Gets 'end' nodes on a given position.
        """

        ends = [(n, d) for n, d in self.NodesOnPosition(pos, data=True) \
                if d["end"]]
        if not data:
            return [n[0] for n in ends]
        return ends

    def AllEndsByPosition(self, data=False):
        """
        Gets all 'end' vertices on all positions ordered by position.
        """

        allPositionEnds = sorted(
                            [(n, d) for n, d in self.nodes_iter(data=True) \
                            if d["position"] != None and d["end"]],
                            key=lambda x: x[1]["position"])

        posdict = OrderedDict()
        for n in allPositionEnds:
            if n[1]["position"] not in posdict:
                posdict[n[1]["position"]] = [n]
            else:
                posdict[n[1]["position"]].append(n)

        aebp = []
        for key in posdict:
            posends = sorted(posdict[key], key=lambda x: x[1]["num"])
            if data:
                aebp.append(posends)
            else:
                aebp.append([pe[0] for pe in posends])

        return aebp

    # POSITION CONTOUR METHODS -------------------------------------------------

    def GeometryAtPositionContour(self, pos, as_crv=False):
        """
        Gets the contour polyline at a given position.
        """

        points = [d["geo"] for n, d in self.NodesOnPosition(pos, True)]
        Contour = RhinoPolyline(points)
        if as_crv:
            Contour = Contour.ToPolylineCurve()
        return Contour

    def LongestPositionContour(self):
        """
        Gets the longest contour position, geometry and length
        """

        longestLength = 0
        longestContour = None
        longestPosition = None
        for i in range(self.TotalPositions):
            contour = self.GeometryAtPositionContour(i, True)
            cl = contour.GetLength()
            if cl > longestLength:
                longestLength = cl
                longestContour = contour.Duplicate()
                longestPosition = i
            contour.Dispose()
        return (longestPosition, longestContour, longestLength)

    # EDGE CREATION METHODS ----------------------------------------------------

    def CreateContourEdge(self, From, To):
        """
        Creates an edge neither 'warp' nor 'weft' between two nodes in the
        network, returns True if the edge has been successfully created.
        """

        # get node indices
        fromNode = From[0]
        toNode = To[0]

        # get geometry from nodes
        fromGeo = From[1]["geo"]
        toGeo = To[1]["geo"]

        # create edge geometry
        edgeGeo = RhinoLine(fromGeo, toGeo)

        # create edge attribute
        edgeAttrs = {"warp": False,
                     "weft": False,
                     "segment": None,
                     "geo": edgeGeo}

        self.add_edge(fromNode, toNode, attr_dict=edgeAttrs)

        return True

    def CreateWeftEdge(self, From, To, segment=None):
        """
        Creates a 'weft' edge between two nodes in the network, returns True if
        the edge has been successfully created.
        """

        # get node indices
        fromNode = From[0]
        toNode = To[0]

        # get geometry from nodes
        fromGeo = From[1]["geo"]
        toGeo = To[1]["geo"]

        # create edge geometry
        edgeGeo = RhinoLine(fromGeo, toGeo)

        # create edge attribute
        edgeAttrs = {"warp": False,
                     "weft": True,
                     "segment": segment,
                     "geo": edgeGeo}

        self.add_edge(fromNode, toNode, attr_dict=edgeAttrs)

        return True

    def CreateWarpEdge(self, From, To):
        """
        Creates a 'warp' edge between two nodes in the network, returns True if
        the edge has been successfully created.
        """

        # get node indices
        fromNode = From[0]
        toNode = To[0]

        # get geometry from nodes
        fromGeo = From[1]["geo"]
        toGeo = To[1]["geo"]

        # create edge geometry
        edgeGeo = RhinoLine(fromGeo, toGeo)

        # create edge attribute
        edgeAttrs = {"warp": True,
                     "weft": False,
                     "segment": None,
                     "geo": edgeGeo}

        self.add_edge(fromNode, toNode, attr_dict=edgeAttrs)

        return True

    def CreateSegmentContourEdge(self, From, To, segment_value, segment_geo):
        """
        Creates a mapping edge between two 'end' nodes in the network. The
        geometry of this edge will be a polyline built from all the given
        former 'weft' edges. returns True if the edge has been successfully
        created.

        Parameters
        ----------
        From : node
            source node of the edge

        To : node
            target node of the edge

        segment_value : 3-tuple of :obj:`int`
            the segment attribute value of the edge

        segment_geo : list of :class:`Rhino.Geometry.Line`
            the geometry of all 'weft' edges that make this segment contour edge

        Returns
        -------
            True on success, False otherwise.
        """

        # get node indices
        fromNode = From[0]
        toNode = To[0]

        # join geo together
        segment_geo = [RhinoLineCurve(l) for l in segment_geo]
        edgeGeo = RhinoCurve.JoinCurves(segment_geo)
        if len(edgeGeo) > 1:
            errMsg = ("Segment geometry could not be joined into " +
                      "one single curve for segment {}!".format(segment_value))
            print(errMsg)
            return False
            # raise KnitNetworkGeometryError(errMsg)

        edgeGeo = edgeGeo[0].ToPolyline()
        if not edgeGeo[0] == From[1]["geo"]:
            edgeGeo.Reverse()

        # create edge attribute
        edgeAttrs = {"warp": False,
                     "weft": False,
                     "segment": segment_value,
                     "geo": edgeGeo}

        self.add_node(fromNode, attr_dict=From[1])
        self.add_node(toNode, attr_dict=To[1])
        self.add_edge(fromNode, toNode, attr_dict=edgeAttrs)

        return True

    # EDGE METHODS -------------------------------------------------------------

    def EdgeGeometryDirection(self, u, v):
        """
        Returns a given edge in order with reference to the direction of the
        associated geometry (line).
        """

        # get data of the edge
        edge_geo = self[u][v]["geo"]

        # compare the startpoint
        if (edge_geo.From == self.node[u]["geo"] \
        and edge_geo.To == self.node[v]["geo"]):
            return (u, v)
        else:
            return (v, u)

    # EDGE PROPERTIES ----------------------------------------------------------

    def _get_contour_edges(self):
        """
        Get all contour edges of the network that are neither 'weft' nor 'warp'.
        """

        ContourEdges = [(f, t, d) for f, t, d in self.edges_iter(data=True) \
                        if not d["weft"] and not d["warp"]]
        for i, ce in enumerate(ContourEdges):
            if ce[0] > ce[1]:
                ContourEdges[i] = (ce[1], ce[0], ce[2])
        return ContourEdges

    ContourEdges = property(_get_contour_edges, None, None,
                            "The contour edges of the network marked neither " +
                            "'weft' nor 'warp'.")

    def _get_weft_edges(self):
        """
        Get all 'weft' edges of the network.
        """

        WeftEdges = [(f, t, d) for f, t, d in self.edges_iter(data=True) \
                     if d["weft"] and not d["warp"]]
        for i, we in enumerate(WeftEdges):
            if we[0] > we[1]:
                WeftEdges[i] = (we[1], we[0], we[2])
        return WeftEdges

    WeftEdges = property(_get_weft_edges, None, None,
                         "The edges of the network marked 'weft'.")

    def _get_warp_edges(self):
        """
        Get all 'warp' edges of the network.
        """

        WarpEdges = [(f, t, d) for f, t, d in self.edges_iter(data=True) \
                     if not d["weft"] and d["warp"]]
        for i, we in enumerate(WarpEdges):
            if we[0] > we[1]:
                WarpEdges[i] = (we[1], we[0], we[2])
        return WarpEdges

    WarpEdges = property(_get_warp_edges, None, None,
                         "The edges of the network marked 'warp'.")

    def _get_segment_contour_edges(self):
        """
        Get all contour edges of the network marked neither 'warp' nor 'weft'
        that have a 'segment' attribute assigned sorted by the 'segment'
        attribute.
        """

        SegmentContourEdges = [(f, t, d) for f, t, d \
                               in self.edges_iter(data=True) if \
                               not d["weft"]and \
                               not d["warp"]]
        SegmentContourEdges = [sce for sce in SegmentContourEdges \
                               if sce[2]["segment"]]

        for i, sce in enumerate(SegmentContourEdges):
            if sce[0] > sce[1]:
                SegmentContourEdges[i] = (sce[1], sce[0], sce[2])

        # sort them by their 'segment' attributes value
        SegmentContourEdges.sort(key=lambda x: x[2]["segment"])

        return SegmentContourEdges

    SegmentContourEdges = property(_get_segment_contour_edges, None, None,
                         "The edges of the network marked neither 'warp' "+
                         "nor 'weft' and which have a 'segment' attribute "+
                         "assigned to them.")

    # NODE EDGE METHODS --------------------------------------------------------

    def NodeWeftEdges(self, node, data=False):
        """
        Gets the 'weft' edges connected to the given node.
        """

        WeftEdges = [(s, e, d) for s, e, d in \
                     self.edges_iter(node, data=True) if d["weft"]]

        if data:
            return WeftEdges
        else:
            return [(e[0], e[1]) for e in WeftEdges]

    def NodeWarpEdges(self, node, data=False):
        """
        Gets the 'warp' edges connected to the given node.
        """

        WarpEdges = [(s, e, d) for s, e, d in \
                     self.edges_iter(node, data=True) if d["warp"]]

        if data:
            return WarpEdges
        else:
            return [(e[0], e[1]) for e in WarpEdges]

    def NodeContourEdges(self, node, data=False):
        """
        Gets the edges marked neither 'warp' nor 'weft' connected to the
        given node.
        """

        ContourEdges = [(s, e, d) for s, e, d in \
                        self.edges_iter(node, data=True) \
                        if not d["warp"] and not d["weft"]]

        if data:
            return ContourEdges
        else:
            return [(e[0], e[1]) for e in ContourEdges]

    # SEGMENT CONTOUR END NODE METHODS -----------------------------------------

    def EndNodeSegmentsByStart(self, node, data=False):
        """
        Get all the segments which share a given 'end' node at the start
        and sort them by their 'segment' value
        """

        connected_segments = [(s, e, d) for s, e, d \
                              in self.edges_iter(node, data=True) if
                              not d["warp"] and not d["weft"]]
        connected_segments = [cs for cs in connected_segments \
                              if cs[2]["segment"]]
        connected_segments = [cs for cs in connected_segments \
                              if cs[2]["segment"][0] == node]

        connected_segments.sort(key=lambda x: x[2]["segment"])

        if data:
            return connected_segments
        else:
            return [(cs[0], cs[1]) for cs in connected_segments]

    def EndNodeSegmentsByEnd(self, node, data=False):
        """
        Get all the segments which share a given 'end' node at the end
        and sort them by their 'segment' value
        """

        connected_segments = [(s, e, d) for s, e, d \
                              in self.edges_iter(node, data=True) if
                              not d["warp"] and not d["weft"]]
        connected_segments = [cs for cs in connected_segments \
                              if cs[2]["segment"]]
        connected_segments = [cs for cs in connected_segments \
                              if cs[2]["segment"][1] == node]

        connected_segments.sort(key=lambda x: x[2]["segment"])

        if data:
            return connected_segments
        else:
            return [(cs[0], cs[1]) for cs in connected_segments]

# MAIN -------------------------------------------------------------------------
if __name__ == '__main__':
    pass
