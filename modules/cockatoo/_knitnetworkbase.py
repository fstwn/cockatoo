# PYTHON STANDARD LIBRARY IMPORTS ---------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from collections import OrderedDict

# DUNDER ----------------------------------------------------------------------
__all__ = [
    "KnitNetworkBase"
]

# THIRD PARTY MODULE IMPORTS --------------------------------------------------
import networkx as nx

# LOCAL MODULE IMPORTS --------------------------------------------------------
from cockatoo.environment import RHINOINSIDE

# RHINO IMPORTS ---------------------------------------------------------------
if RHINOINSIDE:
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

# CLASS DECLARATION -----------------------------------------------------------


class KnitNetworkBase(nx.Graph):
    """
    Abstract datastructure for representing a network (graph) consisting of
    nodes with special attributes aswell as 'warp' edges, 'weft' edges and
    contour edges which are neither 'warp' nor 'weft'.

    Used as a base class for sharing behaviour between the KnitNetwork,
    KnitMappingNetwork and KnitDiNetwork classes.

    Inherits from :class:`networkx.Graph`.
    For more info, see *NetworkX* [13]_.

    References
    ----------
    .. [13] Hagberg, Aric A.; Schult, Daniel A.; Swart, Pieter J.
            *Exploring Network Structure, Dynamics, and Function using
            NetworkX* In: *Varoquaux, Vaught et al. (Hg.) 2008 - Proceedings
            of the 7th Python in Science Conference* pp. 11-15

            See: `NetworkX 1.5 <https://networkx.github.io/documentation/
            networkx-1.5/>`_
    """

    # REPRESENTATION OF NETWORK -----------------------------------------------

    def __str__(self):
        """
        Return the graph name if it is set, otherwise return a textual
        description of the network.

        Returns
        -------
        name : str
            The name of the graph or a textual description of the network.
        """
        if self.name != "":
            return self.name
        else:
            return self.ToString()

    def __repr__(self):
        """
        Return a textual description of the network.

        Returns
        -------
        description : str
            A textual description of the network.
        """

        if self.name != "":
            name = self.name
        else:
            name = "KnitNetworkBase"

        nn = len(self.nodes())
        ce = len(self.contour_edges)
        wee = len(self.weft_edges)
        wae = len(self.warp_edges)
        data = ("({} Nodes, {} Contours, {} Weft, {} Warp)")
        data = data.format(nn, ce, wee, wae)

        return name + data

    def ToString(self):
        """
        Return a textual description of the network.

        Returns
        -------
        description : str
            A textual description of the network.

        Notes
        -----
        Used for overloading the Grasshopper display in data parameters.
        """

        return repr(self)

    def prepare_for_graphviz(self):
        """
        Creates a new graph with attributes for visualising this network
        using GraphViz.

        Based on code by Anders Holden Deleuran
        """

        # Set render variables
        nodeFontSize = 10
        edgeFontSize = 3.75
        arrowSize = 0.4

        # shapes
        circle = "circle"

        # colors
        black = "black"
        white = "white"
        red = "red"
        blue = "blue"

        col_regular = "black"
        col_start = "green"
        col_start_leaf = "seagreen"
        col_start_leaf_end = "orange"
        col_start_end = "darkgreen"
        col_end = "blue"
        col_leaf = "cyan"
        col_end_leaf = "magenta"
        col_increase_end = "purple"
        col_decrease_end = "darkorchid4"
        col_increase = "red"
        col_decrease = "darkred"

        font = "Helvetica"

        # choose graph type for new graph depending on current graph
        if isinstance(self, nx.MultiGraph):
            DotGraph = nx.MultiDiGraph()
        else:
            DotGraph = nx.DiGraph()

        # get all nodes and all edges
        network_nodes = self.nodes(data=True)
        network_edges = self.edges(data=True)

        # process all nodes and add them to the dot graph
        for node in network_nodes:
            ndata = node[1]

            # END BUT NOT LEAF
            if ndata["end"] and not ndata["leaf"]:
                if not ndata["increase"] and not ndata["decrease"]:
                    if ndata["start"]:
                        node_type = "S"
                        node_color = col_start_end
                        node_txt_color = black
                    else:
                        node_type = "E"
                        node_color = col_end
                        node_txt_color = white

                elif ndata["increase"] and not ndata["decrease"]:
                    node_type = "Ei"
                    node_color = col_increase_end
                    node_txt_color = black
                elif not ndata["increase"] and ndata["decrease"]:
                    node_type = "Ed"
                    node_color = col_decrease_end
                    node_txt_color = black

                node_shape = circle

            # LEAF BUT NOT END
            elif ndata["leaf"] and not ndata["end"]:
                if ndata["start"]:
                    node_type = "SL"
                    node_color = col_start_leaf
                else:
                    node_type = "L"
                    node_color = col_leaf

                node_txt_color = black
                node_shape = circle

            # END AND LEAF
            elif ndata["leaf"] and ndata["end"]:
                if ndata["start"]:
                    node_type = "SEL"
                    node_color = col_start_leaf_end
                else:
                    node_type = "EL"
                    node_color = col_end_leaf

                node_txt_color = black
                node_shape = circle

            # NO END NO LEAF
            elif not ndata["leaf"] and not ndata["end"]:
                # INCREASE
                if ndata["increase"] and not ndata["decrease"]:
                    node_type = "i"
                    node_color = col_increase
                # DECREASE
                elif not ndata["increase"] and ndata["decrease"]:
                    node_type = "d"
                    node_color = col_decrease
                else:
                    node_type = "R"
                    node_color = col_regular

                node_txt_color = white
                node_shape = circle

            if node[1]["segment"]:
                node_label = str(node[0]) + "\n" + node_type + "\n" + \
                             str(node[1]["segment"])
            else:
                node_label = str(node[0]) + node_type

            node_attributes = {"x": ndata["x"],
                               "y": ndata["y"],
                               "z": ndata["z"],
                               "label": node_label,
                               "shape": node_shape,
                               "fontname": font,
                               "style": "filled",
                               "fillcolor": node_color,
                               "fontcolor": node_txt_color,
                               "fontsize": nodeFontSize,
                               "margin": 0.0001}

            DotGraph.add_node(node[0], attr_dict=node_attributes)

        # make edge types and labels and add them to the graph
        for edge in network_edges:
            padding = "  "
            if edge[2]["weft"]:
                edge_type = "WP"
                edge_color = blue
            elif edge[2]["warp"]:
                edge_type = "WT"
                edge_color = red
            elif not edge[2]["weft"] and not edge[2]["warp"]:
                edge_type = "C"
                edge_color = black

            edge_info = str(edge[0]) + ">" + str(edge[1])
            edge_segment = edge[2]["segment"]
            if edge_segment:
                edge_label = edge_info + edge_type + "\n" + str(edge_segment)
            else:
                edge_label = edge_info + edge_type

            DotGraph.add_edge(
                            edge[0],
                            edge[1],
                            label=edge_label,
                            fontname=font,
                            fontcolor=black,
                            color=edge_color,
                            fontsize=edgeFontSize,
                            arrowsize=arrowSize)

        return DotGraph

    def make_gephi_graph(self):
        """
        Creates a new graph with attributes for visualising this network
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

        network_nodes = self.nodes(data=True)
        network_edges = self.edges(data=True)

        # add all nodes to the render graph
        for node in network_nodes:
            if node[1]["end"] and not node[1]["leaf"]:
                node_type = "end"
                node_color = red
                node_shape = circle

            elif node[1]["leaf"] and not node[1]["end"]:
                node_type = "leaf"
                node_color = green
                node_shape = circle

            elif node[1]["leaf"] and node[1]["end"]:
                node_type = "end leaf"
                node_color = orange
                node_shape = circle

            else:
                node_type = "regular"
                node_color = black
                node_shape = circle

            nodeAttrs = {"color": node_color,
                         "shape": node_shape,
                         "type": node_type}

            GephiGraph.add_node(node[0], attr_dict=nodeAttrs)

        # ad all edges to the render graph
        for edge in network_edges:
            if edge[2]["weft"]:
                edge_type = "weft"
                edge_color = blue
            elif edge[2]["warp"]:
                edge_type = "warp"
                edge_color = red
            elif not edge[2]["weft"] and not edge[2]["warp"]:
                continue

            edgeAttrs = {"color": edge_color,
                         "type": edge_type}

            GephiGraph.add_edge(edge[0], edge[1], attr_dict=edgeAttrs)

        return GephiGraph

    # NODE CREATION -----------------------------------------------------------

    def node_from_point3d(self, node_index, pt, position=None, num=None,
                          leaf=False, start=False, end=False, segment=None,
                          increase=False, decrease=False, color=None):
        """
        Creates a network node from a Rhino Point3d and attributes.

        Parameters
        ----------
        node_index : hashable
            The index of the node in the network. Usually an integer is used.

        pt : :class:`Rhino.Geometry.Point3d`
            A RhinoCommon Point3d object.

        position : hashable, optional
            The 'position' attribute of the node identifying the underlying
            contour edge of the network.

            Defaults to ``None``.

        num : int, optional
            The 'num' attribute of the node representing its index in the
            underlying contour edge of the network.

            Defaults to ``None``.

        leaf : bool, optional
            The 'leaf' attribute of the node identifying it as a node on the
            first or last course of the knitting pattern.

            Defaults to ``False``.

        start : bool, optional
            The 'start' attribute of the node identifying it as the start of
            a course.

            Defaults to ``False``.

        end : bool, optional
            The 'end' attribute of the node identifying it as the end of a
            segment or course.

            Defaults to ``False``.

        segment : :obj:`tuple` of :obj:`int`, optional
            The 'segment' attribute of the node identifying its position
            between two 'end' nodes.

            Defaults to ``None``.

        increase : bool, optional
            The 'increase' attribute identifying the node as an increase
            (needed for translation from dual to 2d knitting pattern).

            Defaults to ``False``.

        decrease : bool, optional
            The 'decrease' attribute identifying the node as a decrease
            (needed for translation from dual to 2d knitting pattern).

            Defaults to ``False``.

        color : :obj:`System.Drawing.Color`, optional
            The 'color' attribute of the node, representing the color of the
            pixel when translating the network to a 2d knitting pattern.

            Defaults to ``None``.
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
                           "start": start,
                           "end": end,
                           "segment": segment,
                           "increase": increase,
                           "decrease": decrease,
                           "geo": pt,
                           "color": color}

        # add the node to the network instance
        self.add_node(node_index, attr_dict=node_attributes)

    # NODE GEOMETRY -----------------------------------------------------------

    def node_geometry(self, node_index):
        """
        Gets the geometry from the 'geo' attribute of the supplied node.

        Parameters
        ----------
        node_index : hashable
            The unique identifier of the node, an int in most cases.

        Returns
        -------
        geometry : data
            The data of the 'geo' attribute of the specified node or ``None``
            if the node is not present or has no 'geo' attribute.
        """
        try:
            return self.node[node_index]["geo"]
        except KeyError:
            return None

    def node_coordinates(self, node_index):
        """
        Gets the node coordinates from the 'x', 'y' and 'z' attributes of the
        supplied node.

        Parameters
        ----------
        node_index : hashable
            The unique identifier of the node, an int in most cases.

        Returns
        -------
        xyz : :obj:`tuple` of :obj:`int`
            The XYZ coordinates of the node as a 3-tuple.
        """
        try:
            node_data = self.node[node_index]
            NodeX = node_data["x"]
            NodeY = node_data["y"]
            NodeZ = node_data["z"]
            return (NodeX, NodeY, NodeZ)
        except KeyError:
            return None

    # PROPERTIES --------------------------------------------------------------

    def _get_total_positions(self):
        """
        Gets the number of total positions (i.e. contours) inside the network.
        """

        total = max([n[1]["position"] for n in self.nodes_iter(data=True)])+1
        return total

    total_positions = property(
                            _get_total_positions,
                            None,
                            None,
                            "The total number of positions (i.e. contours) " +
                            "inside the network")

    # NODES ON POSITION CONTOURS ----------------------------------------------

    def nodes_on_position(self, position, data=False):
        """
        Gets the nodes on a given position (i.e. contour) by returning all
        nodes which share the given value as their 'position' attribute.

        Parameters
        ----------
        position : hashable
            The index of the position.

        data : bool, optional
            If ``True``, found nodes will be returned with their attribute
            data.

            Defaults to ``False``.

        Returns
        -------
        nodes : :obj:`list`
            The nodes sharing the supplied 'position' attribute.
        """

        nodes = [(n, d) for n, d in self.nodes_iter(data=True)
                 if d["position"] == position]

        nodes.sort(key=lambda x: x[1]["num"])

        if not data:
            nodes = [n[0] for n in nodes]

        return nodes

    def all_nodes_by_position(self, data=False):
        """
        Gets all the nodes of the network, ordered by the values of their
        'position' attribute.

        Parameters
        ----------
        data : bool, optional
            If ``True``, found nodes will be returned with their attribute
            data.

            Defaults to ``False``.

        Returns
        -------
        nodes : :obj:`list` of :obj:`list`
            All nodes grouped by their 'position' attribute
        """

        allPositionNodes = sorted(
                                [(n, d) for n, d in self.nodes_iter(data=True)
                                 if d["position"] is not None],
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

    # NODES ON SEGMENT CONTOURS -----------------------------------------------

    def nodes_on_segment(self, segment, data=False):
        """
        Gets all nodes on a given segment by finding all nodes which share the
        specified value as their 'segment' attribute, ordered by the value of
        their 'num' attribute.

        Parameters
        ----------
        segment : hashable
            The identifier of the segment to look for.

        data : bool, optional
            If ``True``, found nodes will be returned with their attribute
            data.

            Defaults to ``False``.

        Returns
        -------
        nodes : :obj:`list`
            List of nodes sharing the supplied value as their 'segment'
            attribute, ordered by their 'num' attribute.
        """

        nodes = [(n, d) for n, d in self.nodes_iter(data=True)
                 if d["segment"] == segment]

        nodes.sort(key=lambda x: x[1]["num"])

        if data:
            return nodes
        else:
            return [n[0] for n in nodes]

    # LEAF NODES --------------------------------------------------------------

    def _get_leaf_nodes(self):
        """
        Gets all 'leaf' nodes of the network.

        Returns
        -------
        nodes : :obj:`list`
            List of all nodes for which the attribute 'leaf' is ``True``
        """

        leaves = [(n, d) for n, d in self.nodes_iter(data=True)
                  if d["leaf"] is True]

        return leaves

    leaf_nodes = property(_get_leaf_nodes, None, None,
                          "All 'leaf' nodes of the network.")

    def leaves_on_position(self, position, data=False):
        """
        Gets all 'leaf' nodes which share the supplied value as their
        'position' attribute.

        Parameters
        ----------
        position : hashable
            The index / identifier of the position

        data : bool, optional
            If ``True``, found nodes will be returned with their attribute
            data.

            Defaults to ``False``.

        Returns
        -------
        nodes : :obj:`list`
            List of all nodes for which the attribute 'leaf' is ``True`` and
            which share the supplied value as their 'position' attribute
        """

        leaves = [(n, d) for n, d
                  in self.nodes_on_position(position, data=True)
                  if d["leaf"]]
        if not data:
            leaves = [n[0] for n in leaves]
        return leaves

    def all_leaves_by_position(self, data=False):
        """
        Gets all 'leaf' nodes ordered by their 'position' attribute.

        Parameters
        ----------
        data : bool, optional
            If ``True``, found nodes will be returned with their attribute
            data.

            Defaults to ``False``.

        Returns
        -------
        nodes : :obj:`list` of :obj:`list`
            All nodes for which the attribute 'leaf' is true, grouped by their
            'position' attribute
        """

        allPositionLeaves = sorted(
                            [(n, d) for n, d in self.nodes_iter(data=True)
                             if d["position"] is not None and d["leaf"]],
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

    # END NODES ---------------------------------------------------------------

    def _get_end_nodes(self):
        """
        Gets all 'end' nodes of the network.
        """

        ends = [(n, d) for n, d in self.nodes_iter(data=True)
                if d["end"]]

        return ends

    end_nodes = property(_get_end_nodes, None, None,
                         "All 'end' nodes of the network")

    def ends_on_position(self, position, data=False):
        """
        Gets all 'end' nodes which share the supplied value as their 'position'
        attribute.

        Parameters
        ----------
        position : hashable
            The index / identifier of the position

        data : bool, optional
            If ``True``, found nodes will be returned with their attribute
            data.

            Defaults to ``False``.

        Returns
        -------
        nodes : :obj:`list`
            List of all nodes for which the attribute 'end' is ``True`` and
            which share the supplied value as their 'position' attribute
        """

        ends = [(n, d) for n, d in self.nodes_on_position(position, data=True)
                if d["end"]]
        if not data:
            return [n[0] for n in ends]
        return ends

    def all_ends_by_position(self, data=False):
        """
        Gets all 'end' nodes ordered by their 'position' attribute.

        Parameters
        ----------
        data : bool, optional
            If ``True``, found nodes will be returned with their attribute
            data.

            Defaults to ``False``.

        Returns
        -------
        nodes : :obj:`list` of :obj:`list`
            All nodes for which the attribute 'end' is true, grouped by their
            'position' attribute
        """

        allPositionEnds = sorted(
                            [(n, d) for n, d in self.nodes_iter(data=True)
                             if d["position"] is not None and d["end"]],
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

    # POSITION CONTOUR METHODS ------------------------------------------------

    def geometry_at_position_contour(self, position, as_crv=False):
        """
        Gets the contour polyline at a given position by making a polyline
        from all nodes which share the specified 'position' attribute.

        Parameters
        ----------
        position : hashable
            The index / identifier of the position

        as_crv : bool, optional
            If ``True``, will return a PolylineCurve instead of a Polyline.

            Defaults to ``False``.

        Returns
        -------
        contour : :obj:`Rhino.Geometry.Polyline`
            The contour as a Polyline if ``as_crv`` is ``False``.
        contour : :obj:`Rhino.Geometry.PolylineCurve`
            The contour as a PolylineCurve if ``as_crv`` is ``True``.
        """

        points = [n[1]["geo"] for n in self.nodes_on_position(position, True)]
        Contour = RhinoPolyline(points)
        if as_crv:
            Contour = Contour.ToPolylineCurve()
        return Contour

    def longest_position_contour(self):
        """
        Gets the longest contour 'position', geometry andgeometric length.

        Returns
        -------
        contour_data : :obj:`tuple`
            3-tuple of the 'position' identifier, the contour geometry and its
            length.
        """

        longestLength = 0
        longestContour = None
        longestPosition = None
        for i in range(self.total_positions):
            contour = self.geometry_at_position_contour(i, True)
            cl = contour.GetLength()
            if cl > longestLength:
                longestLength = cl
                longestContour = contour.Duplicate()
                longestPosition = i
            contour.Dispose()
        return (longestPosition, longestContour, longestLength)

    # EDGE CREATION METHODS ---------------------------------------------------

    def create_contour_edge(self, from_node, to_node):
        """
        Creates an edge neither 'warp' nor 'weft' between two nodes in the
        network.

        Parameters
        ----------
        from_node : :obj:`tuple`
            2-tuple of (node_identifier, node_data) that represents the edges'
            source node.
        to_node : :obj:`tuple`
            2-tuple of (node_identifier, node_data) that represents the edges'
            target node.

        Returns
        -------
        success : bool
            ``True`` if the edge has been successfully created,
            ``False`` otherwise.
        """

        # get node indices
        fromNode = from_node[0]
        toNode = to_node[0]

        # get geometry from nodes
        fromGeo = from_node[1]["geo"]
        toGeo = to_node[1]["geo"]

        # create edge geometry
        edgeGeo = RhinoLine(fromGeo, toGeo)

        # create edge attribute
        edgeAttrs = {"warp": False,
                     "weft": False,
                     "segment": None,
                     "geo": edgeGeo}

        try:
            self.add_edge(fromNode, toNode, attr_dict=edgeAttrs)
        except Exception:
            return False

        return True

    def create_weft_edge(self, from_node, to_node, segment=None):
        """
        Creates a 'weft' edge between two nodes in the network.

        Parameters
        ----------
        from_node : :obj:`tuple`
            2-tuple of (node_identifier, node_data) that represents the edges'
            source node.
        to_node : :obj:`tuple`
            2-tuple of (node_identifier, node_data) that represents the edges'
            target node.
        segment : :obj:`tuple`
            3-tuple that will be used to set the 'segment' attribute of the
            'weft' edge.

        Returns
        -------
        success : bool
            ``True`` if the edge has been successfully created.
            ``False`` otherwise.
        """

        # get node indices
        fromNode = from_node[0]
        toNode = to_node[0]

        # get geometry from nodes
        fromGeo = from_node[1]["geo"]
        toGeo = to_node[1]["geo"]

        # create edge geometry
        edgeGeo = RhinoLine(fromGeo, toGeo)

        # create edge attribute
        edgeAttrs = {"warp": False,
                     "weft": True,
                     "segment": segment,
                     "geo": edgeGeo}

        try:
            self.add_edge(fromNode, toNode, attr_dict=edgeAttrs)
        except Exception:
            return False

        return True

    def create_warp_edge(self, from_node, to_node):
        """
        Creates a 'warp' edge between two nodes in the network.

        Parameters
        ----------
        from_node : :obj:`tuple`
            2-tuple of (node_identifier, node_data) that represents the edges'
            source node.
        to_node : :obj:`tuple`
            2-tuple of (node_identifier, node_data) that represents the edges'
            target node.

        Returns
        -------
        success : bool
            ``True`` if the edge has been successfully created.
            ``False`` otherwise.
        """

        # get node indices
        fromNode = from_node[0]
        toNode = to_node[0]

        # get geometry from nodes
        fromGeo = from_node[1]["geo"]
        toGeo = to_node[1]["geo"]

        # create edge geometry
        edgeGeo = RhinoLine(fromGeo, toGeo)

        # create edge attribute
        edgeAttrs = {"warp": True,
                     "weft": False,
                     "segment": None,
                     "geo": edgeGeo}

        try:
            self.add_edge(fromNode, toNode, attr_dict=edgeAttrs)
        except Exception:
            return False

        return True

    def create_segment_contour_edge(self, from_node, to_node,
                                    segment_value, segment_geo):
        """
        Creates a mapping edge between two 'end' nodes in the network. The
        geometry of this edge will be a polyline built from all the given
        former 'weft' edges. returns True if the edge has been successfully
        created.

        Parameters
        ----------
        from_node : :obj:`tuple`
            2-tuple of (node_identifier, node_data) that represents the edges'
            source node.

        to_node : :obj:`tuple`
            2-tuple of (node_identifier, node_data) that represents the edges'
            target node.

        segment_value : :obj:`tuple` of :obj:`int`
            3-tuple that will be used to set the 'segment' attribute of the
            'weft' edge.

        segment_geo : :obj:`list` of :class:`Rhino.Geometry.Line`
            the geometry of all 'weft' edges that make this segment contour
            edge

        Returns
        -------
        success : bool
            ``True`` if the edge has been successfully created,
            ``False`` otherwise
        """

        # get node indices
        fromNode = from_node[0]
        toNode = to_node[0]

        # join geo together
        segment_geo = [RhinoLineCurve(ln) for ln in segment_geo]
        edgeGeo = RhinoCurve.JoinCurves(segment_geo)
        if len(edgeGeo) > 1:
            errMsg = ("Segment geometry could not be joined into " +
                      "one single curve for segment {}!".format(segment_value))
            print(errMsg)
            return False

        edgeGeo = edgeGeo[0].ToPolyline()
        if not edgeGeo[0] == from_node[1]["geo"]:
            edgeGeo.Reverse()

        # create edge attribute
        edgeAttrs = {"warp": False,
                     "weft": False,
                     "segment": segment_value,
                     "geo": edgeGeo}

        self.add_node(fromNode, attr_dict=from_node[1])
        self.add_node(toNode, attr_dict=to_node[1])

        try:
            self.add_edge(fromNode, toNode, attr_dict=edgeAttrs)
        except Exception:
            return False

        return True

    # EDGE METHODS ------------------------------------------------------------

    def edge_geometry_direction(self, u, v):
        """
        Returns a given edge in order with reference to the direction of the
        associated geometry (line).

        Parameters
        ----------
        u : hashable
            Hashable identifier of the edges source node.

        v : hashable
            Hashable identifier of the edges target node.

        Returns
        -------
        edge : 2-tuple
            2-tuple of (u, v) or (v, u) depending on the directions
        """

        # get geometry data of the edge
        edge_geo = self[u][v]["geo"]

        # compare start and endpoint and return nodes in order accordingly
        if (edge_geo.From == self.node[u]["geo"]
                and edge_geo.To == self.node[v]["geo"]):
            return (u, v)
        else:
            return (v, u)

    # EDGE PROPERTIES ---------------------------------------------------------

    def _get_contour_edges(self):
        """
        Get all contour edges of the network that are neither 'weft' nor
        'warp'.
        """

        contour_edges = [(f, t, d) for f, t, d in self.edges_iter(data=True)
                         if not d["weft"] and not d["warp"]]
        for i, ce in enumerate(contour_edges):
            if ce[0] > ce[1]:
                contour_edges[i] = (ce[1], ce[0], ce[2])
        return contour_edges

    contour_edges = property(_get_contour_edges, None, None,
                             "The contour edges of the network marked " +
                             "neither 'weft' nor 'warp'.")

    def _get_weft_edges(self):
        """
        Get all 'weft' edges of the network.
        """

        weft_edges = [(f, t, d) for f, t, d in self.edges_iter(data=True)
                      if d["weft"] and not d["warp"]]
        for i, we in enumerate(weft_edges):
            if we[0] > we[1]:
                weft_edges[i] = (we[1], we[0], we[2])
        return weft_edges

    weft_edges = property(_get_weft_edges, None, None,
                          "The edges of the network marked 'weft'.")

    def _get_warp_edges(self):
        """
        Get all 'warp' edges of the network.
        """

        warp_edges = [(f, t, d) for f, t, d in self.edges_iter(data=True)
                      if not d["weft"] and d["warp"]]
        for i, we in enumerate(warp_edges):
            if we[0] > we[1]:
                warp_edges[i] = (we[1], we[0], we[2])
        return warp_edges

    warp_edges = property(_get_warp_edges, None, None,
                          "The edges of the network marked 'warp'.")

    def _get_segment_contour_edges(self):
        """
        Get all contour edges of the network marked neither 'warp' nor 'weft'
        that have a 'segment' attribute assigned sorted by the 'segment'
        attribute.
        """

        segment_contour_edges = [(f, t, d) for f, t, d
                                 in self.edges_iter(data=True)
                                 if not d["weft"] and
                                 not d["warp"]]
        segment_contour_edges = [sce for sce in segment_contour_edges
                                 if sce[2]["segment"]]

        for i, sce in enumerate(segment_contour_edges):
            if sce[0] > sce[1]:
                segment_contour_edges[i] = (sce[1], sce[0], sce[2])

        # sort them by their 'segment' attributes value
        segment_contour_edges.sort(key=lambda x: x[2]["segment"])

        return segment_contour_edges

    segment_contour_edges = property(
                        _get_segment_contour_edges,
                        None,
                        None,
                        "The edges of the network marked neither 'warp' " +
                        "nor 'weft' and which have a 'segment' attribute " +
                        "assigned to them.")

    # NODE EDGE METHODS -------------------------------------------------------

    def node_weft_edges(self, node, data=False):
        """
        Gets the 'weft' edges connected to a given node.

        Parameters
        ----------
        node : hashable
            Hashable identifier of the node to check for 'weft' edges.

        data : bool, optional
            If ``True``, the edges will be returned as 3-tuples with their
            associated attribute data.

            Defaults to ``False``.

        Returns
        -------
        edges : :obj:`list`
            List of 'weft' edges connected to the given node. Each item in the
            list will be either a 2-tuple of (u, v) identifiers or a 3-tuple
            of (u, v, d) where d is the attribute data of the edge, depending
            on the data parameter.
        """

        weft_edges = [(s, e, d) for s, e, d in
                      self.edges_iter(node, data=True) if d["weft"]]

        if data:
            return weft_edges
        else:
            return [(e[0], e[1]) for e in weft_edges]

    def node_warp_edges(self, node, data=False):
        """
        Gets the 'warp' edges connected to the given node.

        Parameters
        ----------
        node : hashable
            Hashable identifier of the node to check for 'warp' edges.

        data : bool, optional
            If ``True``, the edges will be returned as 3-tuples with their
            associated attribute data.

            Defaults to ``False``.

        Returns
        -------
        edges : :obj:`list`
            List of 'warp' edges connected to the given node. Each item in the
            list will be either a 2-tuple of (u, v) identifiers or a 3-tuple
            of (u, v, d) where d is the attribute data of the edge, depending
            on the data parameter.
        """

        warp_edges = [(s, e, d) for s, e, d in
                      self.edges_iter(node, data=True) if d["warp"]]

        if data:
            return warp_edges
        else:
            return [(e[0], e[1]) for e in warp_edges]

    def node_contour_edges(self, node, data=False):
        """
        Gets the edges marked neither 'warp' nor 'weft' connected to the
        given node.

        Parameters
        ----------
        node : hashable
            Hashable identifier of the node to check for edges marked neither
            'warp' nor 'weft'.

        data : bool, optional
            If ``True``, the edges will be returned as 3-tuples with their
            associated attribute data.

            Defaults to ``False``.

        Returns
        -------
        edges : :obj:`list`
            List of edges marked neither 'warp' nor 'weft' connected to the
            given node. Each item in the list will be either a 2-tuple of
            (u, v) identifiers or a 3-tuple of (u, v, d) where d is the
            attribute data of the edge, depending on the data parameter.
        """

        contour_edges = [(s, e, d) for s, e, d in
                         self.edges_iter(node, data=True)
                         if not d["warp"] and not d["weft"]]

        if data:
            return contour_edges
        else:
            return [(e[0], e[1]) for e in contour_edges]

    # SEGMENT CONTOUR END NODE METHODS ----------------------------------------

    def end_node_segments_by_start(self, node, data=False):
        """
        Get all the edges with a 'segment' attribute marked neither 'weft' nor
        'warp' and share a given 'end' node at the start, sorted by the values
        of their 'segment' attribute.

        Parameters
        ----------
        node : hashable
            Hashable identifier of the node to check for connected segments.

        data : bool, optional
            If ``True``, the edges will be returned as 3-tuples with their
            associated attribute data.

            Defaults to ``False``.

        Returns
        -------
        edges : :obj:`list`
            List of edges. Each item will be either a 2-tuple of (u, v)
            identifiers or a 3-tuple of (u, v, d) where d is the attribute data
            of the edge, depending on the data parameter.
        """

        connected_segments = [(s, e, d) for s, e, d
                              in self.edges_iter(node, data=True) if
                              not d["warp"] and not d["weft"]]
        connected_segments = [cs for cs in connected_segments
                              if cs[2]["segment"]]
        connected_segments = [cs for cs in connected_segments
                              if cs[2]["segment"][0] == node]

        connected_segments.sort(key=lambda x: x[2]["segment"])

        if data:
            return connected_segments
        else:
            return [(cs[0], cs[1]) for cs in connected_segments]

    def end_node_segments_by_end(self, node, data=False):
        """
        Get all the edges with a 'segment' attribute marked neither 'weft' nor
        'warp' and share a given 'end' node at the end, sorted by the values
        of their 'segment' attribute.

        Parameters
        ----------
        node : hashable
            Hashable identifier of the node to check for connected segments.

        data : bool, optional
            If ``True``, the edges will be returned as 3-tuples with their
            associated attribute data.

            Defaults to ``False``.

        Returns
        -------
        edges : list
            List of edges. Each item will be either a 2-tuple of (u, v)
            identifiers or a 3-tuple of (u, v, d) where d is the attribute data
            of the edge, depending on the data parameter.
        """

        connected_segments = [(s, e, d) for s, e, d
                              in self.edges_iter(node, data=True) if
                              not d["warp"] and not d["weft"]]
        connected_segments = [cs for cs in connected_segments
                              if cs[2]["segment"]]
        connected_segments = [cs for cs in connected_segments
                              if cs[2]["segment"][1] == node]

        connected_segments.sort(key=lambda x: x[2]["segment"])

        if data:
            return connected_segments
        else:
            return [(cs[0], cs[1]) for cs in connected_segments]

# MAIN ------------------------------------------------------------------------


if __name__ == '__main__':
    pass
