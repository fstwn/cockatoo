# PYTHON LIBRARY IMPORTS
from __future__ import division

# RHINO IMPORTS
import Rhino

# CUSTOM MODULE IMPORTS
import networkx as nx

class KnitNetworkBase(nx.Graph):

    """
    Base class for representing a network that facilitates the automatic
    generation of knitting patterns based on Rhino geometry.
    """

    # REPRESENTATION OF NETWORK ------------------------------------------------

    def ToString(self):
        """
        Return a textual description of the network.
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

    # NODE CREATION ------------------------------------------------------------

    def NodeFromPoint3d(self, node_index, pt, position=None, num=None, leaf=False, end=False, segment=None):
        """
        Creates a network node from a Rhino Point3d and attributes.
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
                           "geo": pt}

        # add the node to the network instance
        self.add_node(node_index, attr_dict=node_attributes)

    # PROPERTIES ---------------------------------------------------------------

    def _get_total_positions(self):
        """
        Gets the number of total positions (contours) inside the network.
        """

        total = max([d["position"] for n, d in self.nodes_iter(data=True)])+1
        return total

    TotalPositions = property(_get_total_positions, None, None,
                              "The total number of positions (contours) " +
                              "inside the network")

    # NODE ORDERING AND SORTING METHODS ----------------------------------------

    def NodesOnPosition(self, pos, data=False):
        """
        Returns the nodes on a given position.
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

        anbp = []
        total = self.TotalPositions
        for pos in range(total):
            posnodes = self.NodesOnPosition(pos, True)
            if data:
                anbp.append(posnodes)
            else:
                anbp.append([pn[0] for pn in posnodes])

        return anbp

    # LEAF NODES ---------------------------------------------------------------

    def LeavesOnPosition(self, pos, data=False):
        """
        Gets 'leaf' vertices on a given position.
        """

        leaves = [(n, d) for n, d in self.NodesOnPosition(pos, data=True) \
                  if d["leaf"] == True]
        if not data:
            leaves = [n[0] for n in leaves]
        return leaves

    def AllLeavesByPosition(self, data=False):
        """
        Gets all 'leaf' vertices on all positions ordered by position.
        """

        albp = []
        total = self.TotalPositions
        for pos in range(total):
            leaves = self.LeavesOnPosition(pos, True)
            if data:
                albp.append(leaves)
            else:
                albp.append([pn[0] for pn in leaves])

        return albp

    # END NODES ----------------------------------------------------------------

    def EndsOnPosition(self, pos, data=False):
        """
        Gets 'end' vertices on a given position.
        """

        ends = [(n, d) for n, d in self.NodesOnPosition(pos, data=True) \
                  if d["end"] == True]
        if not data:
            ends = [n[0] for n in ends]
        return ends

    def AllEndsByPosition(self, data=False):
        """
        Gets all 'end' vertices on all positions ordered by position.
        """

        aebp = []
        total = self.TotalPositions
        for pos in range(total):
            ends = self.EndsOnPosition(pos, True)
            if data:
                aebp.append(ends)
            else:
                aebp.append([pn[0] for pn in ends])

        return aebp

    # POSITION CONTOUR METHODS -------------------------------------------------

    def GeometryAtPositionContour(self, pos, asCrv=False):
        """
        Gets the contour polyline at a given position.
        """

        points = [d["geo"] for n, d in self.NodesOnPosition(pos, True)]
        Contour = Rhino.Geometry.Polyline(points)
        if asCrv:
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
        edgeGeo = Rhino.Geometry.Line(fromGeo, toGeo)

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
        edgeGeo = Rhino.Geometry.Line(fromGeo, toGeo)

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
        edgeGeo = Rhino.Geometry.Line(fromGeo, toGeo)

        # create edge attribute
        edgeAttrs = {"warp": True,
                     "weft": False,
                     "segment": None,
                     "geo": edgeGeo}

        self.add_edge(fromNode, toNode, attr_dict=edgeAttrs)

        return True

    def CreateSegmentContourEdge(self, From, To, segmentValue, segmentGeo):
        """
        Creates a mapping edge between two 'end' nodes in the network. The
        geometry of this edge will be a polyline built from all the given
        former 'weft' edges. returns True if the edge has been successfully
        created.
        """

        # get node indices
        fromNode = From[0]
        toNode = To[0]

        # join geo together
        segmentGeo = [Rhino.Geometry.LineCurve(l) for l in segmentGeo]
        edgeGeo = Rhino.Geometry.Curve.JoinCurves(segmentGeo)
        if len(edgeGeo) > 1:
            print segmentGeo
            print edgeGeo
            return False
            #raise RuntimeError("Segment geometry could not be joined into " +
            #                   "one single curve!")

        edgeGeo = edgeGeo[0].ToPolyline()
        if not edgeGeo[0] == From[1]["geo"]:
            edgeGeo.Reverse()

        # create edge attribute
        edgeAttrs = {"warp": False,
                     "weft": False,
                     "segment": segmentValue,
                     "geo": edgeGeo}

        self.add_node(fromNode, attr_dict=From[1])
        self.add_node(toNode, attr_dict=To[1])
        self.add_edge(fromNode, toNode, attr_dict=edgeAttrs)

        return True

    # EDGE PROPERTIES ----------------------------------------------------------

    def _get_contour_edges(self):
        """
        Get all contour edges of the network that are neither 'weft' nor 'warp'.
        """

        ContourEdges = [(f, t, d) for f, t, d in self.edges_iter(data=True) \
                        if d["weft"] == False and d["warp"] == False]
        return ContourEdges

    ContourEdges = property(_get_contour_edges, None, None,
                            "The contour edges of the network marked neither " +
                            "'weft' nor 'warp'.")

    def _get_weft_edges(self):
        """
        Get all 'weft' edges of the network.
        """

        WeftEdges = [(f, t, d) for f, t, d in self.edges_iter(data=True) \
                     if d["weft"] == True and d["warp"] == False]
        return WeftEdges

    WeftEdges = property(_get_weft_edges, None, None,
                         "The edges of the network marked 'weft'.")

    def _get_warp_edges(self):
        """
        Get all 'warp' edges of the network.
        """

        WarpEdges = [(f, t, d) for f, t, d in self.edges_iter(data=True) \
                     if d["weft"] == False and d["warp"] == True]
        return WarpEdges

    WarpEdges = property(_get_warp_edges, None, None,
                         "The edges of the network marked 'warp'.")

    # EDGE METHODS -------------------------------------------------------------

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

    # EDGE TRAVERSAL -----------------------------------------------------------

    def TraverseEdge(self, startNode, connectedEdge):
        """
        Traverse an edge from a start node and return the other node.
        """

        if startNode != connectedEdge[0]:
            return (connectedEdge[0], self.node[connectedEdge[0]])
        elif startNode != connectedEdge[1]:
            return (connectedEdge[1], self.node[connectedEdge[1]])
