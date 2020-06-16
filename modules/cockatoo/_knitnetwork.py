# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from collections import deque
from collections import OrderedDict
from math import radians
from math import pi
from operator import itemgetter

# DUNDER -----------------------------------------------------------------------
__all__ = [
    "KnitNetwork"
]

# THIRD PARTY MODULE IMPORTS ---------------------------------------------------
import networkx as nx

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from cockatoo._knitnetworkbase import KnitNetworkBase
from cockatoo._knitmappingnetwork import KnitMappingNetwork
from cockatoo._knitdinetwork import KnitDiNetwork
from cockatoo.environment import RHINOINSIDE
from cockatoo.exception import *
from cockatoo.utilities import is_ccw_xy
from cockatoo.utilities import pairwise

# RHINO IMPORTS ----------------------------------------------------------------
if RHINOINSIDE:
    import rhinoinside
    rhinoinside.load()
    from Rhino.Geometry import Brep as RhinoBrep
    from Rhino.Geometry import Curve as RhinoCurve
    from Rhino.Geometry import Line as RhinoLine
    from Rhino.Geometry import Interval as RhinoInterval
    from Rhino.Geometry import Mesh as RhinoMesh
    from Rhino.Geometry import NurbsSurface as RhinoNurbsSurface
    from Rhino.Geometry import Point3d as RhinoPoint3d
    from Rhino.Geometry import Polyline as RhinoPolyline
    from Rhino.Geometry import Surface as RhinoSurface
    from Rhino.Geometry import Vector3d as RhinoVector3d
else:
    from Rhino.Geometry import Brep as RhinoBrep
    from Rhino.Geometry import Curve as RhinoCurve
    from Rhino.Geometry import Line as RhinoLine
    from Rhino.Geometry import Interval as RhinoInterval
    from Rhino.Geometry import Mesh as RhinoMesh
    from Rhino.Geometry import NurbsSurface as RhinoNurbsSurface
    from Rhino.Geometry import Point3d as RhinoPoint3d
    from Rhino.Geometry import Polyline as RhinoPolyline
    from Rhino.Geometry import Surface as RhinoSurface
    from Rhino.Geometry import Vector3d as RhinoVector3d

# CLASS DECLARATION ------------------------------------------------------------
class KnitNetwork(KnitNetworkBase):
    """
    Datastructure for representing a network (graph) consisting of nodes with
    special attributes aswell as 'warp' edges, 'weft' edges and contour edges
    which are neither 'warp' nor 'weft'.

    Used for the automatic generation of knitting patterns based on mesh or
    NURBS surface geometry.

    Inherits from :class:`KnitNetworkBase`.

    Notes
    -----
    The implemented algorithms are strongly based on the paper
    *Automated Generation of Knit Patterns for Non-developable Surfaces* [1]_.
    Also see *KnitCrete - Stay-in-place knitted formworks for complex concrete
    structures* [2]_.

    The implementation was further influenced by concepts and ideas presented
    in the papers *Automatic Machine Knitting of 3D Meshes* [3]_,
    *Visual Knitting Machine Programming* [4]_ and
    *A Compiler for 3D Machine Knitting* [5]_.

    References
    ----------
    .. [1] Popescu, Mariana et al. *Automated Generation of Knit Patterns
           for Non-developable Surfaces*

           See: `Automated Generation of Knit Patterns for Non-developable
           Surfaces <https://block.arch.ethz.ch/brg/files/POPESCU_DMSP-2017_automated-generation-knit-patterns_1505737906.pdf>`_

    .. [2] Popescu, Mariana *KnitCrete - Stay-in-place knitted formworks for
           complex concrete structures*

           See: `KnitCrete - Stay-in-place knitted formworks for complex
           concrete structures <https://block.arch.ethz.ch/brg/files/POPESCU_2019_ETHZ_PhD_KnitCrete-Stay-in-place-knitted-fabric-formwork-for-complex-concrete-structures_small_1586266206.pdf>`_

    .. [3] Narayanan, Vidya; Albaugh, Lea; Hodgins, Jessica; Coros, Stelian;
           McCann, James *Automatic Machine Knitting of 3D Meshes*

           See: `Automatic Machine Knitting of 3D Meshes
           <https://textiles-lab.github.io/publications/2018-autoknit/>`_

    .. [4] Narayanan, Vidya; Wu, Kui et al. *Visual Knitting Machine
           Programming*

           See: `Visual Knitting Machine Programming
           <https://textiles-lab.github.io/publications/2019-visualknit/>`_

    .. [5] McCann, James; Albaugh, Lea; Narayanan, Vidya; Grow, April;
           Matusik, Wojciech; Mankoff, Jen; Hodgins, Jessica
           *A Compiler for 3D Machine Knitting*

           See: `A Compiler for 3D Machine Knitting
           <https://la.disneyresearch.com/publication/machine-knitting-compiler/>`_
    """

    # INITIALIZATION -----------------------------------------------------------

    def __init__(self, data=None, **attr):
        """
        Initialize a KnitNetwork (inherits NetworkX graph) with edges, name,
        graph attributes.

        Parameters
        ----------
        data : input graph
            Data to initialize graph.  If data=None (default) an empty
            network is created.  The data can be an edge list, any
            KnitNetworkBase or NetworkX graph object.

        name : string, optional (default='')
            An optional name for the graph.

        attr : keyword arguments, optional (default= no attributes)
            Attributes to add to graph as key=value pairs.
        """

        # initialize using original init method
        super(KnitNetwork, self).__init__(data=data, **attr)

        # also copy the mapping_network attribute if it is already available
        if data and isinstance(data, KnitNetwork) and data.mapping_network:
            self.mapping_network = data.mapping_network
        else:
            self.mapping_network = None

    @classmethod
    def create_from_contours(cls, contours, course_height, reference_geometry=None):
        """
        Create and initialize a KnitNetwork based on a set of contours, a
        given course height and an optional reference geometry.
        The reference geometry is a mesh or surface which should be described by the
        network. While it is optional, it is **HIGHLY** recommended to provide
        it!

        Parameters
        ----------
        contours : :obj:`list` of :class:`Rhino.Geometry.Polyline` or :class:`Rhino.Geometry.Curve`
            Ordered contours (i.e. isocurves, isolines) to initialize the
            KnitNetwork with.

        course_height : float
            The course height for sampling the contours.

        reference_geometry : :class:`Rhino.Geometry.Mesh` or :class:`Rhino.Geometry.Surface`
            Optional underlying geometry that this network is based on.

        Returns
        -------
        KnitNetwork : KnitNetwork
            A new, initialized KnitNetwork instance.

        Notes
        -----
        This method will automatically call initialize_position_contour_edges() on
        the newly created network!

        Raises
        ------
        KnitNetworkGeometryError
            If a supplied contour is not a valid instance of
            :obj:`Rhino.Geometry.Polyline` or :obj:`Rhino.Geometry.Curve`.
        """

        # create network
        network = cls(reference_geometry=reference_geometry)

        # assign reference_geometry if present and valid
        if reference_geometry:
            if isinstance(reference_geometry, RhinoMesh):
                network.graph["reference_geometry"] = reference_geometry
            elif isinstance(reference_geometry, RhinoBrep):
                if reference_geometry.IsSurface:
                    network.graph["reference_geometry"] = RhinoNurbsSurface(
                                                 reference_geometry.Surfaces[0])
            elif isinstance(reference_geometry, RhinoSurface):
                network.graph["reference_geometry"] = reference_geometry
        else:
            network.graph["reference_geometry"] = None

        # divide the contours and fill network with nodes
        nodenum = 0
        for i, crv in enumerate(contours):
            # check input
            if not isinstance(crv, RhinoCurve):
                if isinstance(crv, RhinoPolyline):
                    crv = crv.ToPolylineCurve()
                else:
                    errMsg = ("Contour at index {} is not ".format(i) + \
                              "a valid Curve or Polyline!")
                    raise KnitNetworkGeometryError(errMsg)

            # compute divisioncount and divide contour
            dc = round(crv.GetLength() / course_height)
            tcrv = crv.DivideByCount(dc, True)
            dpts = [crv.PointAt(t) for t in tcrv]

            # loop over all nodes on the current contour
            for j, point in enumerate(dpts):
                # declare node attributes
                vpos = i
                vnum = j
                if j == 0 or j == len(dpts) - 1:
                    vleaf = True
                else:
                    vleaf = False
                # create network node from rhino point
                network.node_from_point3d(nodenum,
                                          point,
                                          position=vpos,
                                          num=vnum,
                                          leaf=vleaf,
                                          start=False,
                                          end=False,
                                          segment=None,
                                          increase=False,
                                          decrease=False,
                                          color=None)

                # increment counter
                nodenum += 1

        # call position contour initialization
        network.initialize_position_contour_edges()

        return network

    # TEXTUAL REPRESENTATION OF NETWORK ----------------------------------------

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
            name = "KnitNetwork"

        nn = len(self.nodes())
        ce = len(self.contour_edges)
        wee = len(self.weft_edges)
        wae = len(self.warp_edges)
        data = ("({} Nodes, {} Position Contours, {} Weft, {} Warp)")
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

    # INITIALIZATION OF POSITION CONTOUR EDGES ---------------------------------

    def initialize_position_contour_edges(self):
        """
        Creates all initial position contour edges as neither 'warp' nor 'weft'
        by iterating over all nodes in the network and grouping them based on
        their 'position' attribute.

        Notes
        -----
        This method is automatically called when creating a KnitNetwork using
        the create_from_contours method!

        Closely resembles the implementation described in Automated Generation
        of Knit Patterns for Non-developable Surfaces* [1]_. Also see *KnitCrete
        - Stay-in-place knitted formworks for complex concrete structures* [2]_.
        """

        # get all nodes by position
        posList = self.all_nodes_by_position(data=True)

        for i, pos in enumerate(posList):
            for j, node in enumerate(pos):
                k = j + 1
                if k < len(pos):
                    self.create_contour_edge(node, pos[k])

    # INITIALIZATION OF 'WEFT' EDGES BETWEEN 'LEAF' NODES ----------------------

    def initialize_leaf_connections(self):
        """
        Create all initial connections of the 'leaf' nodes by iterating over
        all position contours and creating 'weft' edges between the 'leaf'
        nodes of the position contours.

        Notes
        -----
        Closely resembles the implementation described in Automated Generation
        of Knit Patterns for Non-developable Surfaces* [1]_. Also see *KnitCrete
        - Stay-in-place knitted formworks for complex concrete structures* [2]_.
        """

        # get all leaves
        leafNodes = self.all_leaves_by_position(True)

        # loop through all the positions leaves
        for i, lpos in enumerate(leafNodes):
            j = i + 1
            # loop through pairs of leaves
            if j < len(leafNodes):
                startLeaf = lpos[0]
                endLeaf = lpos[1]
                nextStart = leafNodes[j][0]
                nextEnd = leafNodes[j][1]

                # add edges to the network
                self.create_weft_edge(startLeaf, nextStart)
                self.create_weft_edge(endLeaf, nextEnd)

    # INITIALIZATION OF PRELIMINARY 'WEFT' EDGES -------------------------------

    def attempt_weft_connection(self, node, candidate, source_nodes, max_connections=4, verbose=False):
        """
        Method for attempting a 'weft' connection to a candidate
        node based on certain parameters.

        Parameters
        ----------
        node : :obj:`tuple`
            2-tuple representing the source node for the possible 'weft' edge.

        candidate ::obj:`tuple`
            -tuple representing the target node for the possible 'weft' edge.

        source_nodes : :obj:`list`
            List of nodes on the position contour of node. Used to check if
            the candidate node already has a connection.

        max_connections : int, optional
            The new 'weft' connection will only be made if the candidate nodes
            number of connected neighbors is below this.

            Defaults to ``4``.

        verbose : bool, optional
            If ``True``, this routine and all its subroutines will print
            messages about what is happening to the console.

            Defaults to ``False``.

        Returns
        -------
        bool
            ``True`` if the connection has been made,
            ``False`` otherwise.

        Notes
        -----
        Closely resembles the implementation described in Automated Generation
        of Knit Patterns for Non-developable Surfaces* [1]_. Also see *KnitCrete
        - Stay-in-place knitted formworks for complex concrete structures* [2]_.
        """

        # define verbose print function
        v_print = print if verbose else lambda *a, **k: None

        # get connected neighbors
        connecting_neighbors = self[candidate[0]]
        # only do something if the maximum is not reached
        if len(connecting_neighbors) < max_connections:
            # determine if the node is already connected to a node from
            # the input source nodes
            isConnected = False
            for cn in connecting_neighbors:
                if cn in [v[0] for v in source_nodes]:
                    isConnected = True
                    # print info on verbose setting
                    v_print("Candidate node {} is ".format(candidate[0]) +
                            "already connected! " +
                            "Skipping to next " +
                            "node...")
                    break
            # check the flag and act accordingly
            if not isConnected:
                # print info on verbose setting
                v_print("Connecting node {} to best ".format(node[0]) +
                        "candidate {}.".format(candidate[0]))
                # if all conditions are met, make the 'weft' connection
                if node[1]["position"] < candidate[1]["position"]:
                    self.create_weft_edge(node, candidate)
                else:
                    self.create_weft_edge(candidate, node)
                return True
            else:
                return False
        else:
            return False

    def _create_initial_weft_connections(self, contour_set, force_continuous_start=False, force_continuous_end=False, max_connections=4, precise=False, verbose=False):
        """
        Private method for creating initial 'weft' connections for the supplied
        set of contours, starting from the first contour in the set and
        propagating to the last contour in the set.

        Notes
        -----
        Closely resembles the implementation described in Automated Generation
        of Knit Patterns for Non-developable Surfaces* [1]_. Also see *KnitCrete
        - Stay-in-place knitted formworks for complex concrete structures* [2]_.
        """

        # define verbose print function
        v_print = print if verbose else lambda *a, **k: None

        if len(contour_set) < 2:
            v_print("Not enough contours in contour set!")
            return

        # print info on verbose output
        v_print("Creating initial 'weft' connections for contour set...")

        # loop over all nodes of positions (list of lists of tuples)
        for i, pos in enumerate(contour_set):
            # pos is a list of tuples (nodes)
            if i < len(contour_set):
                j = i + 1
                if j == len(contour_set):
                    break

                # get initial and target nodes without 'leaf' nodes
                initial_nodes = contour_set[i][1:-1]
                target_nodes = contour_set[j][1:-1]

                # options for continuous start and end
                if force_continuous_start:
                    initial_nodes = initial_nodes[1:]
                    target_nodes = target_nodes[1:]
                if force_continuous_end:
                    initial_nodes = initial_nodes[:-1]
                    target_nodes = target_nodes[:-1]

                # skip if one of the contours has no nodes
                if len(initial_nodes) == 0 or len(target_nodes) == 0:
                    continue

                # define forbidden node index
                forbidden_node = -1

                # loop through all nodes on the current position
                for k, node in enumerate(initial_nodes):
                    # print info on verbose setting
                    v_print("Processing node {} on position {}:".format(
                                                  node[0], node[1]["position"]))

                    # get the geometry for the current node
                    thisPt = node[1]["geo"]

                    # filtering according to forbidden nodes
                    target_nodes = [tn for tn in target_nodes \
                                    if tn[0] >= forbidden_node]

                    if len(target_nodes) == 0:
                        continue

                    # get four closest nodes on adjacent contour
                    if precise:
                        allDists = [thisPt.DistanceTo(tv[1]["geo"]) \
                                    for tv in target_nodes]
                    else:
                        allDists = [thisPt.DistanceToSquared(tv[1]["geo"]) \
                                    for tv in target_nodes]

                    # sort the target nodes by distance to current node
                    allDists, sorted_target_nodes = zip(
                                *sorted(zip(allDists,
                                            target_nodes),
                                            key = itemgetter(0)))

                    # the four closest nodes are the possible connections
                    possible_connections = sorted_target_nodes[:4]
                    # print info on verbose setting
                    v_print("Possible connections: {}".format([pc[0] for pc in \
                                                         possible_connections]))

                    # handle edge case where there is no possible
                    # connection or just one
                    if len(possible_connections) == 0:
                        # skip if there are no possible connections
                        continue
                    elif len(possible_connections) == 1:
                        # attempt to connect to only possible candidate
                        fCand = possible_connections[0]
                        res = self.attempt_weft_connection(node,
                                                fCand,
                                                initial_nodes,
                                                max_connections=max_connections,
                                                verbose=verbose)
                        # set forbidden node
                        if res:
                            forbidden_node = fCand[0]
                        continue

                    # get the contours current direction
                    if k < len(initial_nodes)-1:
                        contourDir = RhinoLine(thisPt,
                                         initial_nodes[k+1][1]["geo"]).Direction
                    elif k == len(initial_nodes)-1:
                        contourDir = RhinoLine(
                                 initial_nodes[k-1][1]["geo"], thisPt).Direction
                    contourDir.Unitize()

                    # get the directions of the possible connections
                    candidatePoints = [pc[1]["geo"] \
                                       for pc in possible_connections]
                    candidateDirections = [RhinoLine(
                                thisPt, cp).Direction for cp in candidatePoints]
                    [cd.Unitize() for cd in candidateDirections]

                    # get the angles between contour dir and possible conn dir
                    normals = [RhinoVector3d.CrossProduct(
                                  contourDir, cd) for cd in candidateDirections]
                    angles = [RhinoVector3d.VectorAngle(
                              contourDir, cd, n) for cd, n in zip(
                              candidateDirections, normals)]

                    # compute deltas as a mesaure of perpendicularity
                    deltas = [abs(a - (0.5 * pi)) for a in angles]

                    # sort possible connections by distance, then by delta
                    allDists, deltas, angles, most_perpendicular = zip(
                            *sorted(zip(allDists,
                                        deltas,
                                        angles,
                                        possible_connections[:]),
                                        key = itemgetter(0, 1)))

                    # get node neighbors
                    nNeighbors = self[node[0]]

                    # compute angle difference
                    aDelta = angles[0] - angles[1]

                    # CONNECTION FOR LEAST ANGLE CHANGE ------------------------
                    if len(nNeighbors) > 2 and aDelta < radians(6.0):
                        # print info on verbose setting
                        v_print("Using procedure for least angle " +
                                "change connection...")

                        # get previous pos nodes, indices and connections
                        prevPos = contour_set[i-1]
                        prevIndices = [n[0] for n in prevPos]

                        # get previous connected edge and its direction
                        prevEdges = self.node_weft_edges(node[0], data=True)
                        if len(prevEdges) > 1:
                            raise KnitNetworkError("More than one " +
                                  "previous 'weft' connection! This was " +
                                  "unexpected...")
                            prevDir = prevEdges[0][2]["geo"].Direction
                        else:
                            prevDir = prevEdges[0][2]["geo"].Direction
                        prevDir.Unitize()

                        # get directions for the best two candidates
                        mpA = most_perpendicular[0]
                        mpB = most_perpendicular[1]
                        dirA = RhinoLine(thisPt, mpA[1]["geo"]).Direction
                        dirB = RhinoLine(thisPt, mpB[1]["geo"]).Direction
                        dirA.Unitize()
                        dirB.Unitize()

                        # get normals for angle measurement
                        normalA = RhinoVector3d.CrossProduct(prevDir, dirA)
                        normalB = RhinoVector3d.CrossProduct(prevDir, dirB)

                        # measure the angles
                        angleA = RhinoVector3d.VectorAngle(
                                                        prevDir,
                                                        dirA,
                                                        normalA)
                        angleB = RhinoVector3d.VectorAngle(
                                                        prevDir,
                                                        dirB,
                                                        normalB)

                        # select final candidate for connection by angle
                        if angleA < angleB:
                            fCand = mpA
                        else:
                            fCand = mpB

                        # attempt to connect to final candidate
                        res = self.attempt_weft_connection(
                                                node,
                                                fCand,
                                                initial_nodes,
                                                max_connections=max_connections,
                                                verbose=verbose)
                        # set forbidden node for next pass
                        if res:
                            forbidden_node = fCand[0]

                    # CONNECTION FOR MOST PERPENDICULAR --------------------
                    else:
                        # print info on verbose setting
                        v_print("Using procedure for most " +
                                "perpendicular connection...")
                        # define final candidate
                        fCand = most_perpendicular[0]

                        # attempt to connect to final candidate node
                        res = self.attempt_weft_connection(
                                                node,
                                                fCand,
                                                initial_nodes,
                                                max_connections=max_connections,
                                                verbose=verbose)
                        # set forbidden node if connection has been made
                        if res:
                            forbidden_node = fCand[0]

    def _create_second_pass_weft_connections(self, contour_set, include_leaves=False, least_connected=False, precise=False, verbose=False):
        """
        Private method for creating second pass 'weft' connections for the
        given set of contours.

        Notes
        -----
        Closely resembles the implementation described in Automated Generation
        of Knit Patterns for Non-developable Surfaces* [1]_. Also see *KnitCrete
        - Stay-in-place knitted formworks for complex concrete structures* [2]_.
        """

        v_print = print if verbose else lambda *a, **k: None

        # get attributes only once
        position_attributes = nx.get_node_attributes(self, "position")
        num_attributes = nx.get_node_attributes(self, "num")

        if len(contour_set) < 2:
            v_print("Not enough contours in contour set!")
            return

        # print info on verbose output
        v_print("Creating second pass 'weft' connections for contour set...")

        # loop over all nodes of positions (list of lists of tuples)
        for i, pos in enumerate(contour_set):
            j = i + 1

            # get initial nodes
            initial_nodes = contour_set[i]

            # get target position candidates
            if (i > 0 and i < len(contour_set)-1 and \
                i != 0 and i != len(contour_set)-1):
                target_positionA = contour_set[i-1][0][1]["position"]
                target_positionB = contour_set[i+1][0][1]["position"]
            elif i == 0:
                target_positionA = None
                target_positionB = contour_set[i+1][0][1]["position"]
            elif i == len(contour_set)-1:
                target_positionA = contour_set[i-1][0][1]["position"]
                target_positionB = None

            # loop through all nodes on current position
            for k, node in enumerate(initial_nodes):
                # print info on verbose setting
                v_print("Processing node " +
                      "{} on position {}:".format(node[0], node[1]["position"]))

                # get connecting edges on target position
                conWeftEdges = self.node_weft_edges(node[0], data=True)
                conPos = []
                if len(conWeftEdges) == 0 and verbose:
                    # print info on verbose setting
                    v_print("No previously connected weft edges...")
                for weftEdge in conWeftEdges:
                    weftEdgeFrom = weftEdge[0]
                    weftEdgeTo = weftEdge[1]
                    if weftEdgeFrom != node[0]:
                        posEdgeTarget = position_attributes[weftEdgeFrom]
                    elif weftEdgeTo != node[0]:
                        posEdgeTarget = position_attributes[weftEdgeTo]
                    if posEdgeTarget not in conPos:
                        conPos.append(posEdgeTarget)

                # select target position and continue in edge case scenarios
                target_positions = []
                if target_positionA == None:
                    if target_positionB in conPos:
                        v_print("Node is connected. Skipping...")
                        continue
                    target_positions.append(target_positionB)
                elif target_positionB == None:
                    if target_positionA in conPos:
                        v_print("Node is connected. Skipping...")
                        continue
                    target_positions.append(target_positionA)
                elif ((target_positionA in conPos) and
                      (target_positionB in conPos)):
                    v_print("Node is connected. Skipping...")
                    continue
                elif ((target_positionB in conPos) and
                      (target_positionA not in conPos)):
                    target_positions.append(target_positionA)
                elif ((target_positionA in conPos) and
                      (target_positionB not in conPos)):
                    target_positions.append(target_positionB)
                elif (target_positionA != None and \
                      target_positionB != None and len(conPos) == 0):
                    target_positions = [target_positionA, target_positionB]

                # print info on verbose setting
                if verbose and len(target_positions) > 1:
                    v_print("Two target positions: {}, {}".format(
                                                         *target_positions))
                elif verbose and len(target_positions) == 1:
                    v_print("Target position: {}".format(target_positions[0]))

                # skip if there are no target positions
                if len(target_positions) == 0:
                    v_print("No target position! Skipping...")
                    continue

                # only proceed if there is a target position
                for target_position in target_positions:
                    # get target nodes
                    target_nodes = self.nodes_on_position(target_position, True)

                    # get the point geo of this node
                    thisPt = node[1]["geo"]

                    # get a window of possible connections on the target
                    # position by looking for the previos node on this contour
                    # connected to target position, then propagating along
                    # the target position to the next node that is connected
                    # to this position. these two nodes will define the window

                    # NOTE: the current node should never have a connection
                    # to target position (theoretically!), otherwise it should
                    # have fallen through the checks by now

                    # print info on verbose setting
                    v_print("Target position is {}. ".format(target_position) +
                            "Computing window...")

                    # get the previous node on this contour
                    prevNode = initial_nodes[k-1]

                    # assume that the previous node has a connection
                    prevCon = self.node_weft_edges(prevNode[0], data=True)

                    # get possible connections from previous connection
                    possible_connections = []
                    for edge in prevCon:
                        edgeFrom = edge[0]
                        edgeTo = edge[1]
                        if edgeFrom != prevNode[0]:
                            prevNodeTargetPos = position_attributes[edgeFrom]
                            prevNodeTargetIndex = num_attributes[edgeFrom]
                        elif edgeTo != prevNode[0]:
                            prevNodeTargetPos = position_attributes[edgeTo]
                            prevNodeTargetIndex = num_attributes[edgeTo]
                        if prevNodeTargetPos == target_position:
                            possible_connections.append(
                                           target_nodes[prevNodeTargetIndex])

                    # the farthest connection of the previous node is the first
                    # point for our window
                    if len(possible_connections) > 1:
                        possible_connections.sort(key=lambda x: x[1]["num"])
                        possible_connections.reverse()
                        start_of_window = possible_connections[0]
                    elif len(possible_connections) == 1:
                        start_of_window = possible_connections[0]
                    elif len(possible_connections) == 0:
                        # print info on verbose setting
                        v_print("No possible connection, skipping...")
                        continue

                    # get the next node on this pos that is
                    # connected to target position
                    if k < len(initial_nodes)-1:
                        future_nodes = initial_nodes[k+1:]
                        for futurenode in future_nodes:
                            filteredWeftEdges = []
                            futureWeftEdges = self.node_weft_edges(futurenode[0],
                                                                 data=True)
                            for futureweft in futureWeftEdges:
                                fwn = (futureweft[1], self.node[futureweft[1]])
                                if (fwn[1]["position"] == target_position and
                                    fwn[1]["num"] == start_of_window[1]["num"]):
                                    # if the start of the window is found,
                                    # it is the only possible connection
                                    filteredWeftEdges = [futureweft]
                                    break
                                if (fwn[1]["position"] == target_position and
                                    fwn[1]["num"] > start_of_window[1]["num"]):
                                    filteredWeftEdges.append(futureweft)
                                else:
                                    continue
                            if (not filteredWeftEdges or
                                len(filteredWeftEdges) == 0):
                                end_of_window = None
                                continue

                            # sort the filtered weft edges based on the 'num'
                            # attribute of their target node
                            filteredWeftEdges.sort(
                                        key=lambda x: self.node[x[1]]["num"])

                            # get the end of the window from the first edge on
                            # the target position
                            end_of_window = (filteredWeftEdges[0][1],
                                             self.node[filteredWeftEdges[0][1]])

                            break
                    else:
                        end_of_window = None

                    # define the window
                    if end_of_window == None:
                        window = [start_of_window]
                    elif end_of_window == start_of_window:
                        window = [start_of_window]
                    else:
                        window = [(n, d) for n, d \
                                  in self.nodes_iter(data=True) \
                                  if n >= start_of_window[0] \
                                  and n <= end_of_window[0]]

                    if len(window) == 0:
                        # print info on verbose setting
                        v_print("Length of window is 0, skipping...")
                    elif len(window) == 1:
                        # print info on verbose setting
                        v_print("Window has only one node.")
                        v_print("Connecting to node {}".format(window[0][0]) +
                                " on position {}...".format(
                                                      window[0][1]["position"]))

                        # connect weft edge
                        if node[1]["position"] < window[0][1]["position"]:
                            self.create_weft_edge(node, window[0])
                        else:
                            self.create_weft_edge(window[0], node)
                    else:
                        # print info on verbose setting
                        v_print("Processing window nodes: {}".format(
                                                        [w[0] for w in window]))

                        # sort nodes in window by distance
                        if precise:
                            allDists = [thisPt.DistanceTo(pc[1]["geo"]) \
                                        for pc in window]
                        else:
                            allDists = [thisPt.DistanceToSquared(pc[1]["geo"]) \
                                        for pc in window]
                        allDists, window = zip(*sorted(zip(allDists, window),
                                               key = itemgetter(0)))

                        if least_connected:
                            wn_count = [len(self[n[0]]) for n in window]
                            wn_count, allDists, window = zip(
                                    *sorted(zip(allDists, wn_count, window),
                                            key = itemgetter(0, 1)))
                            # set final candidate node
                            fCand = window[0]
                        else:
                            # get the contours current direction
                            if k < len(initial_nodes)-1:
                                contourDir = RhinoLine(
                                        thisPt,
                                        initial_nodes[k+1][1]["geo"]).Direction
                            elif k == len(initial_nodes)-1:
                                contourDir = RhinoLine(
                                        initial_nodes[k-1][1]["geo"],
                                        thisPt).Direction
                            contourDir.Unitize()

                            # get the directions of the possible connections
                            candidatePoints = [pc[1]["geo"] \
                                               for pc in window]
                            candidateDirections = [RhinoLine(
                                                    thisPt, cp).Direction \
                                                    for cp in candidatePoints]
                            [cd.Unitize() for cd in candidateDirections]

                            # get the angles between contour dir and window dir
                            normals = [RhinoVector3d.CrossProduct(
                                       contourDir, cd) \
                                       for cd in candidateDirections]
                            angles = [RhinoVector3d.VectorAngle(
                                      contourDir, cd, n) for cd, n in zip(
                                                candidateDirections, normals)]

                            # compute deltas as a mesaure of perpendicularity
                            deltas = [abs(a - (0.5 * pi)) for a in angles]

                            # sort window by distance, then by delta
                            allDists, deltas, most_perpendicular = zip(*sorted(
                                        zip(allDists,
                                            deltas,
                                            window),
                                            key = itemgetter(0, 1)))
                            # set final candidate node for connection
                            fCand = most_perpendicular[0]

                        # print info on verbose setting
                        v_print("Connecting to node " +
                                "{} on position {}...".format(
                                                        fCand[0],
                                                        fCand[1]["position"]))

                        # connect weft edge to best target
                        if node[1]["position"] < fCand[1]["position"]:
                            self.create_weft_edge(node, fCand)
                        else:
                            self.create_weft_edge(fCand, node)

    def initialize_weft_edges(self, start_index=None, propagate_from_center=False, force_continuous_start=False, force_continuous_end=False, max_connections=4, least_connected=False, precise=False, verbose=False):
        """
        Attempts to create all the preliminary 'weft' connections for the
        network.

        Parameters
        ----------
        start_index : int, optional
            This value defines at which index the list of contours is split.
            If no index is supplied, will split the list at the longest contour.

            Defaults to ``None``.

        propagate_from_center : bool, optional
            If ``True``, will propagate left and right set of contours from
            the center contour defined by start_index or the longest contour
            ( < | > ). Otherwise, the propagation of the contours left to the
            center will start at the left boundary ( > | > ).

            Defaults to ``False``

        force_continuous_start : bool, optional
            If ``True``, forces the first row of stitches to be continuous.

            Defaults to ``False``.

        force_continuous_end : bool, optional
            If ``True``, forces the last row of stitches to be continuous.

            Defaults to ``False``.

        max_connections : int, optional
            The maximum connections a node is allowed to have to be considered
            for an additional 'weft' connection.

            Defaults to ``4``.

        least_connected : bool, optional
            If ``True``, uses the least connected node from the found
            candidates.

            Defaults to ``False``

        precise : bool, optional
            If ``True``, the distance between nodes will be calculated using the
            Rhino.Geometry.Point3d.DistanceTo method, otherwise the much faster
            Rhino.Geometry.Point3d.DistanceToSquared method is used.

            Defaults to ``False``.

        verbose : bool, optional
            If ``True``, this routine and all its subroutines will print
            messages about what is happening to the console. Great for debugging
            and analysis.

            Defaults to ``False``.

        Raises
        ------
        KnitNetworkError
            If the supplied splitting index is too high.

        Notes
        -----
        Closely resembles the implementation described in Automated Generation
        of Knit Patterns for Non-developable Surfaces* [1]_. Also see *KnitCrete
        - Stay-in-place knitted formworks for complex concrete structures* [2]_.
        """

        # get all the positions / contours
        AllPositions = self.all_nodes_by_position(data=True)

        if start_index == None:
            # get index of longest contour
            start_index = self.longest_position_contour()[0]
        elif start_index >= len(AllPositions):
            raise KnitNetworkError("Supplied splitting index is too high!")

        # if continuous start is True, connect the whole first row
        if force_continuous_start:
            chain = [pos[1] for pos in AllPositions]
            for pair in pairwise(chain):
                self.create_weft_edge(pair[0], pair[1])
        # if continuous end is True, connect the whole last row
        if force_continuous_end:
            chain = [pos[-2] for pos in AllPositions]
            for pair in pairwise(chain):
                self.create_weft_edge(pair[0], pair[1])

        # split position list into two sets based on start index
        leftContours = AllPositions[0:start_index+1]
        # optional propagation from center
        # NOTE: this has shown problems / weird stitch geometries
        if propagate_from_center:
            leftContours.reverse()

        rightContours = AllPositions[start_index:]

        # create the initial weft connections
        self._create_initial_weft_connections(
                            leftContours,
                            force_continuous_start=force_continuous_start,
                            force_continuous_end=force_continuous_end,
                            max_connections=max_connections,
                            precise=precise,
                            verbose=verbose)

        self._create_initial_weft_connections(
                            rightContours,
                            force_continuous_start=force_continuous_start,
                            force_continuous_end=force_continuous_end,
                            max_connections=max_connections,
                            precise=precise,
                            verbose=verbose)

        # create second pass weft connections
        self._create_second_pass_weft_connections(
                                            leftContours,
                                            least_connected,
                                            precise=precise,
                                            verbose=verbose)

        self._create_second_pass_weft_connections(
                                            rightContours,
                                            least_connected,
                                            precise=precise,
                                            verbose=verbose)

        return True

    # INITIALIZATION OF PRELIMINARY 'WARP' EDGES -------------------------------

    def initialize_warp_edges(self, contour_set=None, verbose=False):
        """
        Method for initializing first 'warp' connections once all preliminary
        'weft' connections are made.

        Parameters
        ----------
        contour_set : :obj:`list`, optional
            List of lists of nodes to initialize 'warp' edges. If none are
            supplied, all nodes ordered by thei 'position' attributes are
            used.

            Defaults to ``None``.

        verbose : bool, optional
            If ``True``, will print verbose output to the console.

            Defaults to ``False``.

        Notes
        -----
        Closely resembles the implementation described in Automated Generation
        of Knit Patterns for Non-developable Surfaces* [1]_. Also see *KnitCrete
        - Stay-in-place knitted formworks for complex concrete structures* [2]_.
        """

        # if no contour set is provided, use all contours of this network
        if contour_set == None:
            contour_set = self.all_nodes_by_position(data=True)

        # loop through all positions in the set of contours
        for i, pos in enumerate(contour_set):
            # get all nodes on current contour
            initial_nodes = contour_set[i]

            # loop through all nodes on this contour
            for k, node in enumerate(initial_nodes):
                connected_edges = self.edges(node[0], data=True)
                numweft = len(self.node_weft_edges(node[0]))
                if (len(connected_edges) > 4 or numweft > 2 \
                    or i == 0 or i == len(contour_set)-1):
                    # set 'end' attribute for this node
                    self.node[node[0]]["end"] = True

                    # loop through all candidate edges
                    for j, edge in enumerate(connected_edges):
                        # if it's not a 'weft' edge, assign attributes
                        if not edge[2]["weft"]:
                            connected_node = edge[1]
                            # set 'end' attribute to conneted node
                            self.node[connected_node]["end"] = True
                            # set 'warp' attribute to current edge
                            self[edge[0]][edge[1]]["warp"] = True

    # ASSIGNING OF 'SEGMENT' ATTRIBUTES FOR MAPPING NETWORK --------------------

    def _traverse_weft_edge_until_end(self, start_end_node, start_node, seen_segments, way_nodes=None, way_edges=None, end_nodes=None):
        """
        Private method for traversing a path of 'weft' edges until another
        'end' node is discoverd.
        """

        # initialize output lists
        if way_nodes == None:
            way_nodes = deque()
            way_nodes.append(start_node[0])
        if way_edges == None:
            way_edges = deque()
        if end_nodes == None:
            end_nodes = deque()

        # get the connected edges and filter them, sort out the ones that
        # already have a 'segment' attribute assigned
        connected_weft_edges = self.node_weft_edges(start_node[0], data=True)
        filtered_weft_edges = []
        for cwe in connected_weft_edges:
            if cwe[2]["segment"] != None:
                continue
            if cwe in way_edges:
                continue
            elif (cwe[1], cwe[0], cwe[2]) in way_edges:
                continue
            filtered_weft_edges.append(cwe)

        if len(filtered_weft_edges) > 1:
            print(filtered_weft_edges)
            print("More than one filtered candidate weft edge! " +
                  "Segment complete...?")
        elif len(filtered_weft_edges) == 1:
            fwec = filtered_weft_edges[0]
            connected_node = (fwec[1], self.node[fwec[1]])

            # if the connected node is an end node, the segment is finished
            if connected_node[1]["end"]:
                # find out which order to set segment attributes
                if start_end_node > connected_node[0]:
                    segStart = connected_node[0]
                    segEnd = start_end_node
                else:
                    segStart = start_end_node
                    segEnd = connected_node[0]
                if (segStart, segEnd) in seen_segments:
                    segIndex = len([s for s in seen_segments \
                                    if s == (segStart, segEnd)])
                else:
                    segIndex = 0
                # append the relevant data to the lists
                end_nodes.append(connected_node[0])
                way_edges.append(fwec)
                seen_segments.append((segStart, segEnd))
                # set final 'segment' attributes to all the way nodes
                for waynode in way_nodes:
                    self.node[waynode]["segment"] = (segStart,
                                                     segEnd,
                                                     segIndex)
                # set final 'segment' attributes to all the way edges
                for wayedge in way_edges:
                    self[wayedge[0]][wayedge[1]]["segment"] = (segStart,
                                                               segEnd,
                                                               segIndex)
                # return the seen segments
                return seen_segments
            else:
                # set the initial segment attribute to the node
                self.node[connected_node[0]]["segment"] = (start_end_node,
                                                           None,
                                                           None)

                # set the initial segment attribute to the edge
                self[fwec[0]][fwec[1]]["segment"] = (start_end_node,
                                                     None,
                                                     None)
                # append the relevant data to the lists
                way_nodes.append(connected_node[0])
                way_edges.append(fwec)
                # call this method recursively until a 'end' node is found
                return self._traverse_weft_edge_until_end(
                                                    start_end_node,
                                                    connected_node,
                                                    seen_segments,
                                                    way_nodes,
                                                    way_edges,
                                                    end_nodes)
        else:
            return seen_segments

    def traverse_weft_edges_and_set_attributes(self, start_end_node):
        """
        Traverse a path of 'weft' edges starting from an 'end' node until
        another 'end' node is discovered. Set 'segment' attributes to nodes
        and edges along the way.

        start_end_node : :obj:`tuple`
            2-tuple representing the node to start the traversal.
        """

        # get connected weft edges and sort them by their connected node
        weft_connections = self.node_weft_edges(start_end_node[0], data=True)
        weft_connections.sort(key=lambda x: x[1])

        # loop through all connected weft edges
        seen_segments = []
        for cwe in weft_connections:
            if cwe[2]["segment"]:
                continue

            # check the connected node. if it is an end node,
            # set the respective keys
            connected_node = (cwe[1], self.node[cwe[1]])

            if connected_node[1]["end"]:
                if start_end_node[0] > connected_node[0]:
                    segStart = connected_node[0]
                    segEnd = start_end_node[0]
                else:
                    segStart = start_end_node[0]
                    segEnd = connected_node[0]
                if (segStart, segEnd) in seen_segments:
                    segIndex = len([s for s in seen_segments \
                                    if s == (segStart, segEnd)])
                else:
                    segIndex = 0
                # set the final segment attribute to the edge
                self[cwe[0]][cwe[1]]["segment"] = (segStart, segEnd, segIndex)
                seen_segments.append((segStart, segEnd))

            else:
                seen_segments = self._traverse_weft_edge_until_end(
                                                        start_end_node[0],
                                                        connected_node,
                                                        seen_segments,
                                                        way_edges=[cwe])

    def assign_segment_attributes(self):
        """
        Get the segmentation for loop generation and assign 'segment' attributes
        to 'weft' edges and nodes.
        """

        if len(self.weft_edges) == 0:
            errMsg = ("No 'weft' edges in KnitNetwork! Segmentation " +
                      "is impossible.")
            raise NoWeftEdgesError(errMsg)
        if len(self.end_nodes) == 0:
            errMsg = ("No 'end' nodes in KnitNetwork! Segmentation " +
                      "is impossible.")
            raise NoEndNodesError(errMsg)

        # remove contour and 'warp' edges and store them
        warp_storage = []
        contour_storage = []
        for edge in self.edges(data=True):
            if not edge[2]["weft"]:
                if edge[2]["warp"]:
                    warp_storage.append(edge)
                else:
                    contour_storage.append(edge)
                self.remove_edge(edge[0], edge[1])

        # get all 'end' nodes ordered by their 'position' attribute
        all_ends_by_position = self.all_ends_by_position(data=True)

        # loop through all 'end' nodes
        for position in all_ends_by_position:
            for endnode in position:
                self.traverse_weft_edges_and_set_attributes(endnode)

        # add all previously removed edges back into the network
        [self.add_edge(edge[0], edge[1], attr_dict=edge[2]) \
         for edge in warp_storage + contour_storage]

    # CREATION OF MAPPING NETWORK ----------------------------------------------

    def create_mapping_network(self):
        """
        Creates the corresponding mapping network for the final loop generation
        from a KnitNetwork instance with fully assigned 'segment' attributes.

        The created mapping network will be part of the KnitNetwork instance.
        It can be accessed using the mapping_network property.

        Notes
        -----
        All nodes without an 'end' attribute as well as all 'weft' edges are
        removed by this step. Final nodes as well as final 'weft' and 'warp'
        edges can only be created using the mapping network.

        Returns
        -------
        success : bool
            ``True`` if the mapping network has been successfully created,
            ``False`` otherwise.

        Notes
        -----
        Closely resembles the implementation described in Automated Generation
        of Knit Patterns for Non-developable Surfaces* [1]_. Also see *KnitCrete
        - Stay-in-place knitted formworks for complex concrete structures* [2]_.
        """

        # create a new KnitMappingNetwork instance
        MappingNetwork = KnitMappingNetwork()

        # get all edges of the current network by segment
        weft_edges = sorted(self.weft_edges, key=lambda x: x[2]["segment"])
        warp_edges = self.warp_edges

        # initialize deque container for segment ids
        segment_ids = deque()

        # loop through all 'weft' edges and fill container with unique ids
        for edge in weft_edges:
            segment_id = edge[2]["segment"]
            if not segment_id in segment_ids:
                segment_ids.append(segment_id)

        # error checking
        if len(segment_ids) == 0:
            errMsg = ("The network contains no 'weft' edges with a 'segment' " +
                      "attribute assigned to them. A KnitMappingNetwork can " +
                      "only be created from a KnitNetwork with initialized "+
                      "'weft' edges for courses and corresponding 'warp' " +
                      "edges connecting their 'end' nodes.")
            raise NoWeftEdgesError(errMsg)

        # loop through all unique segment ids
        for id in segment_ids:
            # get the corresponding edges for this id and sort them
            segment_edges = [e for e in weft_edges if e[2]["segment"] == id]
            segment_edges.sort(key=lambda x: x[0])
            # extract start and end nodes
            start_node = (id[0], self.node[id[0]])
            endNode = (id[1], self.node[id[1]])
            # get all the geometry of the individual edges
            segment_geo = [e[2]["geo"] for e in segment_edges]
            # create a segment contour edge in the mapping network
            res = MappingNetwork.create_segment_contour_edge(
                                                        start_node,
                                                        endNode,
                                                        id,
                                                        segment_geo)
            if not res:
                errMsg = ("SegmentContourEdge at segment id {} could not be " +
                          "created!")
                raise KnitNetworkError(errMsg)

        # add all warp edges to the mapping network to avoid lookup hassle
        for warp_edge in warp_edges:
            if warp_edge[0] > warp_edge[1]:
                warp_from =  warp_edge[1]
                warp_to = warp_edge[0]
            else:
                warp_from =  warp_edge[0]
                warp_to = warp_edge[1]
            MappingNetwork.add_edge(warp_from, warp_to, attr_dict=warp_edge[2])

        # set mapping network property for this instance
        self.mapping_network = MappingNetwork

        # ditch all edges that are not 'warp' and nodes without 'end' attribute
        [self.remove_node(n) for n, d in self.nodes_iter(data=True) \
         if not d["end"]]
        [self.remove_edge(s, e) for s, e, d in self.edges_iter(data=True) \
         if not d["warp"]]

        return True

    # MAPPING NETWORK PROPERTY -------------------------------------------------

    def _get_mapping_network(self):
        """
        Gets the associated mapping network for this KnitNetwork instance.
        """

        return self._mapping_network

    def _set_mapping_network(self, mapping_network):
        """
        Setter for this instance's associated mapping network.
        """

        # set mapping network to instance
        if (isinstance(mapping_network, KnitMappingNetwork) \
        or mapping_network == None):
            self._mapping_network = mapping_network
        else:
            raise ValueError("Input is not of type KnitMappingNetwork!")

    mapping_network = property(_get_mapping_network, _set_mapping_network, None,
                              "The associated mapping network of this \
                               KnitNetwork instance.")

    # RETRIEVAL OF NODES AND EDGES FROM MAPPING NETWORK ------------------------

    def all_nodes_by_segment(self, data=False, edges=False):
        """
        Returns all nodes of the network ordered by 'segment' attribute.
        Note: 'end' nodes are not included!

        Parameters
        ----------
        data : bool, optional
            If ``True``, the nodes contained in the output will be represented
            as 2-tuples in the form of (node_identifier, node_data).

            Defaults to ``False``

        edges : bool, optional
            If ``True``, the returned output list will contain 3-tuples in the
            form of (segment_value, segment_nodes, segment_edge).

            Defaults to ``False``.

        Returns
        -------
        nodes_by_segment : :obj:`list` of :obj:`tuple`
            List of 2-tuples in the form of (segment_value, segment_nodes) or
            3-tuples in the form of (segment_value, segment_nodes, segment_edge)
            depending on the ``edges`` argument.

        Raises
        ------
        MappingNetworkError
            If the mapping network is not available for this instance.
        """

        # retrieve mappingnetwork
        mapnet = self.mapping_network
        if not mapnet:
            errMsg = ("Mapping network has not been built for this instance!")
            raise MappingNetworkError(errMsg)

        allSegments = mapnet.segment_contour_edges
        allSegmentNodes = [(n, d) for n, d \
                           in self.nodes_iter(data=True) if d["segment"]]

        segdict = {}
        for n in allSegmentNodes:
            if n[1]["segment"] not in segdict:
                segdict[n[1]["segment"]] = [n]
            else:
                segdict[n[1]["segment"]].append(n)

        anbs = []
        if data and edges:
            for segment in allSegments:
                segval = segment[2]["segment"]
                try:
                    segnodes = sorted(segdict[segval])
                except KeyError:
                    segnodes = []
                anbs.append((segval, segnodes, segment))
        elif data and not edges:
            for segment in allSegments:
                segval = segment[2]["segment"]
                try:
                    segnodes = sorted(segdict[segval])
                except KeyError:
                    segnodes = []
                anbs.append((segval, segnodes))
        elif not data and edges:
            for segment in allSegments:
                segval = segment[2]["segment"]
                try:
                    segnodes = sorted(segdict[segval])
                except KeyError:
                    segnodes = []
                anbs.append((segval, [sn[0] for sn in segnodes], segment))
        elif not data and not edges:
            for segment in allSegments:
                segval = segment[2]["segment"]
                try:
                    segnodes = sorted(segdict[segval])
                except KeyError:
                    segnodes = []
                anbs.append((segval, [sn[0] for sn in segnodes]))

        return anbs

    # STITCH WIDTH SAMPLING ----------------------------------------------------

    def sample_segment_contours(self, stitch_width):
        """
        Samples the segment contours of the mapping network with the given
        stitch width. The resulting points are added to the network as nodes
        and a 'segment' attribute is assigned to them based on their origin
        segment contour edge.

        Parameters
        ----------

        stitch_width : float
            The width of a single stitch inside the knit.

        Raises
        ------
        MappingNetworkError
            If the mapping network is not available for this instance.

        Notes
        -----
        Closely resembles the implementation described in Automated Generation
        of Knit Patterns for Non-developable Surfaces* [1]_. Also see *KnitCrete
        - Stay-in-place knitted formworks for complex concrete structures* [2]_.
        """

        # retrieve mapping network
        mapnet = self.mapping_network
        if not mapnet:
            errMsg = ("Mapping network has not been built for this instance, " +
                      "sampling segment contours is impossible!")
            raise MappingNetworkError(errMsg)

        # get the highest index of all the nodes in the network
        maxNode = max(self.nodes())

        # get all the segment geometry ordered by segment number
        segment_contours = mapnet.segment_contour_edges

        # sample all segments with the stitch width
        nodeindex = maxNode + 1
        newPts = []
        for i, seg in enumerate(segment_contours):
            # get the geometry of the contour and reparametreize its domain
            geo = seg[2]["geo"]
            geo = geo.ToPolylineCurve()
            geo.Domain = RhinoInterval(0.0, 1.0)

            # compute the division points
            crvlen = geo.GetLength()
            density = int(round(crvlen / stitch_width))
            if density == 0:
                continue
            divT = geo.DivideByCount(density, False)
            divPts = [geo.PointAt(t) for t in divT]

            # set leaf attribute
            if self.node[seg[0]]["leaf"] and self.node[seg[1]]["leaf"]:
                nodeLeaf = True
            else:
                nodeLeaf = False

            # add all the nodes to the network
            for j, pt in enumerate(divPts):
                # add node to network
                self.node_from_point3d(
                                    nodeindex,
                                    pt,
                                    position=None,
                                    num=j,
                                    leaf=nodeLeaf,
                                    start=False,
                                    end=False,
                                    segment=seg[2]["segment"],
                                    increase=False,
                                    decrease=False,
                                    color = None)
                # increment node index
                nodeindex += 1

    # CREATION OF FINAL 'WEFT' CONNECTIONS -------------------------------------

    def create_final_weft_connections(self):
        """
        Loop through all the segment contour edges and create all 'weft'
        connections for this network.

        Notes
        -----
        Closely resembles the implementation described in Automated Generation
        of Knit Patterns for Non-developable Surfaces* [1]_. Also see *KnitCrete
        - Stay-in-place knitted formworks for complex concrete structures* [2]_.
        """

        # get all nodes by segment contour
        SegmentValues, AllNodesBySegment = zip(*self.all_nodes_by_segment(
                                                                    data=True))

        # loop through all the segment contours
        for i, segment in enumerate(AllNodesBySegment):
            segval = SegmentValues[i]
            firstNode = (segval[0], self.node[segval[0]])
            lastNode = (segval[1], self.node[segval[1]])

            if len(segment) == 0:
                self.create_weft_edge(firstNode, lastNode, segval)
            elif len(segment) == 1:
                self.create_weft_edge(firstNode, segment[0], segval)
                self.create_weft_edge(segment[0], lastNode, segval)
            else:
                # loop through all nodes on the current segment and create
                # the final 'weft' edges
                for j, node in enumerate(segment):
                    if j == 0:
                        self.create_weft_edge(firstNode, node, segval)
                        self.create_weft_edge(node, segment[j+1], segval)
                    elif j < len(segment)-1:
                        self.create_weft_edge(node, segment[j+1], segval)
                    elif j == len(segment)-1:
                        self.create_weft_edge(node, lastNode, segval)

    # CREATION OF FINAL 'WARP' CONNECTIONS -------------------------------------

    def attempt_warp_connection(self, node, candidate, source_nodes, max_connections=4, verbose=False):
        """
        Method for attempting a 'warp' connection to a candidate
        node based on certain parameters.

        Parameters
        ----------
        node : node
            The starting node for the possible 'weft' edge.

        candidate : node
            The target node for the possible 'weft' edge.

        source_nodes : :obj:`list`
            List of nodes on the position contour of node. Used to check if
            the candidate node already has a connection.

        max_connections : int, optional
            The new 'weft' connection will only be made if the candidate nodes
            number of connected neighbors is below this.

            Defaults to ``4``.

        verbose : bool, optional
            If ``True``, this routine and all its subroutines will print
            messages about what is happening to the console.

            Defaults to ``False``.

        Returns
        -------
        result : bool
            True if the connection has been made, otherwise false.

        Notes
        -----
        Closely resembles the implementation described in Automated Generation
        of Knit Patterns for Non-developable Surfaces* [1]_. Also see *KnitCrete
        - Stay-in-place knitted formworks for complex concrete structures* [2]_.
        """

        # define verbose print function
        v_print = print if verbose else lambda *a, **k: None

        connecting_neighbors = self[candidate[0]]
        if len(connecting_neighbors) < max_connections:
            isConnected = False
            for cn in connecting_neighbors:
                if cn in [v[0] for v in source_nodes]:
                    isConnected = True
                    # print info on verbose setting
                    v_print("Candidate node {} is ".format(candidate[0]) +
                            "already connected! Skipping to next node...")
                    break
            if not isConnected:
                # print info on verbose setting
                v_print("Connecting node {} to best candidate {}.".format(
                                                                node[0],
                                                                candidate[0]))
                # finally create the warp edge for good
                self.create_warp_edge(node, candidate)
                return True
            else:
                return False
        else:
            return False

    def _create_initial_warp_connections(self, segment_pair, max_connections=4, precise=False, verbose=False):
        """
        Private method for creating first pass 'warp' connections for the
        supplied pair of segment chains.
        The pair is only defined as a list of nodes, the nodes have to be
        supplied with their attribute data!

        Notes
        -----
        Closely resembles the implementation described in Automated Generation
        of Knit Patterns for Non-developable Surfaces* [1]_. Also see *KnitCrete
        - Stay-in-place knitted formworks for complex concrete structures* [2]_.
        """

        # define verbose print function
        v_print = print if verbose else lambda *a, **k: None

        if len(segment_pair) < 2:
            v_print("Not enough contour segments in supplied set!")
            return

        # print info on verbose output
        v_print("Creating initial 'warp' connections for contour set...")

        # get initial and target nodes without 'end' nodes
        initial_nodes = segment_pair[0]
        target_nodes = segment_pair[1]

        # define forbidden node index
        forbidden_node = -1

        # do nothing if one of the sets is empty
        if len(initial_nodes) == 0 or len(target_nodes) == 0:
            return

        # loop through all nodes on the current segment
        for k, node in enumerate(initial_nodes):
            # get geometry from current node
            thisPt = node[1]["geo"]

            # print info on verbose setting
            v_print("Processing node {} on segment {}:".format(
                                                            node[0],
                                                            node[1]["segment"]))

            # filtering according to forbidden nodes
            if forbidden_node != -1:
                target_nodes = [tnode for tx, tnode in enumerate(target_nodes) \
                                if tx >= target_nodes.index(forbidden_node)]
            if len(target_nodes) == 0:
                continue

            # compute distances to target nodes
            if precise:
                allDists = [thisPt.DistanceTo(tn[1]["geo"]) \
                            for tn in target_nodes]
            else:
                allDists = [thisPt.DistanceToSquared(tn[1]["geo"]) \
                            for tn in target_nodes]

            # sort nodes after distances
            allDists, sorted_target_nodes = zip(*sorted(
                                                zip(allDists, target_nodes),
                                                key = itemgetter(0)))

            # the four nearest nodes are the possible connections
            possible_connections = sorted_target_nodes[:4]
            # print info on verbose setting
            v_print("Possible connections: {}".format([pc[0] for pc in \
                                                       possible_connections]))

            # handle edge case where there is no possible connection or just one
            if len(possible_connections) == 0:
                continue
            elif len(possible_connections) == 1:
                # attempt to connect to only possible candidate
                fCand = possible_connections[0]
                res = self.attempt_warp_connection(
                                                node,
                                                fCand,
                                                initial_nodes,
                                                max_connections=max_connections,
                                                verbose=verbose)
                # set forbidden node
                if res:
                    forbidden_node = fCand
                continue

            # get the segment contours current direction
            if k < len(initial_nodes)-1:
                contourDir = RhinoLine(thisPt,
                                         initial_nodes[k+1][1]["geo"]).Direction
            elif k == len(initial_nodes)-1:
                contourDir = RhinoLine(
                                 initial_nodes[k-1][1]["geo"], thisPt).Direction
            contourDir.Unitize()

            # get the directions of the possible connections
            candidatePoints = [pc[1]["geo"] for pc in possible_connections]
            candidateDirections = [RhinoLine(
                                thisPt, cp).Direction for cp in candidatePoints]
            [cd.Unitize() for cd in candidateDirections]

            # get the angles between segment contour dir and possible conn dir
            normals = [RhinoVector3d.CrossProduct(
                                  contourDir, cd) for cd in candidateDirections]
            angles = [RhinoVector3d.VectorAngle(
                      contourDir, cd, n) for cd, n in zip(
                      candidateDirections, normals)]

            # compute deltas as a measure of perpendicularity
            deltas = [abs(a - (0.5 * pi)) for a in angles]

            # sort possible connections first by distance, then by delta
            allDists, \
            deltas, \
            angles, \
            most_perpendicular = zip(*sorted(
                                            zip(
                                                allDists,
                                                deltas,
                                                angles,
                                                possible_connections[:]),
                                            key = itemgetter(0, 1)))

            # compute angle difference
            aDelta = angles[0] - angles[1]

            # get node neighbors
            nNeighbors = self[node[0]]

            # CONNECTION FOR LEAST ANGLE CHANGE --------------------------------
            if len(nNeighbors) > 2 and aDelta < radians(6.0):
                # print info on verbose setting
                v_print("Using procedure for least angle " +
                        "change connection...")

                # get previous connected edge and its direction
                prevEdges = self.node_warp_edges(node[0], data=True)
                if len(prevEdges) > 1:
                    print("More than one previous " +
                          "'warp' connection! This was unexpected..." +
                          "Taking the first one..?")
                    prevDir = prevEdges[0][2]["geo"].Direction
                else:
                    prevDir = prevEdges[0][2]["geo"].Direction
                prevDir.Unitize()

                # get directions for the best two candidates
                mpA = most_perpendicular[0]
                mpB = most_perpendicular[1]
                dirA = RhinoLine(thisPt, mpA[1]["geo"]).Direction
                dirB = RhinoLine(thisPt, mpB[1]["geo"]).Direction
                dirA.Unitize()
                dirB.Unitize()

                # get normals for angle measurement
                normalA = RhinoVector3d.CrossProduct(prevDir, dirA)
                normalB = RhinoVector3d.CrossProduct(prevDir, dirB)

                # measure the angles
                angleA = RhinoVector3d.VectorAngle(prevDir, dirA, normalA)
                angleB = RhinoVector3d.VectorAngle(prevDir, dirB, normalB)

                # select final candidate for connection
                if angleA < angleB:
                    fCand = mpA
                else:
                    fCand = mpB

                # attempt connection to final candidate
                res = self.attempt_warp_connection(
                                                node,
                                                fCand,
                                                initial_nodes,
                                                max_connections=max_connections,
                                                verbose=verbose)
                # set forbidden node
                if res:
                    forbidden_node = fCand
                continue

            # CONNECTION FOR MOST PERPENDICULAR --------------------------------
            else:
                # print info on verbose setting
                v_print("Using procedure for most " +
                        "perpendicular connection...")
                # define final candidate node
                fCand = most_perpendicular[0]
                # attempt connection to final candidate
                res = self.attempt_warp_connection(
                                                node,
                                                fCand,
                                                initial_nodes,
                                                max_connections=max_connections,
                                                verbose=verbose)
                # set forbidden node
                if res:
                    forbidden_node = fCand

    def _create_second_pass_warp_connection(self, source_nodes, source_index, window, precise=False, verbose=False, reverse=False):
        """
        Private method for creating second pass 'warp' connections for the
        given set of contours.

        Notes
        -----
        Closely resembles the implementation described in Automated Generation
        of Knit Patterns for Non-developable Surfaces* [1]_. Also see *KnitCrete
        - Stay-in-place knitted formworks for complex concrete structures* [2]_.
        """

        # define verbose print function
        v_print = print if verbose else lambda *a, **k: None

        if len(window) == 0:
            # print info on verbose setting
            v_print("Length of window is 0, skipping...")
        elif len(window) == 1:
            # print info on verbose setting
            v_print("Window has only one node.")
            v_print("Connecting to node {}.".format(window[0][0]))

            # connect 'warp' edge
            if reverse:
                self.create_warp_edge(window[0], source_nodes[source_index])
            else:
                self.create_warp_edge(source_nodes[source_index], window[0])
        else:
            # retrive the point of the current source node
            thisPt = source_nodes[source_index][1]["geo"]

            # print info on verbose setting
            v_print("Processing window nodes: {}".format(
                                                        [w[0] for w in window]))

            # sort nodes in window by distance
            if precise:
                allDists = [thisPt.DistanceTo(pc[1]["geo"]) \
                            for pc in window]
            else:
                allDists = [thisPt.DistanceToSquared(pc[1]["geo"]) \
                            for pc in window]
            allDists, window = zip(*sorted(zip(allDists, window),
                                   key = itemgetter(0)))

            # get the contours current direction
            if source_index < len(source_nodes)-1:
                sourceDir = RhinoLine(thisPt,
                            source_nodes[source_index+1][1]["geo"]).Direction
            elif source_index == len(initial_nodes)-1:
                sourceDir = RhinoLine(source_nodes[source_index-1][1]["geo"],
                                   thisPt).Direction
            sourceDir.Unitize()

            # get the directions of the possible connections
            candidatePoints = [pc[1]["geo"] for pc in window]
            candidateDirections = [RhinoLine(thisPt, cp).Direction for cp \
                                   in candidatePoints]
            [cd.Unitize() for cd in candidateDirections]

            # get the angles between contour dir and window dir
            normals = [RhinoVector3d.CrossProduct(sourceDir, cd) \
                       for cd in candidateDirections]
            angles = [RhinoVector3d.VectorAngle(sourceDir, cd, n) for cd, n \
                      in zip(candidateDirections, normals)]

            # compute deltas as a mesaure of perpendicularity
            deltas = [abs(a - (0.5 * pi)) for a in angles]

            # sort window by distance, then by delta
            allDists, deltas, most_perpendicular = zip(*sorted(
                                                    zip(allDists,
                                                        deltas,
                                                        window),
                                                        key=itemgetter(0, 1)))
            # set final candidate node for connection
            fCand = most_perpendicular[0]

            # print info on verbose setting
            v_print("Connecting to node " +
                    "{} on segment {}...".format(fCand[0],
                                                  fCand[1]["segment"]))

            # connect warp edge to best target
            if reverse:
                self.create_warp_edge(fCand, source_nodes[source_index])
            else:
                self.create_warp_edge(source_nodes[source_index], fCand)

    def create_final_warp_connections(self, max_connections=4, include_end_nodes=True, precise=False, verbose=False):
        """
        Create the final 'warp' connections by building chains of segment
        contour edges and connecting them.

        For each source chain, a target chain is found using an
        'educated guessing' strategy. This means that the possible target chains
        are guessed by leveraging known topology facts about the network and its
        special 'end' nodes.

        Parameters
        ----------
        max_connections : int, optional
            The number of maximum previous connections a candidate node for a
            'warp' connection is allowed to have.

            Defaults to ``4``.

        include_end_nodes : bool, optional
            If ``True``, 'end' nodes between adjacent segment contours in a
            source chain will be included in the first pass of connecting 'warp'
            edges.

            Defaults to ``True``.

        precise : bool
            If ``True``, the distance between nodes will be calculated using the
            Rhino.Geometry.Point3d.DistanceTo method, otherwise the much faster
            Rhino.Geometry.Point3d.DistanceToSquared method is used.

            Defaults to ``False``.

        verbose : bool, optional
            If ``True``, this routine and all its subroutines will print
            messages about what is happening to the console. Great for debugging
            and analysis.

            Defaults to ``False``.

        Notes
        -----
        Closely resembles the implementation described in Automated Generation
        of Knit Patterns for Non-developable Surfaces* [1]_. Also see *KnitCrete
        - Stay-in-place knitted formworks for complex concrete structures* [2]_.
        """

        # define verbose print function
        v_print = print if verbose else lambda *a, **k: None

        # get all segment ids, nodes per segment and edges
        SegmentValues, AllNodesBySegment, SegmentContourEdges = zip(
                        *self.all_nodes_by_segment(data=True, edges=True))

        # build a dictionary of the segments by their index
        SegmentDict = dict(zip(SegmentValues,
                               zip(SegmentContourEdges, AllNodesBySegment)))

        # build source and target chains
        source_chains, target_chain_dict = self.mapping_network.build_chains(
                                                                    False, True)

        # initialize container dict for connected chains
        connected_chains = dict()

        # initialize segment mapping dictionaries
        source_to_target = OrderedDict()
        target_to_source = OrderedDict()

        source_to_key = dict()
        target_to_key = dict()

        # ITERATE OVER SOURCE SEGMENT CHAINS -----------------------------------

        # loop through all source chains and find targets in target chains
        # using an 'educated guess strategy'
        for i, source_chain in enumerate(source_chains):
            # get the first and last node ('end' nodes)
            firstNode = (source_chain[0][0][0],
                         self.node[source_chain[0][0][0]])
            lastNode = (source_chain[0][-1][1],
                        self.node[source_chain[0][-1][1]])
            # get the chain value of the current chain
            chain_value = source_chain[1]
            # extract the ids of the current chain
            current_ids = tuple(source_chain[0])
            # extract the current chains geometry
            current_chain_geo_list = [SegmentDict[id][0][2]["geo"] \
                                      for id in current_ids]
            current_chain_geo = RhinoCurve.JoinCurves([ccg.ToPolylineCurve() \
                                          for ccg in current_chain_geo_list])[0]
            current_chain_spt = current_chain_geo.PointAtNormalizedLength(0.5)
            # retrieve the current segments from the segment dictionary by id
            current_segment_nodes = [SegmentDict[id][1] for id in current_ids]
            # retrieve the current nodes from the list of current segments
            current_nodes = []
            for j, csn in enumerate(current_segment_nodes):
                if include_end_nodes and j > 0:
                    current_nodes.append((current_ids[j][0],
                                          self.node[current_ids[j][0]]))
                [current_nodes.append(n) for n in csn]

            # reset the target key
            target_key = None

            # print info on verbose setting
            v_print("---------------------------------------------------------")
            v_print("Processing segment chain {} ...".format(source_chain))

            # CASE 1 - ENCLOSED SHORT ROW <====> ALL CASES ---------------------

            # look for possible targets using a guess about the chain value
            possible_target_keys = [key for key in target_chain_dict \
                                    if key[0] == chain_value[0] \
                                    and key[1] == chain_value[1] \
                                    and key not in connected_chains]
            if len(possible_target_keys) > 0:
                # find the correct chain by using geometric distance
                possible_target_chains = [target_chain_dict[tk] for tk \
                                          in possible_target_keys]
                # for every chain in the possible target chains, get the
                # geometry and compute a sample distance
                filtered_target_keys = []
                possible_target_chain_dists = []
                for j, ptc in enumerate(possible_target_chains):
                    # retrieve possible target geometry and join into one crv
                    ptc_geo_list = [SegmentDict[id][0][2]["geo"] for id in ptc]
                    if ptc_geo_list == current_chain_geo_list:
                        continue
                    ptc_geo = RhinoCurve.JoinCurves([ptcg.ToPolylineCurve() \
                                                  for ptcg in ptc_geo_list])[0]
                    # get a sample point and measure the distance to the
                    # source chain sample point
                    ptc_spt = ptc_geo.PointAtNormalizedLength(0.5)
                    if precise:
                        ptc_dist = current_chain_spt.DistanceTo(ptc_spt)
                    else:
                        ptc_dist = current_chain_spt.DistanceToSquared(ptc_spt)
                    # append the filtered key to the key list
                    filtered_target_keys.append(possible_target_keys[j])
                    # append the measured distance to the distance list
                    possible_target_chain_dists.append(ptc_dist)
                if len(filtered_target_keys) > 0:
                    # sort filtered target keys using the distances
                    possible_target_chain_dists, filtered_target_keys = zip(*
                                        sorted(zip(possible_target_chain_dists,
                                                   filtered_target_keys),
                                                   key=itemgetter(0)))
                    # set target key
                    target_key = filtered_target_keys[0]
                else:
                    target_key = None
            else:
                target_key = None

            # attempt warp connections if we have found a correct key
            if target_key:
                # get the guessed target chain from the chain dictionary
                target_chain = target_chain_dict[target_key]
                # extract the ids for node retrieval
                target_ids = tuple([seg for seg in target_chain])
                # retrieve the target nodes from the segment dictionary by id
                target_segment_nodes = [SegmentDict[id][1] for id in target_ids]
                target_nodes = []
                for j, tsn in enumerate(target_segment_nodes):
                    if include_end_nodes and j > 0:
                        target_nodes.append((target_ids[j][0],
                                              self.node[target_ids[j][0]]))
                    [target_nodes.append(n) for n in tsn]

                # print info on verbose setting
                v_print("<=====> detected. Connecting to " +
                        "segment chain {}.".format(target_key))

                # we have successfully verified our target segment and
                # can create some warp edges!
                segment_pair = [current_nodes, target_nodes]

                # fill mapping dictionaries
                if current_ids not in source_to_target:
                    source_to_target[current_ids] = target_ids
                if current_ids not in source_to_key:
                    source_to_key[current_ids] = chain_value
                if target_ids not in target_to_source:
                    target_to_source[target_ids] = current_ids
                if target_ids not in target_to_key:
                    target_to_key[target_ids] = target_key

                # create initial warp connections between the chains
                connected_chains[target_key] = True
                self._create_initial_warp_connections(
                                            segment_pair,
                                            max_connections=max_connections,
                                            precise=precise,
                                            verbose=verbose)
                continue

            # CASE 2 - SHORT ROW TO THE RIGHT <=====/ ALL CASES ----------------

            # look for possible targets using a guess about the chain value
            possible_target_keys = [key for key in target_chain_dict \
                                    if key[0] == chain_value[0] \
                                    and key[1] == chain_value[1]+1 \
                                    and key not in connected_chains]
            if len(possible_target_keys) == 1:
                target_key = possible_target_keys[0]
            elif len(possible_target_keys) > 1:
                # find the correct chain by using geometric distance
                possible_target_chains = [target_chain_dict[tk] for tk \
                                          in possible_target_keys]
                # for every chain in the possible target chains, get the
                # geometry and compute a sample distance
                possible_target_chain_dists = []
                for ptc in possible_target_chains:
                    # retrieve possible target geometry and join into one crv
                    ptc_geo = [SegmentDict[id][0][2]["geo"] for id in ptc]
                    ptc_geo = RhinoCurve.JoinCurves([pg.ToPolylineCurve() \
                                                  for pg in ptc_geo])[0]
                    # get a sample point and measure the distance to the
                    # source chain sample point
                    ptc_spt = ptc_geo.PointAtNormalizedLength(0.5)
                    if precise:
                        ptc_dist = current_chain_spt.DistanceTo(ptc_spt)
                    else:
                        ptc_dist = current_chain_spt.DistanceToSquared(ptc_spt)
                    # append the measured distance to the list
                    possible_target_chain_dists.append(ptc_dist)
                # sort possible target keys using the distances
                possible_target_chain_dists, possible_target_keys = zip(*
                                        sorted(zip(possible_target_chain_dists,
                                                   possible_target_keys),
                                                   key=itemgetter(0)))
                target_key = possible_target_keys[0]
            else:
                target_key = None

            # attempt warp connections if we have found a correct key
            if target_key:
                # get the guessed target chain from the chain dictionary
                target_chain = target_chain_dict[target_key]
                # extract the ids for node retrieval
                target_ids = tuple([seg for seg in target_chain])
                # retrieve the target nodes from the segment dictionary by id
                target_segment_nodes = [SegmentDict[id][1] for id in target_ids]
                target_nodes = []
                for j, tsn in enumerate(target_segment_nodes):
                    if include_end_nodes and j > 0:
                        target_nodes.append((target_ids[j][0],
                                              self.node[target_ids[j][0]]))
                    [target_nodes.append(n) for n in tsn]

                targetFirstNode = target_ids[0][0]
                targetLastNode = target_ids[-1][1]

                # check if firstNode and targetFirstNode are connected via a
                # 'warp' edge to verify
                if (targetFirstNode == firstNode[0] \
                and targetLastNode in self[lastNode[0]]):
                    # print info on verbose setting
                    v_print("<=====/ detected. Connecting " +
                            "to segment {}.".format(target_key))
                    # we have successfully verified our target segment and
                    # can create some warp edges!
                    segment_pair = [current_nodes, target_nodes]
                    connected_chains[target_key] = True

                    # fill mapping dictionaries
                    if current_ids not in source_to_target:
                        source_to_target[current_ids] = target_ids
                    if current_ids not in source_to_key:
                        source_to_key[current_ids] = chain_value
                    if target_ids not in target_to_source:
                        target_to_source[target_ids] = current_ids
                    if target_ids not in target_to_key:
                        target_to_key[target_ids] = target_key

                    # create initial 'warp' connections between the chains
                    self._create_initial_warp_connections(
                                                segment_pair,
                                                max_connections=max_connections,
                                                precise=precise,
                                                verbose=verbose)
                    continue
                else:
                    v_print("No real connection for <=====/. Next case...")

            # CASE 3 - SHORT ROW TO THE LEFT /====> ALL CASES ------------------

            # look for possible targets using a guess about the chain value
            possible_target_keys = [key for key in target_chain_dict \
                                    if key[0] == chain_value[0]+1 \
                                    and key[1] == chain_value[1] \
                                    and key not in connected_chains]
            if len(possible_target_keys) == 1:
                target_key = possible_target_keys[0]
            elif len(possible_target_keys) > 1:
                # find the correct chain by using geometric distance
                possible_target_chains = [target_chain_dict[tk] for tk \
                                          in possible_target_keys]
                # for every chain in the possible target chains, get the
                # geometry and compute a sample distance
                possible_target_chain_dists = []
                for ptc in possible_target_chains:
                    # retrieve possible target geometry and join into one crv
                    ptc_geo = [SegmentDict[id][0][2]["geo"] for id in ptc]
                    ptc_geo = RhinoCurve.JoinCurves([pg.ToPolylineCurve() \
                                                  for pg in ptc_geo])[0]
                    # get a sample point and measure the distance to the
                    # source chain sample point
                    ptc_spt = ptc_geo.PointAtNormalizedLength(0.5)
                    if precise:
                        ptc_dist = current_chain_spt.DistanceTo(ptc_spt)
                    else:
                        ptc_dist = current_chain_spt.DistanceToSquared(ptc_spt)
                    # append the measured distance to the list
                    possible_target_chain_dists.append(ptc_dist)
                # sort possible target keys using the distances
                possible_target_chain_dists, possible_target_keys = zip(*
                                        sorted(zip(possible_target_chain_dists,
                                                   possible_target_keys),
                                                   key=itemgetter(0)))
                target_key = possible_target_keys[0]
            else:
                target_key = None

            # attempt warp connections if we have found a correct key
            if target_key:
                # get the guessed target chain from the chain dictionary
                target_chain = target_chain_dict[target_key]
                # extract the ids for node retrieval
                target_ids = tuple([seg for seg in target_chain])
                # retrieve the target nodes from the segment dictionary by id
                target_segment_nodes = [SegmentDict[id][1] for id in target_ids]
                target_nodes = []
                for j, tsn in enumerate(target_segment_nodes):
                    if include_end_nodes and j > 0:
                        target_nodes.append((target_ids[j][0],
                                              self.node[target_ids[j][0]]))
                    [target_nodes.append(n) for n in tsn]

                targetFirstNode = target_ids[0][0]
                targetLastNode = target_ids[-1][1]

                # check if firstNode and targetFirstNode are connected via a
                # 'warp' edge to verify
                if (targetFirstNode in self[firstNode[0]] \
                and targetLastNode == lastNode[0]):
                    # print info on verbose setting
                    v_print("/=====> detected. Connecting " +
                            "to segment {}.".format(target_key))
                    # we have successfully verified our target segment and
                    # can create some warp edges!
                    segment_pair = [current_nodes, target_nodes]
                    connected_chains[target_key] = True

                    # fill mapping dictionaries
                    if current_ids not in source_to_target:
                        source_to_target[current_ids] = target_ids
                    if current_ids not in source_to_key:
                        source_to_key[current_ids] = chain_value
                    if target_ids not in target_to_source:
                        target_to_source[target_ids] = current_ids
                    if target_ids not in target_to_key:
                        target_to_key[target_ids] = target_key

                    self._create_initial_warp_connections(
                                                segment_pair,
                                                max_connections=max_connections,
                                                precise=precise,
                                                verbose=verbose)
                    continue
                else:
                    v_print("No real connection for /=====>. Next case...")

            # CASE 4 - REGULAR ROW /=====/ ALL CASES ---------------------------

            # look for possible targets using a guess about the chain value
            possible_target_keys = [key for key in target_chain_dict \
                                    if key[0] == chain_value[0]+1 \
                                    and key[1] == chain_value[1]+1 \
                                    and key not in connected_chains]
            if len(possible_target_keys) == 1:
                target_key = possible_target_keys[0]
            elif len(possible_target_keys) > 1:
                # find the correct chain by using geometric distance
                possible_target_chains = [target_chain_dict[tk] for tk \
                                          in possible_target_keys]
                # for every chain in the possible target chains, get the
                # geometry and compute a sample distance
                possible_target_chain_dists = []
                for ptc in possible_target_chains:
                    # retrieve possible target geometry and join into one crv
                    ptc_geo = [SegmentDict[id][0][2]["geo"] for id in ptc]
                    ptc_geo = RhinoCurve.JoinCurves([pg.ToPolylineCurve() \
                                                  for pg in ptc_geo])[0]
                    # get a sample point and measure the distance to the
                    # source chain sample point
                    ptc_spt = ptc_geo.PointAtNormalizedLength(0.5)
                    if precise:
                        ptc_dist = current_chain_spt.DistanceTo(ptc_spt)
                    else:
                        ptc_dist = current_chain_spt.DistanceToSquared(ptc_spt)
                    # append the measured distance to the list
                    possible_target_chain_dists.append(ptc_dist)
                # sort possible target keys using the distances
                possible_target_chain_dists, possible_target_keys = zip(*
                                        sorted(zip(possible_target_chain_dists,
                                                   possible_target_keys),
                                                   key=itemgetter(0)))
                target_key = possible_target_keys[0]
            else:
                target_key = None

            # attempt warp connections if we have found a correct key
            if target_key:
                # get the guessed target chain from the chain dictionary
                target_chain = target_chain_dict[target_key]
                # extract the ids for node retrieval
                target_ids = tuple([seg for seg in target_chain])
                # retrieve the target nodes from the segment dictionary by id
                target_segment_nodes = [SegmentDict[id][1] for id in target_ids]
                target_nodes = []
                for j, tsn in enumerate(target_segment_nodes):
                    if include_end_nodes and j > 0:
                        target_nodes.append((target_ids[j][0],
                                              self.node[target_ids[j][0]]))
                    [target_nodes.append(n) for n in tsn]

                # set target first and last node ('end' nodes)
                targetFirstNode = target_ids[0][0]
                targetLastNode = target_ids[-1][1]

                # check if firstNode and targetFirstNode are connected via a
                # 'warp' edge to verify
                if (targetFirstNode in self[firstNode[0]] \
                and targetLastNode in self[lastNode[0]]):
                    # print info on verbose setting
                    v_print("/=====/ detected. Connecting " +
                            "to segment {}.".format(target_key))
                    # we have successfully verified our target segment and
                    # can create some warp edges!
                    segment_pair = [current_nodes, target_nodes]
                    connected_chains[target_key] = True

                    # fill mapping dictionaries
                    if current_ids not in source_to_target:
                        source_to_target[current_ids] = target_ids
                    if current_ids not in source_to_key:
                        source_to_key[current_ids] = chain_value
                    if target_ids not in target_to_source:
                        target_to_source[target_ids] = current_ids
                    if target_ids not in target_to_key:
                        target_to_key[target_ids] = target_key

                    self._create_initial_warp_connections(
                                                segment_pair,
                                                max_connections=max_connections,
                                                precise=precise,
                                                verbose=verbose)
                    continue
                else:
                    v_print("No real connection for /=====/. No cases match.")

        # INVOKE SECOND PASS FOR SOURCE ---> TARGET ----------------------------
        for i, current_chain in enumerate(source_to_target):
            v_print("---------------------------------------------------------")
            v_print("S>T Current Chain: {}".format(current_chain))
            # build a list of nodes containing all nodes in the current chain
            # including all 'end' nodes
            current_chain_nodes = []
            for j, ccid in enumerate(current_chain):
                current_chain_nodes.append((ccid[0], self.node[ccid[0]]))
                [current_chain_nodes.append(n) for n in SegmentDict[ccid][1]]
            current_chain_nodes.append((current_chain[-1][1],
                                        self.node[current_chain[-1][1]]))

            # retrieve target chain from the source to target mapping
            target_chain = source_to_target[current_chain]

            cckey = source_to_key[current_chain]
            tckey = target_to_key[target_chain]

            # build a list of nodes containing all nodes in the target chain
            # including all 'end' nodes
            target_chain_nodes = []
            for j, tcid in enumerate(target_chain):
                target_chain_nodes.append((tcid[0], self.node[tcid[0]]))
                [target_chain_nodes.append(n) for n in SegmentDict[tcid][1]]
            target_chain_nodes.append((target_chain[-1][1],
                                       self.node[target_chain[-1][1]]))

            # initialize start of window marker
            start_of_window = -1

            # loop through all nodes on the current chain
            for k, node in enumerate(current_chain_nodes):
                # find out if the current node is already principally connected
                node_neighbors = self[node[0]]
                node_connected = False
                # if the node is the first or the last node, it is defined as
                # connected per-se
                if k == 0 or k == len(current_chain_nodes)-1:
                    node_connected = True

                # find out if the current node is already connected to the
                # target chain, get node warp edges and their target nodes
                node_warp_edges = self.node_warp_edges(node[0], data=False)
                warp_edge_targets = [we[1] for we in node_warp_edges]
                # loop over warp edge targets to get the start of the window
                for wet in warp_edge_targets:
                    # loop over target chain nodes
                    for n, tcn in enumerate(target_chain_nodes):
                        # if a warp edge target is in the target chain,
                        # the node is connected and star of window for next
                        # node is defined
                        if wet == tcn[0]:
                            if n > start_of_window or start_of_window == -1:
                                start_of_window = n
                            node_connected = True

                # if the node is not connected to the target chain, we
                # need to find the end of the window
                if not node_connected:
                    v_print("Node: {}".format(node[0]))
                    v_print("Start of window: {}".format(start_of_window))

                    # re-check start of window for <.====/ case
                    if len(target_chain_nodes) >= 2 and start_of_window == -1:
                        if target_chain_nodes[0] == current_chain_nodes[0]:
                            start_of_window = 1
                        else:
                            start_of_window = 0

                    end_of_window = None
                    # loop over target chain nodes
                    for n, tcn in enumerate(target_chain_nodes):
                        if n >= start_of_window:
                            if tcn[0] == current_chain_nodes[-1][0]:
                                end_of_window = n
                            # get all warp edges of the current target node
                            # and their targets
                            tcn_warp_edges = self.node_warp_edges(tcn[0],
                                                                data=False)
                            tcn_warp_edge_targets = [we[1] for we \
                                                     in tcn_warp_edges]
                            # loop over warp edge targets
                            for twet in tcn_warp_edge_targets:
                                if (twet in [cn[0] for cn \
                                             in current_chain_nodes]):
                                    end_of_window = n
                                    break
                        if end_of_window and end_of_window > start_of_window:
                            break

                    # re-check end of window for /====.> case
                    if end_of_window:
                        tcn_we = target_chain_nodes[end_of_window]
                        ccn_end = current_chain_nodes[-1]
                        ccn_len = len(current_chain_nodes)
                        if tcn_we == ccn_end and k == ccn_len-2:
                            end_of_window -= 1
                    if end_of_window < start_of_window:
                        start_of_window = -1
                        end_of_window = None

                    # if we have a valid window, set the target nodes
                    if start_of_window != -1 and end_of_window != None:
                        if end_of_window == len(target_chain_nodes)-1:
                            window = target_chain_nodes[start_of_window:]
                        else:
                            window = target_chain_nodes[start_of_window: \
                                                        end_of_window+1]

                        v_print("End of window: {}".format(end_of_window))

                        # execute connection to target
                        if cckey <= tckey:
                            rev = False
                        else:
                            rev = True

                        v_print("Connecting chain {} to chain {}".format(
                                                                    cckey,
                                                                    tckey))

                        self._create_second_pass_warp_connection(
                                                            current_chain_nodes,
                                                            k,
                                                            window,
                                                            precise=precise,
                                                            verbose=verbose,
                                                            reverse=rev)
                    else:
                        # print info on verbose setting
                        v_print("No valid window for current chain!")

        # INVOKE SECOND PASS FOR TARGET ---> SOURCE ----------------------------
        for i, current_chain in enumerate(target_to_source):
            v_print("---------------------------------------------------------")
            v_print("T>S Current Chain: {}".format(current_chain))

            # build a list of nodes containing all nodes in the current chain
            # including all 'end' nodes
            current_chain_nodes = []
            for j, ccid in enumerate(current_chain):
                current_chain_nodes.append((ccid[0], self.node[ccid[0]]))
                [current_chain_nodes.append(n) for n in SegmentDict[ccid][1]]
            current_chain_nodes.append((current_chain[-1][1],
                                        self.node[current_chain[-1][1]]))

            # retrieve target chain from the source to target mapping
            target_chain = target_to_source[current_chain]

            cckey = target_to_key[current_chain]
            tckey = source_to_key[target_chain]

            # build a list of nodes containing all nodes in the target chain
            # including all 'end' nodes
            target_chain_nodes = []
            for j, tcid in enumerate(target_chain):
                target_chain_nodes.append((tcid[0], self.node[tcid[0]]))
                [target_chain_nodes.append(n) for n in SegmentDict[tcid][1]]
            target_chain_nodes.append((target_chain[-1][1],
                                       self.node[target_chain[-1][1]]))

            # initialize start of window marker
            start_of_window = -1

            # loop through all nodes on the current chain
            for k, node in enumerate(current_chain_nodes):
                # find out if the current node is already principally connected
                node_neighbors = self[node[0]]
                node_connected = False
                if k == 0 or k == len(current_chain_nodes)-1:
                    node_connected = True

                # find out if the current node is already connected to the
                # target chain
                node_warp_edges = self.node_warp_edges(node[0], data=False)
                warp_edge_targets = [we[1] for we in node_warp_edges]
                # loop over weft edge targets
                for wet in warp_edge_targets:
                    # if warp edge target  is in target chain nodes, node
                    # is connected and the start of our window for the next node
                    for n, tcn in enumerate(target_chain_nodes):
                        if wet == tcn[0]:
                            if n > start_of_window or start_of_window == -1:
                                start_of_window = n
                            node_connected = True

                # if the node is not connected to the target chain, we
                # need to find the end of the window
                if not node_connected:
                    # print info on verbose output
                    v_print("Node: {}".format(node[0]))
                    v_print("Start of window: {}".format(start_of_window))

                    # re-check start of window for <.====/ case
                    if len(target_chain_nodes) >= 2 and start_of_window == -1:
                        if target_chain_nodes[0] == current_chain_nodes[0]:
                            start_of_window = 1
                        else:
                            start_of_window = 0

                    end_of_window = None
                    # loop over target chain nodes
                    for n, tcn in enumerate(target_chain_nodes):
                        if n >= start_of_window:
                            if tcn[0] == current_chain_nodes[-1][0]:
                                end_of_window = n
                            # get all warp edges of the current target node and
                            # their targets
                            tcn_warp_edges = self.node_warp_edges(tcn[0],
                                                                data=False)
                            tcn_warp_edge_targets = [we[1] for we \
                                                     in tcn_warp_edges]
                            # loop over warp edge targets of current target node
                            for twet in tcn_warp_edge_targets:
                                # if warp edge target is in current chain,
                                # it is the end of the window
                                if (twet in [cn[0] for cn \
                                             in current_chain_nodes]):
                                    end_of_window = n
                                    break
                        if end_of_window and end_of_window > start_of_window:
                            break

                    # re-check end of window for /====.> case
                    if end_of_window:
                        tcn_we = target_chain_nodes[end_of_window]
                        ccn_end = current_chain_nodes[-1]
                        ccn_len = len(current_chain_nodes)
                        if tcn_we == ccn_end and k == ccn_len-2:
                            end_of_window -= 1
                    if end_of_window < start_of_window:
                        start_of_window = -1
                        end_of_window = None

                    # if there is a valid window, set the target chain nodes
                    if start_of_window != -1 and end_of_window != None:
                        if end_of_window == len(target_chain_nodes)-1:
                            window = target_chain_nodes[start_of_window:]
                        else:
                            window = target_chain_nodes[start_of_window: \
                                                        end_of_window+1]

                        # print info on verbose output
                        v_print("End of window: {}".format(end_of_window))

                        # execute connection
                        if cckey < tckey:
                            rev = False
                        else:
                            rev = True

                        v_print("Connecting chain {} to chain {}.".format(
                                                                        cckey,
                                                                        tckey))

                        self._create_second_pass_warp_connection(
                                                            current_chain_nodes,
                                                            k,
                                                            window,
                                                            precise=precise,
                                                            verbose=verbose,
                                                            reverse=rev)
                    else:
                        v_print("No valid window for current chain!")

    # FIND FACES OF NETWORK ----------------------------------------------------

    def to_KnitDiNetwork(self):
        """
        Constructs and returns a directed KnitDiNetwork based on this network
        by duplicating all edges so that [u -> v] and [v -> u] for every
        edge [u - v] in this undirected network.

        Returns
        -------
        directed_network : :class:`KnitDiNetwork`
            The directed representation of this network.
        """

        # create a directed network with duplicate edges in opposing directions
        dirnet = KnitDiNetwork()

        dirnet.name = self.name
        dirnet.add_nodes_from(self)
        dirnet.add_edges_from( (u, v, data)
                                for u, nbrs in self.adjacency_iter()
                                for v, data in nbrs.items() )
        dirnet.graph = self.graph
        dirnet.node = self.node
        dirnet.mapping_network = self.mapping_network

        return dirnet

    def find_cycles(self, mode=-1):
        """
        Finds the cycles (faces) of this network by utilizing a wall-follower
        mechanism.

        Parameters
        ----------
        mode : int, optional
            Determines how the neighbors of each node are sorted when finding
            cycles for the network.
            ``-1`` equals to using the world XY plane.

            ``0`` equals to using a plane normal to the origin nodes closest
            point on the reference geometry.

            ``1`` equals to using a plane normal to the average of the origin
            and neighbor nodes' closest points on the reference geometry.

            ``2`` equals to using an average plane between a plane fit to the
            origin and its neighbor nodes and a plane normal to the origin
            nodes closest point on the reference geometry.

            Defaults to ``-1``.

        Warning
        -------
        Modes other than ``-1`` are only possible if this network has an
        underlying reference geometry in form of a Mesh or NurbsSurface. The
        reference geometry should be assigned when initializing the network by
        assigning the geometry to the "reference_geometry" attribute of the
        network.

        Notes
        -----
        Based on an implementation inside the COMPAS framework.
        For more info see [16]_.
        """

        return self.to_KnitDiNetwork().find_cycles(mode=mode)

    def create_mesh(self, mode=-1, max_valence=4):
        """
        Constructs a mesh from this network by finding cycles and using them as
        mesh faces.

        Parameters
        ----------
        mode : int, optional
            Determines how the neighbors of each node are sorted when finding
            cycles for the network.

            ``-1`` equals to using the world XY plane.

            ``0`` equals to using a plane normal to the origin nodes closest
            point on the reference geometry.

            ``1`` equals to using a plane normal to the average of the origin
            and neighbor nodes' closest points on the reference geometry.

            ``2`` equals to using an average plane between a plane fit to the
            origin and its neighbor nodes and a plane normal to the origin
            nodes closest point on the reference geometry.

            Defaults to ``-1``.

        max_valence : int, optional
            Sets the maximum edge valence of the faces. If this is set to > 4,
            n-gon faces (more than 4 edges) are allowed. Otherwise, their cycles
            are treated as invalid and will be ignored.

            Defaults to ``4``.

        Warning
        -------
        Modes other than ``-1`` are only possible if this network has an
        underlying reference geometry in form of a Mesh or NurbsSurface. The
        reference geometry should be assigned when initializing the network by
        assigning the geometry to the "reference_geometry" attribute of the
        network.
        """

        return self.to_KnitDiNetwork().create_mesh(mode=mode,
                                                 max_valence=max_valence)

    # DUALITY ------------------------------------------------------------------

    def create_dual(self, mode=-1, merge_adj_creases=False, mend_trailing_rows=False):
        """
        Creates the dual of this KnitNetwork while translating current edge
        attributes to the edges of the dual network.

        Parameters
        ----------
        mode : int, optional
            Determines how the neighbors of each node are sorted when finding
            cycles for the network.

            ``-1`` equals to using the world XY plane.

            ``0`` equals to using a plane normal to the origin nodes closest
            point on the reference geometry.

            ``1`` equals to using a plane normal to the average of the origin
            and neighbor nodes' closest points on the reference geometry.

            ``2`` equals to using an average plane between a plane fit to the
            origin and its neighbor nodes and a plane normal to the origin
            nodes closest point on the reference geometry.

            Defaults to ``-1``.

        merge_adj_creases : bool, optional
            If ``True``, will merge adjacent 'increase' and 'decrease' nodes
            connected by a 'weft' edge into a single node. This effectively
            simplifies the pattern, as a decrease is unneccessary to perform
            if an increase is right beside it - both nodes can be replaced by a
            single regular node (stitch).

            Defaults to ``False``.

        mend_trailing_rows : bool, optional
            If ``True``, will attempt to mend trailing rows by reconnecting
            nodes.

            Defaults to ``False``.

        Returns
        -------
        dual_network : :class:`KnitDiNetwork`
            The dual network of this KnitNetwork.

        Warning
        -------
        Modes other than -1 (default) are only possible if this network has an
        underlying reference geometry in form of a Mesh or NurbsSurface. The
        reference geometry  should be assigned when initializing the network by
        assigning the geometry to the 'reference_geometry' attribute of the
        network.

        Notes
        -----
        Closely resembles the implementation described in Automated Generation
        of Knit Patterns for Non-developable Surfaces* [1]_. Also see *KnitCrete
        - Stay-in-place knitted formworks for complex concrete structures* [2]_.
        """

        # first find the cycles of this network
        cycles = self.find_cycles(mode=mode)

        # get node data for all nodes once
        node_data = {k: self.node[k] for k in self.nodes_iter()}

        # create new directed KnitDiNetwork for dual network
        DualNetwork = KnitDiNetwork(
                            reference_geometry=self.graph["reference_geometry"])

        # create mapping dict for edges to adjacent cycles
        edge_to_cycle = {(u, v): None for u, v in self.edges_iter()}
        edge_to_cycle.update({(v, u): None for u, v in self.edges_iter()})

        # CREATE NODES OF DUAL -------------------------------------------------

        # for each cycle, find the centroid node
        for ckey in sorted(cycles.keys()):
            cycle = cycles[ckey]
            clen = len(cycle)

            # skip invalid cycles (ngons and self-loops)
            if clen > 4 or clen < 3:
                continue

            # loop over cycle edges and fill mapping dicts
            closed_cycle = cycle[:]
            closed_cycle.append(cycle[0])
            for u, v in pairwise(closed_cycle):
                edge_to_cycle[(u, v)] = ckey

            # get coords of cycle nodes
            cycle_coords = [ [ node_data[k]["x"],
                               node_data[k]["y"],
                               node_data[k]["z"] ] for k in cycle ]

            # compute centroid
            cx, cy, cz = zip(*cycle_coords)
            centroid = [sum(cx) / clen, sum(cy) / clen, sum(cz) / clen]
            centroid_pt = RhinoPoint3d(*centroid)

            # get node 'leaf' attributes
            is_leaf = True in [node_data[k]["leaf"] for k in cycle]

            # get node 'color' attributes. only if all colors of the cycle
            # match, the color attribute will be set!
            colors = [node_data[k]["color"] for k in cycle]
            if all(x == colors[0] for x in colors):
                cycle_color = colors[0]
            else:
                cycle_color = None

            # add node to dual network
            DualNetwork.node_from_point3d(ckey,
                                          centroid_pt,
                                          position=None,
                                          num=None,
                                          leaf=is_leaf,
                                          start=False,
                                          end=False,
                                          segment=None,
                                          increase=False,
                                          decrease=False,
                                          color=cycle_color)

        # CREATE EDGES IN DUAL -------------------------------------------------

        # loop over original edges and create corresponding edges in dual
        for u, v, d in self.edges_iter(data=True):
            u, v = self.edge_geometry_direction(u, v)
            cycle_a = edge_to_cycle[(u, v)]
            cycle_b = edge_to_cycle[(v, u)]
            if cycle_a is not None and cycle_b is not None:
                node_a = (cycle_a, DualNetwork.node[cycle_a])
                node_b = (cycle_b, DualNetwork.node[cycle_b])
                if d["warp"]:
                    DualNetwork.create_weft_edge(node_b, node_a)
                elif d["weft"]:
                    DualNetwork.create_warp_edge(node_a, node_b)

        # SET ATTRIBUTES OF DUAL NODES -----------------------------------------

        # loop over all nodes of the network and set crease and end attributes
        for node in DualNetwork.nodes_iter():
            node_data = DualNetwork.node[node]

            warp_in = DualNetwork.node_warp_edges_in(node)
            warp_out = DualNetwork.node_warp_edges_out(node)
            weft_in = DualNetwork.node_weft_edges_in(node)
            weft_out = DualNetwork.node_weft_edges_out(node)

            warplen = len(warp_in) + len(warp_out)
            weftlen = len(weft_in) + len(weft_out)

            # 2 warp edges and 1 weft edge  >> end
            if warplen == 2 and weftlen == 1:
                node_data["end"] = True
                if weft_out:
                    node_data["start"] = True

            # 1 warp edge and 1 weft edge   >> end and increase / decrease
            elif warplen == 1 and weftlen == 1:
                node_data["end"] = True
                if weft_out:
                    node_data["start"] = True

                if warp_out and not node_data["leaf"]:
                    node_data["increase"] = True
                elif warp_in and not node_data["leaf"]:
                    node_data["decrease"] = True

            # 2 warp edges and 0 weft edges >> end
            elif warplen == 2 and weftlen == 0:
                node_data["end"] = True
                node_data["start"] = True

            # 1 warp edge and 0 weft edges  >> end
            elif warplen == 1 and weftlen == 0:
                node_data["end"] = True
                node_data["start"] = True

            # 0 warp edges and 1 weft edge  >> end
            elif warplen == 0 and weftlen == 1:
                node_data["end"] = True
                if weft_out:
                    node_data["start"] = True

            # 1 warp edge and 2 weft edges  >> increase or decrease
            elif warplen == 1 and weftlen == 2:
                if not node_data["leaf"]:
                    if warp_out:
                        node_data["increase"] = True
                    elif warp_in:
                        node_data["decrease"] = True


        # MERGE ADJACENT INCREASES/DECREASES -----------------------------------

        if merge_adj_creases:
            increase_nodes = [inc for inc in DualNetwork.nodes_iter(data=True) \
                              if inc[1]["increase"]]
            for increase, data in increase_nodes:
                pred = DualNetwork.predecessors(increase)
                suc = DualNetwork.successors(increase)
                pred = [p for p in pred if DualNetwork.node[p]["decrease"]]
                suc = [s for s in suc if DualNetwork.node[s]["decrease"]]
                # merge only with pred or with suc but not both
                if len(pred) == 1 and \
                DualNetwork.edge[pred[0]][increase]["weft"]:
                    # merge nodes, edge is pred, increase
                    pred = pred[0]
                    pd = DualNetwork.node[pred]
                    # remove the connecting edge
                    DualNetwork.remove_edge(pred, increase)
                    # get the points of the nodes
                    increase_pt = data["geo"]
                    pred_pt = pd["geo"]
                    # compute the new merged point
                    new_vec = RhinoVector3d(increase_pt - pred_pt)
                    new_pt = pred_pt + (new_vec * 0.5)
                    # replace the increase with the new pt and invert the
                    # increase attribute
                    data["geo"] = new_pt
                    data["x"] = new_pt.X
                    data["y"] = new_pt.Y
                    data["z"] = new_pt.Z
                    data["increase"] = False
                    # edit the edges of the increase
                    for edge in DualNetwork.edges_iter(increase, data=True):
                        edge[2]["geo"] = RhinoLine(
                                            data["geo"],
                                            DualNetwork.node[edge[1]]["geo"])
                    # edit edges of decrease
                    for edge in DualNetwork.in_edges_iter(pred, data=True):
                        if edge[2]["warp"]:
                            fromNode = (edge[0], DualNetwork.node[edge[0]])
                            toNode = (increase, data)
                            DualNetwork.create_warp_edge(fromNode, toNode)
                            DualNetwork.remove_edge(edge[0], edge[1])
                        elif edge[2]["weft"]:
                            fromNode = (edge[0], DualNetwork.node[edge[0]])
                            toNode = (increase, data)
                            DualNetwork.create_weft_edge(fromNode, toNode)
                            DualNetwork.remove_edge(edge[0], edge[1])
                    DualNetwork.remove_node(pred)
                elif not pred and len(suc) == 1 and \
                DualNetwork.edge[increase][suc[0]]["weft"] :
                    # merge nodes, edge is increase, suc
                    suc = suc[0]
                    sd = DualNetwork.node[suc]
                    # remove the connecting edge
                    DualNetwork.remove_edge(increase, suc)
                    # get the points of the nodes
                    increase_pt = data["geo"]
                    suc_pt = sd["geo"]
                    # compute the new merged point
                    new_vec = RhinoVector3d(suc_pt - increase_pt)
                    new_pt = increase_pt + (new_vec * 0.5)
                    # replace the increase with the new pt and invert the
                    # increase attribute
                    data["geo"] = new_pt
                    data["x"] = new_pt.X
                    data["y"] = new_pt.Y
                    data["z"] = new_pt.Z
                    data["increase"] = False
                    # edit the edges of the increase
                    for edge in DualNetwork.edges_iter(increase, data=True):
                        edge[2]["geo"] = RhinoLine(
                                            data["geo"],
                                            DualNetwork.node[edge[1]]["geo"])
                    for edge in DualNetwork.in_edges_iter(increase, data=True):
                        edge[2]["geo"] = RhinoLine(
                                            DualNetwork.node[edge[0]]["geo"],
                                            data["geo"])
                    # edit incoming edges of decrease
                    for edge in DualNetwork.in_edges_iter(suc, data=True):
                        if edge[2]["warp"]:
                            fromNode = (edge[0], DualNetwork.node[edge[0]])
                            toNode = (increase, data)
                            DualNetwork.create_warp_edge(fromNode, toNode)
                            DualNetwork.remove_edge(edge[0], edge[1])
                        elif edge[2]["weft"]:
                            fromNode = (edge[0], DualNetwork.node[edge[0]])
                            toNode = (increase, data)
                            DualNetwork.create_weft_edge(fromNode, toNode)
                            DualNetwork.remove_edge(edge[0], edge[1])
                    # edit outgoing edges of decrease
                    for edge in DualNetwork.edges_iter(suc, data=True):
                        if edge[2]["warp"]:
                            fromNode = (increase, data)
                            toNode = (edge[1], DualNetwork.node[edge[1]])
                            DualNetwork.create_warp_edge(fromNode, toNode)
                            DualNetwork.remove_edge(edge[0], edge[1])
                        elif edge[2]["weft"]:
                            fromNode = (increase, data)
                            toNode = (edge[1], DualNetwork.node[edge[1]])
                            DualNetwork.create_weft_edge(fromNode, toNode)
                            DualNetwork.remove_edge(edge[0], edge[1])
                    DualNetwork.remove_node(suc)


        # ATTEMPT TO MEND TRAILING ROWS ----------------------------------------

        if mend_trailing_rows:

            # TODO: find a safer / more robust implementation attempt!
            errMsg = "This option is not satisfyingly implemented for this " + \
                     "method, yet. Therefore, it is deactivated for now."
            raise NotImplementedError(errMsg)

            # get all nodes which are 'leaf' and 'end' (right side)
            # and all nodes which are 'leaf' and 'start' (left side)
            trailing = sorted([(n, d) for n, d in \
                              DualNetwork.nodes_iter(data=True) \
                              if d["leaf"] \
                              and d["end"]], key=lambda x: x[0])
            trailing_left = deque([t for t in trailing if t[1]["start"]])
            trailing_right = deque([t for t in trailing if not t[1]["start"]])

            # from the trailing left nodes...
            # travel one outgoing 'weft'
            # from there travel one incoming 'warp'
            # if the resulting node is 'start', 'end' and has 3 edges in total
            # >> take its outgoing 'warp' edge (we already traveled that so
            #    we should already have it)
            # >> connect it to the trailing left node
            # >> remove the 'leaf' attribute from the trailing node as it is no
            #    longer trailing
            # >> add the 'increase' attribute to the previous target of the
            #    'warp' edge

            while len(trailing_left) > 0:
                # pop an item from the deque
                trail = trailing_left.popleft()
                # travel one outgoing 'weft' edge
                weft_out = DualNetwork.node_weft_edges_out(trail[0], data=True)
                if not weft_out:
                    continue
                weft_out = weft_out[0]
                # check the target of the 'weft' edge for incoming 'warp'
                warp_in = DualNetwork.node_warp_edges_in(
                                                        weft_out[1],
                                                        data=True)
                warp_out = DualNetwork.node_warp_edges_out(
                                                        weft_out[1],
                                                        data=True)
                if not warp_in:
                    continue
                warp_in = warp_in[0]
                candidate = (warp_in[0], DualNetwork.node[warp_in[0]])
                nce = len(DualNetwork.in_edges(warp_in[0]))
                nce += len(DualNetwork.edges(warp_in[0]))
                # if this condition holds, we have a trailing increase
                if candidate[1]["start"] and candidate[1]["end"] \
                and nce == 3:
                    # remove found 'warp' edge
                    DualNetwork.remove_edge(warp_in[0], warp_in[1])
                    # assign 'increase' attribute to former 'warp' edge target
                    DualNetwork.node[warp_in[1]]["increase"] = True
                    # connect candidate to trail with new 'warp' edge
                    DualNetwork.create_warp_edge(candidate, trail)
                    # remove 'leaf' attribute of former trail
                    trail[1]["leaf"] = False
                else:
                    if warp_out:
                        warp_out = warp_out[0]
                        candidate = (warp_out[1], DualNetwork.node[warp_out[1]])
                        nce = len(DualNetwork.in_edges(warp_out[1]))
                        nce += len(DualNetwork.edges(warp_out[1]))
                        # if this condition holds, we have a trailing decrease
                        if candidate[1]["start"] and candidate[1]["end"] \
                        and nce == 3:
                            # remove found 'warp' edge
                            DualNetwork.remove_edge(warp_out[0], warp_out[1])
                            # assign 'decrease' attribute to former 'warp'
                            # edge source
                            DualNetwork.node[warp_out[0]]["decrease"] = True
                            # connect former trail to candidate with new
                            # 'warp' edge
                            DualNetwork.create_warp_edge(trail, candidate)
                            # remove 'leaf' attribute of former trail
                            trail[1]["leaf"] = False

            while len(trailing_right) > 0:
                # pop an item from the deque
                trail = trailing_right.popleft()
                # travel one incoming 'weft' edge
                weft_in = DualNetwork.node_weft_edges_in(trail[0], data=True)
                if not weft_in:
                    continue
                weft_in = weft_in[0]
                # check the target of the 'weft' edge for incoming 'warp'
                warp_in = DualNetwork.node_warp_edges_in(weft_in[0], data=True)
                warp_out = DualNetwork.node_warp_edges_out(weft_in[0], data=True)
                if not warp_in:
                    continue
                warp_in = warp_in[0]
                candidate = (warp_in[0], DualNetwork.node[warp_in[0]])
                nce = len(DualNetwork.in_edges(warp_in[0]))
                nce += len(DualNetwork.edges(warp_in[0]))
                # if this condition holds, we have a trailing increase
                if candidate[1]["end"] \
                and nce == 3:
                    # remove found 'warp' edge
                    DualNetwork.remove_edge(warp_in[0], warp_in[1])
                    # assign 'increase' attribute to former 'warp' edge target
                    DualNetwork.node[warp_in[1]]["increase"] = True
                    # connect candidate to trail with new 'warp' edge
                    DualNetwork.create_warp_edge(candidate, trail)
                    # remove 'leaf' attribute of former trail
                    trail[1]["leaf"] = False
                else:
                    if warp_out:
                        warp_out = warp_out[0]
                        candidate = (warp_out[1], DualNetwork.node[warp_out[1]])
                        nce = len(DualNetwork.in_edges(warp_out[1]))
                        nce += len(DualNetwork.edges(warp_out[1]))
                        # if this condition holds, we have a trailing decrease
                        if candidate[1]["start"] and candidate[1]["end"] \
                        and nce == 3:
                            # remove found 'warp' edge
                            DualNetwork.remove_edge(warp_out[0], warp_out[1])
                            # assign 'decrease' attribute to former 'warp'
                            # edge source
                            DualNetwork.node[warp_out[0]]["decrease"] = True
                            # connect former trail to candidate with new
                            # 'warp' edge
                            DualNetwork.create_warp_edge(trail, candidate)
                            # remove 'leaf' attribute of former trail
                            trail[1]["leaf"] = False

        return DualNetwork

# MAIN -------------------------------------------------------------------------
if __name__ == '__main__':
    pass
