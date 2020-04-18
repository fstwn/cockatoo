# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from collections import deque, OrderedDict
import math
from operator import itemgetter

# RHINO IMPORTS ----------------------------------------------------------------
from Rhino.Geometry import Curve as RhinoCurve
from Rhino.Geometry import Line as RhinoLine
from Rhino.Geometry import Interval as RhinoInterval
from Rhino.Geometry import Vector3d as RhinoVector3d

# THIRD PARTY MODULE IMPORTS ---------------------------------------------------
import networkx as nx

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from .Exceptions import *
from .KnitNetworkBase import KnitNetworkBase
from .KnitMappingNetwork import KnitMappingNetwork

# ALL DICTIONARY ---------------------------------------------------------------
__all__ = [
    "KnitNetwork"
]

# ACTUAL CLASS -----------------------------------------------------------------
class KnitNetwork(KnitNetworkBase):
    """
    Class for representing a network that facilitates the automatic generation
    of knitting patterns based on Rhino geometry.
    """

    # INITIALIZATION -----------------------------------------------------------

    def __init__(self, data=None, **attr):
        """
        Initialize a KnitNetwork (inherits NetworkX graph with edges, name,
        graph attributes.

        Parameters
        ----------
        data : input graph
            Data to initialize graph.  If data=None (default) an empty
            graph is created.  The data can be an edge list, or any
            NetworkX graph object.  If the corresponding optional Python
            packages are installed the data can also be a NumPy matrix
            or 2d ndarray, a SciPy sparse matrix, or a PyGraphviz graph.
        name : string, optional (default='')
            An optional name for the graph.
        attr : keyword arguments, optional (default= no attributes)
            Attributes to add to graph as key=value pairs.
        """

        # initialize using original init method
        super(KnitNetwork, self).__init__(data=data, **attr)

        # also copy the MappingNetwork attribute if it is already available
        if data and isinstance(data, KnitNetwork) and data.MappingNetwork:
            self.MappingNetwork = data.MappingNetwork
        else:
            self.MappingNetwork = None

    # REPRESENTATION OF NETWORK ------------------------------------------------

    def ToString(self):
        """
        Return a textual description of the network.
        """

        name = "KnitNetwork"
        nn = len(self.nodes())
        ce = len(self.ContourEdges)
        wee = len(self.WeftEdges)
        wae = len(self.WarpEdges)
        data = ("({} Nodes, {} Position Contours, {} Weft, {} Warp)")
        data = data.format(nn, ce, wee, wae)
        return name + data

    # INITIALIZATION OF POSITION CONTOUR EDGES ---------------------------------

    def InitializePositionContourEdges(self):
        """
        Creates all initial position contour edges as neither 'warp' nor 'weft'
        by iterating over all nodes in the network and grouping them based on
        their 'position' attribute.
        """

        # get all nodes by position
        posList = self.AllNodesByPosition(True)

        for i, pos in enumerate(posList):
            for j, node in enumerate(pos):
                k = j + 1
                if k < len(pos):
                    self.CreateContourEdge(node, pos[k])

    # INITIALIZATION OF 'WEFT' EDGES BETWEEN 'LEAF' NODES ----------------------

    def InitializeLeafConnections(self):
        """
        Create all initial connections of the 'leaf' nodes by iterating over
        all position contours and creating 'weft' edges between the 'leaf'
        nodes of the position contours.
        """

        # get all leaves
        leafNodes = self.AllLeavesByPosition(True)

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
                self.CreateWeftEdge(startLeaf, nextStart)
                self.CreateWeftEdge(endLeaf, nextEnd)

    # INITIALIZATION OF PRELIMINARY 'WEFT' EDGES -------------------------------

    def AttemptWeftConnectionToCandidate(self, node, candidate, source_nodes, max_connections=4, verbose=False):
        """
        Method for attempting a 'weft' connection to a candidate
        node based on certain parameters.

        Parameters
        ----------
        node : node
            The starting node for the possible 'weft' edge.

        candidate : node
            The target node for the possible 'weft' edge.

        source_nodes : list
            List of nodes on the position contour of node. Used to check if
            the candidate node already has a connection.

        max_connections : int
            The new 'weft' connection will only be made if the candidate nodes
            number of connected neighbours is below this. Defaults to 4.

        verbose : bool
            If True, this routine and all its subroutines will print messages
            about what is happening to the console.
            Defaults to False.

        Returns
        -------
        result : bool
            True if the connection has been made, otherwise false.
        """

        # get connected neighbours
        connecting_neighbours = self[candidate[0]]
        # only do something if the maximum is not reached
        if len(connecting_neighbours) < max_connections:
            # determine if the node is already connected to a node from
            # the input source nodes
            isConnected = False
            for cn in connecting_neighbours:
                if cn in [v[0] for v in source_nodes]:
                    isConnected = True
                    # print info on verbose setting
                    if verbose:
                        vStr = ("Candidate node {} is " +
                                "already connected! " +
                                "Skipping to next " +
                                "node...")
                        vStr = vStr.format(candidate[0])
                        print(vStr)
                    break
            # check the flag and act accordingly
            if not isConnected:
                # print info on verbose setting
                if verbose:
                    vStr = ("Connecting node {} to best " +
                            "candidate {}.")
                    vStr = vStr.format(node[0], candidate[0])
                    print(vStr)
                # if all conditions are met, make the 'weft' connection
                self.CreateWeftEdge(node, candidate)
                return True
            else:
                return False
        else:
            return False

    def _create_initial_weft_connections(self, contour_set, max_connections=4, precise=False, verbose=False):
        """
        Private method for creating initial 'weft' connections for the supplied
        set of contours, starting from the first contour in the set and
        propagating to the last contour in the set.
        """

        # namespace mapping for performance gains
        pi = math.pi
        to_radians = math.radians

        if len(contour_set) < 2:
            if verbose:
                print("Not enough contours in contour set!")
            return

        # print info on verbose output
        if verbose:
            print("Creating initial 'weft' connections for contour set...")

        # loop over all vertices of positions (list of lists of tuples)
        for i, pos in enumerate(contour_set):
            # pos is a list of tuples (nodes)
            if i < len(contour_set):
                j = i + 1
                if j == len(contour_set):
                    break
                # get initial and target vertices without 'leaf' nodes
                initial_nodes = contour_set[i][1:-1]
                target_nodes = contour_set[j][1:-1]

                # skip if one of the contours has no nodes
                if len(initial_nodes) == 0 or len(target_nodes) == 0:
                    continue

                # define forbidden node index
                forbidden_node = -1

                # loop through all nodes on the current position
                for k, node in enumerate(initial_nodes):
                    # print info on verbose setting
                    if verbose:
                        vStr = "Processing node {} on position {}:"
                        vStr = vStr.format(node[0], node[1]["position"])
                        print(vStr)

                    # get the geometry for the current node
                    thisPt = node[1]["geo"]

                    # filtering according to forbidden nodes
                    target_nodes = [tn for tn in target_nodes \
                                    if tn[0] >= forbidden_node]
                    if len(target_nodes) == 0:
                        continue

                    # get four closest verts on adjacent contour
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
                    if verbose:
                        vStr = "Possible connections: {}"
                        vStr = vStr.format([pc[0] for pc in \
                                           possible_connections])
                        print(vStr)

                    # handle edge case where there is no possible
                    # connection or just one
                    if len(possible_connections) == 0:
                        # skip if there are no possible connections
                        continue
                    elif len(possible_connections) == 1:
                        # attempt to connect to only possible candidate
                        fCand = possible_connections[0]
                        res = self.AttemptWeftConnectionToCandidate(node,
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

                    # get node neighbours
                    nNeighbours = self[node[0]]

                    # compute angle difference
                    aDelta = angles[0] - angles[1]

                    # CONNECTION FOR LEAST ANGLE CHANGE ------------------------
                    if len(nNeighbours) > 2 and aDelta < to_radians(6.0):
                        # print info on verbose setting
                        if verbose:
                            print("Using procedure for least angle " +
                                  "change connection...")

                        # get previous pos verts, indices and connections
                        prevPos = contour_set[i-1]
                        prevIndices = [n[0] for n in prevPos]

                        # get previous connected edge and its direction
                        prevEdges = self.NodeWeftEdges(node[0], data=True)
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
                        angleA = RhinoVector3d.VectorAngle(prevDir, dirA, normalA)
                        angleB = RhinoVector3d.VectorAngle(prevDir, dirB, normalB)

                        # select final candidate for connection by angle
                        if angleA < angleB:
                            fCand = mpA
                        else:
                            fCand = mpB

                        # attempt to connect to final candidate
                        res = self.AttemptWeftConnectionToCandidate(node,
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
                        if verbose:
                            print("Using procedure for most " +
                                  "perpendicular connection...")
                        # define final candidate
                        fCand = most_perpendicular[0]

                        # attempt to connect to final candidate node
                        res = self.AttemptWeftConnectionToCandidate(node,
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
        """

        # namespace mapping for performance gains
        pi = math.pi

        # get attributes only once
        position_attributes = nx.get_node_attributes(self, "position")
        num_attributes = nx.get_node_attributes(self, "num")

        if len(contour_set) < 2:
            if verbose:
                print("Not enough contours in contour set!")
            return

        # print info on verbose output
        if verbose:
            print("Creating second pass 'weft' connections for contour set...")

        # loop over all vertices of positions (list of lists of tuples)
        for i, pos in enumerate(contour_set):
            j = i + 1

            # get initial vertices without 'leaf' nodes
            if include_leaves:
                initial_nodes = contour_set[i]
            else:
                initial_nodes = contour_set[i][1:-1]

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
                if verbose:
                    vStr = "Processing node {} on position {}:"
                    vStr = vStr.format(node[0], node[1]["position"])
                    print(vStr)

                # get connecting edges on target position
                conWeftEdges = self.NodeWeftEdges(node[0], data=True)
                conPos = []
                if len(conWeftEdges) == 0 and verbose:
                    # print info on verbose setting
                    print("No previously connected weft edges...")
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
                        if verbose:
                            print("Node is connected. Skipping...")
                        continue
                    target_positions.append(target_positionB)
                elif target_positionB == None:
                    if target_positionA in conPos:
                        if verbose:
                            print("Node is connected. Skipping...")
                        continue
                    target_positions.append(target_positionA)
                elif ((target_positionA in conPos) and
                      (target_positionB in conPos)):
                    if verbose:
                        print("Node is connected. Skipping...")
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
                if verbose:
                    if len(target_positions) > 1:
                        vStr = "Two target positions: {}, {}"
                        vStr = vStr.format(*target_positions)
                        print(vStr)
                    elif len(target_positions) == 1:
                        vStr = "Target position: {}"
                        vStr = vStr.format(target_positions[0])
                        print(vStr)

                # skip if there are no target positions
                if len(target_positions) == 0:
                    if verbose:
                        print("No target position! Skipping...")
                    continue

                # only proceed if there is a target position
                for target_position in target_positions:
                    # get target vertices
                    target_nodes = self.NodesOnPosition(target_position, True)

                    # get the point geo of this node
                    thisPt = node[1]["geo"]

                    # get a window of possible connections on the target
                    # position by looking for the previos vertex on this contour
                    # connected to target position, then propagating along
                    # the target position to the next node that is connected
                    # to this position. these two nodes will define the window

                    # NOTE: the current node should never have a connection
                    # to target position (theoretically!), otherwise it should
                    # have fallen through the checks by now

                    # print info on verbose setting
                    if verbose:
                        vStr = "Target position is {}. Computing window..."
                        vStr = vStr.format(target_position)
                        print(vStr)

                    # get the previous node on this contour
                    prevNode = initial_nodes[k-1]

                    # assume that the previous node has a connection
                    prevCon = self.NodeWeftEdges(prevNode[0], data=True)

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
                        if verbose:
                            print("No possible connection, skipping...")
                        continue

                    # get the next node on this pos that is
                    # connected to target position
                    if k < len(initial_nodes)-1:
                        future_nodes = initial_nodes[k+1:]
                        for futurenode in future_nodes:
                            filteredWeftEdges = []
                            futureWeftEdges = self.NodeWeftEdges(futurenode[0],
                                                                 data=True)
                            for futureweft in futureWeftEdges:
                                fwn = (futureweft[1], self.node[futureweft[1]])
                                if (fwn[1]["position"] == target_position and
                                    fwn[1]["num"] >= start_of_window[1]["num"]):
                                    filteredWeftEdges.append(futureweft)
                                else:
                                    continue
                            if (not filteredWeftEdges or
                                len(filteredWeftEdges) == 0):
                                end_of_window = None
                                continue
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
                        if verbose:
                            print("Length of window is 0, skipping...")
                    elif len(window) == 1:
                        # print info on verbose setting
                        if verbose:
                            print("Window has only one node.")
                            vStr = ("Connecting to node {} on " +
                                    "position {}...")
                            vStr = vStr.format(window[0][0],
                                               window[0][1]["position"])
                            print(vStr)

                        # connect weft edge
                        self.CreateWeftEdge(node, window[0])
                    else:
                        # print info on verbose setting
                        if verbose:
                            vStr = "Processing window nodes: {}"
                            vStr = vStr.format([w[0] for w in window])
                            print(vStr)

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
                        if verbose:
                            vStr = ("Connecting to node {} on " +
                                    "position {}...")
                            vStr = vStr.format(fCand[0],
                                               fCand[1]["position"])
                            print(vStr)

                        # connect weft edge to best target
                        self.CreateWeftEdge(node, fCand)

    def InitializeWeftEdges(self, start_index=None, include_leaves=False, max_connections=4, least_connected=False, precise=False, verbose=False):
        """
        Attempts to create all the preliminary 'weft' connections for the
        network.

        Parameters
        ----------
        start_index : int
            The starting index

        include_leaves : bool
            If 'leaf' nodes should be included

        max_connections : int
            The maximum connections a node is allowed to have to be considered
            for an additional 'weft' connection.
            Defaults to 4.

        least_connected : bool
            If True, uses the least connected node from the found candidates

        precise : bool
            If True, the distance between nodes will be calculated using the
            Rhino.Geometry.Point3d.DistanceTo method, otherwise the much faster
            Rhino.Geometry.Point3d.DistanceToSquared method is used.
            Defaults to False.

        verbose : boolean
            If True, this routine and all its subroutines will print messages
            about what is happening to the console. Great for debugging and
            analysis.
            Defaults to False.
        """

        # get all the positions / contours
        AllPositions = self.AllNodesByPosition(True)

        if start_index == None:
            # get index of longest contour
            start_index = self.LongestPositionContour()[0]
        elif start_index >= len(AllPositions):
            raise KnitNetworkError("Supplied splitting index is too high!")

        # split position list into two sets based on start index
        leftContours = AllPositions[0:start_index+1]
        leftContours.reverse()
        rightContours = AllPositions[start_index:]

        # create the initial weft connections
        self._create_initial_weft_connections(leftContours,
                                              max_connections=max_connections,
                                              precise=precise,
                                              verbose=verbose)

        self._create_initial_weft_connections(rightContours,
                                              max_connections=max_connections,
                                              precise=precise,
                                              verbose=verbose)

        # create second pass weft connections
        self._create_second_pass_weft_connections(leftContours,
                                                  include_leaves,
                                                  least_connected,
                                                  precise=precise,
                                                  verbose=verbose)

        self._create_second_pass_weft_connections(rightContours,
                                                  include_leaves,
                                                  least_connected,
                                                  precise=precise,
                                                  verbose=verbose)

        return True

    # INITIALIZATION OF PRELIMINARY 'WARP' EDGES -------------------------------

    def InitializeWarpEdges(self, contour_set=None, verbose=False):
        """
        Method for initializing first 'warp' connections once
        all 'weft' connections are made.
        """

        # if no contour set is provided, use all contours of this network
        if contour_set == None:
            contour_set = self.AllNodesByPosition(True)

        # loop through all positions in the set of contours
        for i, pos in enumerate(contour_set):
            # get all vertices on current contour
            initial_nodes = contour_set[i]

            # loop through all nodes on this contour
            for k, node in enumerate(initial_nodes):
                connected_edges = self.edges(node[0], data=True)
                numweft = len(self.NodeWeftEdges(node[0]))
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

    def TraverseEdgeUntilEnd(self, start_end_node, start_node, seen_segments, way_nodes=None, way_edges=None, end_nodes=None):
        """
        Method for traversing a path of 'weft' edges until another
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
        connected_weft_edges = self.edges(start_node[0], data=True)
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
            print("More than one filtered candidate weft edge!")
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
                return self.TraverseEdgeUntilEnd(start_end_node,
                                                 connected_node,
                                                 seen_segments,
                                                 way_nodes,
                                                 way_edges,
                                                 end_nodes)
        else:
            return seen_segments

    def TraverseWeftEdgesAndSetAttributes(self, start_end_node):
        """
        Traverse a path of 'weft' edges starting from an 'end' node until
        another 'end' node is discovered. Set 'segment' attributes to nodes
        and egdes along the way.
        """

        # get connected weft edges and sort them by their connected node
        weft_connections = self.edges(start_end_node[0], data=True)
        weft_connections.sort(key=lambda x: x[1])

        # loop through all connected weft edges
        seen_segments = []
        for cwe in weft_connections:
            if cwe[2]["segment"]:
                continue

            # check the connected node. if it is an end vertex,
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
                seen_segments = self.TraverseEdgeUntilEnd(start_end_node[0],
                                                          connected_node,
                                                          seen_segments,
                                                          way_edges=[cwe])

    def AssignSegmentAttributes(self):
        """
        Get the segmentation for loop generation and assign 'segment' attributes
        to 'weft' edges and nodes.
        """

        if len(self.WeftEdges) == 0:
            errMsg = ("No 'weft' edges in KnitNetwork! Segmentation " +
                      "is impossible.")
            raise NoWeftEdgesError(errMsg)
        if len(self.EndNodes) == 0:
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

        # get all 'end' vertices ordered by their 'position' attribute
        all_ends_by_position = self.AllEndsByPosition(data=True)

        # loop through all 'end' vertices
        for position in all_ends_by_position:
            for endnode in position:
                self.TraverseWeftEdgesAndSetAttributes(endnode)

        # add all previously removed edges back into the network
        [self.add_edge(edge[0], edge[1], attr_dict=edge[2]) \
         for edge in warp_storage + contour_storage]

    # CREATION OF MAPPING NETWORK ----------------------------------------------

    def CreateMappingNetwork(self):
        """
        Creates the corresponding mapping network for the final loop generation
        from a KnitNetwork instance with fully assigned 'segment' attributes.

        Notes
        -----
        All nodes without an 'end' attribute as well as all 'weft' edges are
        removed by this step. Final nodes as well as final 'weft' and 'warp'
        edges can only be created using the mapping network.
        """

        # create a new KnitMappingNetwork instance
        MappingNetwork = KnitMappingNetwork()

        # get all edges of the current network by segment
        WeftEdges = sorted(self.WeftEdges, key=lambda x: x[2]["segment"])
        WarpEdges = self.WarpEdges

        # initialize deque container for segment ids
        segment_ids = deque()

        # loop through all 'weft' edges and fill container with unique ids
        for edge in WeftEdges:
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
            segment_edges = [e for e in WeftEdges if e[2]["segment"] == id]
            segment_edges.sort(key=lambda x: x[0])
            # extract start and end nodes
            start_node = (id[0], self.node[id[0]])
            endNode = (id[1], self.node[id[1]])
            # get all the geometry of the individual edges
            segment_geo = [e[2]["geo"] for e in segment_edges]
            # create a segment contour edge in the mapping network
            res = MappingNetwork.CreateSegmentContourEdge(start_node,
                                                          endNode,
                                                          id,
                                                          segment_geo)
            if not res:
                errMsg = ("SegmentContourEdge at segment id {} could not be " +
                          "created!")
                raise KnitNetworkError(errMsg)

        # add all warp edges to the mapping network to avoid lookup hassle
        for warp_edge in WarpEdges:
            if warp_edge[0] > warp_edge[1]:
                warp_from =  warp_edge[1]
                warp_to = warp_edge[0]
            else:
                warp_from =  warp_edge[0]
                warp_to = warp_edge[1]
            MappingNetwork.add_edge(warp_from, warp_to, attr_dict=warp_edge[2])

        # set mapping network property for this instance
        self.MappingNetwork = MappingNetwork

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

        return self._MappingNetwork

    def _set_mapping_network(self, mapping_network):
        """
        Private setter method for setting this instance's associated mapping
        network.
        """

        # set mapping network to instance
        if (isinstance(mapping_network, KnitMappingNetwork) \
        or mapping_network == None):
            self._MappingNetwork = mapping_network
        else:
            raise ValueError("Input is not of type KnitMappingNetwork!")

    MappingNetwork = property(_get_mapping_network, _set_mapping_network, None,
                              "The associated mapping network of this \
                               KnitNetwork instance.")

    # RETRIEVAL OF NODES AND EDGES FROM MAPPING NETWORK ------------------------

    def AllNodesBySegment(self, data=False, edges=False):
        """
        Returns all nodes of the network ordered by 'segment' attribute.
        Note: 'end' nodes are not included!
        """

        # retrieve mappingnetwork
        mapnet = self.MappingNetwork
        if not mapnet:
            errMsg = ("Mapping network has not been built for this instance!")
            raise MappingNetworkError(errMsg)

        allSegments = mapnet.SegmentContourEdges

        anbs = []
        for i, segment in enumerate(allSegments):
            segval = segment[2]["segment"]
            segnodes = self.NodesOnSegment(segval, data=True)
            if data:
                if edges:
                    anbs.append((segval, segnodes, allSegments[i]))
                else:
                    anbs.append((segval, segnodes))
            else:
                if edges:
                    anbs.append((segval, [sn[0] for sn in segnodes], allSegments[i]))
                else:
                    anbs.append((segval, [sn[0] for sn in segnodes]))

        return anbs

    # STITCH WIDTH SAMPLING ----------------------------------------------------

    def SampleSegmentContours(self, stitch_width):
        """
        Samples the segment contours of the mapping network with the given
        stitch width. The resulting points are added to the network as nodes
        and a 'segment' attribute is assigned to them based on their origin
        segment contour edge.

        Parameters
        ----------

        stitch_width : float
            The width of a single stitch inside the knit.
        """

        # retrieve mapping network
        mapnet = self.MappingNetwork
        if not mapnet:
            errMsg = ("Mapping network has not been built for this instance, " +
                      "sampling segment contours is impossible!")
            raise MappingNetworkError(errMsg)

        # get the highest index of all the nodes in the network
        maxNode = max(self.nodes())

        # get all the segment geometry ordered by segment number
        segment_contours = mapnet.SegmentContourEdges

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
                self.NodeFromPoint3d(nodeindex,
                                    pt,
                                    position = None,
                                    num = j,
                                    leaf = nodeLeaf,
                                    end = False,
                                    segment = seg[2]["segment"])
                # increment node index
                nodeindex += 1

    # CREATION OF FINAL 'WEFT' CONNECTIONS -------------------------------------

    def CreateFinalWeftConnections(self):
        """
        Loop through all the segment contour edges and create all 'weft'
        connections for this network.
        """

        # get all nodes by segment contour
        SegmentValues, AllNodesBySegment = zip(*self.AllNodesBySegment(data=True))

        # loop through all the segment contours
        for i, segment in enumerate(AllNodesBySegment):
            segval = SegmentValues[i]
            firstNode = (segval[0], self.node[segval[0]])
            lastNode = (segval[1], self.node[segval[1]])

            if len(segment) == 0:
                self.CreateWeftEdge(firstNode, lastNode, segval)
            elif len(segment) == 1:
                self.CreateWeftEdge(firstNode, segment[0], segval)
                self.CreateWeftEdge(segment[0], lastNode, segval)
            else:
                # loop through all nodes on the current segment and create
                # the final 'weft' edges
                for j, node in enumerate(segment):
                    if j == 0:
                        self.CreateWeftEdge(firstNode, node, segval)
                        self.CreateWeftEdge(node, segment[j+1], segval)
                    elif j < len(segment)-1:
                        self.CreateWeftEdge(node, segment[j+1], segval)
                    elif j == len(segment)-1:
                        self.CreateWeftEdge(node, lastNode, segval)

    # CREATION OF FINAL 'WARP' CONNECTIONS -------------------------------------

    def AttemptWarpConnectionToCandidate(self, node, candidate, source_nodes, max_connections=4, verbose=False):
        """
        Method for attempting a 'warp' connection to a candidate
        node based on certain parameters.

        Parameters
        ----------
        node : node
            The starting node for the possible 'weft' edge.

        candidate : node
            The target node for the possible 'weft' edge.

        source_nodes : list
            List of nodes on the position contour of node. Used to check if
            the candidate node already has a connection.

        max_connections : int
            The new 'weft' connection will only be made if the candidate nodes
            number of connected neighbours is below this. Defaults to 4.

        verbose : bool
            If True, this routine and all its subroutines will print messages
            about what is happening to the console.
            Defaults to False.

        Returns
        -------
        result : bool
            True if the connection has been made, otherwise false.
        """

        connecting_neighbours = self[candidate[0]]
        if len(connecting_neighbours) < max_connections:
            isConnected = False
            for cn in connecting_neighbours:
                if cn in [v[0] for v in source_nodes]:
                    isConnected = True
                    # print info on verbose setting
                    if verbose:
                        vStr = ("Candidate node {} is " +
                                "already connected! " +
                                "Skipping to next " +
                                "node...")
                        vStr = vStr.format(candidate[0])
                        print(vStr)
                    break
            if not isConnected:
                # print info on verbose setting
                if verbose:
                    vStr = ("Connecting node {} to best " +
                            "candidate {}.")
                    vStr = vStr.format(node[0], candidate[0])
                    print(vStr)
                # finally create the warp edge for good
                self.CreateWarpEdge(node, candidate)
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
        """

        # namespace mapping for performance gains
        pi = math.pi
        to_radians = math.radians

        if len(segment_pair) < 2:
            if verbose:
                print("Not enough contour segments in supplied set!")
            return

        # print info on verbose output
        if verbose:
            print("Creating initial 'warp' connections for contour set...")

        # get initial and target vertices without 'end' nodes
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
            if verbose:
                vStr = "Processing node {} on segment {}:"
                vStr = vStr.format(node[0], node[1]["segment"])
                print(vStr)

            # filtering according to forbidden nodes
            target_nodes = [tn for tn in target_nodes \
                            if tn[0] >= forbidden_node]
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
            allDists, sorted_target_nodes = zip(
                                    *sorted(zip(allDists,
                                                target_nodes),
                                                key = itemgetter(0)))

            # the four nearest nodes are the possible connections
            possible_connections = sorted_target_nodes[:4]
            # print info on verbose setting
            if verbose:
                vStr = "Possible connections: {}"
                vStr = vStr.format([pc[0] for pc in \
                                   possible_connections])
                print(vStr)

            # handle edge case where there is no possible connection or just one
            if len(possible_connections) == 0:
                continue
            elif len(possible_connections) == 1:
                # attempt to connect to only possible candidate
                fCand = possible_connections[0]
                res = self.AttemptWarpConnectionToCandidate(node,
                                                fCand,
                                                initial_nodes,
                                                max_connections=max_connections,
                                                verbose=verbose)
                # set forbidden node
                if res:
                    forbidden_node = fCand[0]
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
            allDists, deltas, angles, most_perpendicular = zip(
                                *sorted(zip(allDists,
                                            deltas,
                                            angles,
                                            possible_connections[:]),
                                            key = itemgetter(0, 1)))

            # compute angle difference
            aDelta = angles[0] - angles[1]

            # get node neighbours
            nNeighbours = self[node[0]]

            # CONNECTION FOR LEAST ANGLE CHANGE --------------------------------
            if len(nNeighbours) > 2 and aDelta < to_radians(6.0):
                # print info on verbose setting
                if verbose:
                    print("Using procedure for least angle " +
                          "change connection...")

                # get previous connected edge and its direction
                prevEdges = self.NodeWarpEdges(node[0], data=True)
                if len(prevEdges) > 1:
                    print("More than one previous " +
                          "'warp' connection! This was unexpected...")
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
                res = self.AttemptWarpConnectionToCandidate(node,
                                                fCand,
                                                initial_nodes,
                                                max_connections=max_connections,
                                                verbose=verbose)
                # set forbidden node
                if res:
                    forbidden_node = fCand[0]
                continue

            # CONNECTION FOR MOST PERPENDICULAR --------------------------------
            else:
                # print info on verbose setting
                if verbose:
                    print("Using procedure for most " +
                          "perpendicular connection...")
                # define final candidate node
                fCand = most_perpendicular[0]
                # attempt connection to final candidate
                res = self.AttemptWarpConnectionToCandidate(node,
                                                fCand,
                                                initial_nodes,
                                                max_connections=max_connections,
                                                verbose=verbose)
                # set forbidden node
                if res:
                    forbidden_node = fCand[0]

    def _create_second_pass_warp_connection(self, source_nodes, source_index, window, precise=False, verbose=False):
        """
        Private method for creating second pass 'warp' connections for the
        given set of contours.
        """

        if len(window) == 0:
            # print info on verbose setting
            if verbose:
                print("Length of window is 0, skipping...")
        elif len(window) == 1:
            # print info on verbose setting
            if verbose:
                print("Window has only one node.")
                vStr = ("Connecting to node {}.")
                vStr = vStr.format(window[0][0])
                print(vStr)

            # connect 'warp' edge
            self.CreateWarpEdge(source_nodes[source_index], window[0])
        else:
            # retrive the point of the current source node
            thisPt = source_nodes[source_index][1]["geo"]

            # print info on verbose setting
            if verbose:
                vStr = "Processing window nodes: {}"
                vStr = vStr.format([w[0] for w in window])
                print(vStr)

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
            deltas = [abs(a - (0.5 * math.pi)) for a in angles]

            # sort window by distance, then by delta
            allDists, deltas, most_perpendicular = zip(*sorted(
                                                    zip(allDists,
                                                        deltas,
                                                        window),
                                                        key = itemgetter(0, 1)))
            # set final candidate node for connection
            fCand = most_perpendicular[0]

            # print info on verbose setting
            if verbose:
                vStr = ("Connecting to node {} on " +
                        "position {}...")
                vStr = vStr.format(fCand[0],
                                   fCand[1]["position"])
                print(vStr)

            # connect weft edge to best target
            self.CreateWarpEdge(source_nodes[source_index], fCand)

    def CreateFinalWarpConnections(self, max_connections=4, include_end_nodes=True, precise=False, verbose=False):
        """
        Create the final 'warp' connections by building chains of segment
        contour edges and connecting them.

        For each source chain, a target chain is found using an
        'educated guessing' strategy. This means that the possible target chains
        are guessed by leveraging known topology facts about the network and its
        special 'end' nodes.

        Parameters
        ----------
        max_connections : integer
            The number of maximum previous connections a candidate node for a
            'warp' connection is allowed to have.

        include_end_nodes : bool
            If True, 'end' nodes between adjacent segment contours in a source
            chain will be included in the first pass of connecting 'warp' edges.
            Defaults to True.

        precise : bool
            If True, the distance between nodes will be calculated using the
            Rhino.Geometry.Point3d.DistanceTo method, otherwise the much faster
            Rhino.Geometry.Point3d.DistanceToSquared method is used.
            Defaults to False.

        verbose : bool
            If True, this routine and all its subroutines will print messages
            about what is happening to the console. Great for debugging and
            analysis.
            Defaults to False.
        """

        # retrieve mapping network
        mapnet = self.MappingNetwork
        if not mapnet:
            errMsg = ("Mapping network has not been built for this instance, " +
                      "sampling segment contours is impossible!")
            raise MappingNetworkError(errMsg)

        # get all segment ids, nodes per segment and edges
        SegmentValues, AllNodesBySegment, SegmentContourEdges = zip(
                                 *self.AllNodesBySegment(data=True, edges=True))

        # build a dictionary of the segments by their index
        SegmentDict = dict(zip(SegmentValues,
                               zip(SegmentContourEdges, AllNodesBySegment)))

        # build source and target chains
        source_chains, target_chain_dict = mapnet.BuildChains(False, True)

        # initialize container dict for connected chains
        connected_chains = dict()

        # initialize segment mapping dictionaries
        source_to_target = OrderedDict()
        target_to_source = OrderedDict()

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
            if verbose:
                print("-------------------------------------------------------")
                print("Processing segment chain {} ...".format(source_chain))

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
                target_nodes = [SegmentDict[id][1] for id in target_ids]
                target_nodes = [n for seg in target_nodes for n in seg]

                # print info on verbose setting
                if verbose:
                    vStr = "<=====> detected. Connecting to segment chain {}."
                    vStr = vStr.format(target_key)
                    print(vStr)
                # we have successfully verified our target segment and
                # can create some warp edges!
                segment_pair = [current_nodes, target_nodes]

                # fill mapping dictionaries
                if current_ids not in source_to_target:
                    source_to_target[current_ids] = target_ids
                if target_ids not in target_to_source:
                    target_to_source[target_ids] = current_ids

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
                target_nodes = [SegmentDict[id][1] for id in target_ids]
                target_nodes = [n for seg in target_nodes for n in seg]

                targetFirstNode = target_ids[0][0]
                targetLastNode = target_ids[-1][1]

                # check if firstNode and targetFirstNode are connected via a
                # 'warp' edge to verify
                if (targetFirstNode == firstNode[0] \
                and targetLastNode in self[lastNode[0]]):
                    # print info on verbose setting
                    if verbose:
                        vStr = "<=====/ detected. Connecting to segment {}."
                        vStr = vStr.format(target_key)
                        print(vStr)
                    # we have successfully verified our target segment and
                    # can create some warp edges!
                    segment_pair = [current_nodes, target_nodes]
                    connected_chains[target_key] = True

                    # fill mapping dictionaries
                    if current_ids not in source_to_target:
                        source_to_target[current_ids] = target_ids
                    if target_ids not in target_to_source:
                        target_to_source[target_ids] = current_ids

                    # create initial 'warp' connections between the chains
                    self._create_initial_warp_connections(
                                                segment_pair,
                                                max_connections=max_connections,
                                                precise=precise,
                                                verbose=verbose)
                    continue
                else:
                    if verbose:
                        print("No real connection for <=====/. Next case...")

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
                target_nodes = [SegmentDict[id][1] for id in target_ids]
                target_nodes = [n for seg in target_nodes for n in seg]

                targetFirstNode = target_ids[0][0]
                targetLastNode = target_ids[-1][1]

                # check if firstNode and targetFirstNode are connected via a
                # 'warp' edge to verify
                if (targetFirstNode in self[firstNode[0]] \
                and targetLastNode == lastNode[0]):
                    # print info on verbose setting
                    if verbose:
                        vStr = "/=====> detected. Connecting to segment {}."
                        vStr = vStr.format(target_key)
                        print(vStr)
                    # we have successfully verified our target segment and
                    # can create some warp edges!
                    segment_pair = [current_nodes, target_nodes]
                    connected_chains[target_key] = True

                    # fill mapping dictionaries
                    if current_ids not in source_to_target:
                        source_to_target[current_ids] = target_ids
                    if target_ids not in target_to_source:
                        target_to_source[target_ids] = current_ids

                    self._create_initial_warp_connections(segment_pair,
                                                max_connections=max_connections,
                                                precise=precise,
                                                verbose=verbose)
                    continue
                else:
                    if verbose:
                        print("No real connection for /=====>. Next case...")

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
                target_nodes = [SegmentDict[id][1] for id in target_ids]
                target_nodes = [n for seg in target_nodes for n in seg]

                # set target first and last node ('end' nodes)
                targetFirstNode = target_ids[0][0]
                targetLastNode = target_ids[-1][1]

                # check if firstNode and targetFirstNode are connected via a
                # 'warp' edge to verify
                if (targetFirstNode in self[firstNode[0]] \
                and targetLastNode in self[lastNode[0]]):
                    # print info on verbose setting
                    if verbose:
                        vStr = "/=====/ detected. Connecting to segment {}."
                        vStr = vStr.format(target_key)
                        print(vStr)
                    # we have successfully verified our target segment and
                    # can create some warp edges!
                    segment_pair = [current_nodes, target_nodes]
                    connected_chains[target_key] = True

                    # fill mapping dictionaries
                    if current_ids not in source_to_target:
                        source_to_target[current_ids] = target_ids
                    if target_ids not in target_to_source:
                        target_to_source[target_ids] = current_ids

                    self._create_initial_warp_connections(
                                                segment_pair,
                                                max_connections=max_connections,
                                                precise=precise,
                                                verbose=verbose)
                    continue
                else:
                    if verbose:
                        print("No real connection for /=====/. No cases match.")

        # SECOND PASS SKETCHING ------------------------------------------------

        # INVOKE SECOND PASS FOR SOURCE ---> TARGET ----------------------------

        for i, current_chain in enumerate(source_to_target):
            print("-----------------------------------------------------------")
            print("S>T Current Chain: {}".format(current_chain))
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
                node_neighbours = self[node[0]]
                node_connected = False
                if k == 0 or k == len(current_chain_nodes)-1:
                    node_connected = True

                # find out if the current node is already connected to the
                # target chain
                # get node warp edges and their target nodes
                node_warp_edges = self.NodeWarpEdges(node[0], data=False)
                warp_edge_targets = [we[1] for we in node_warp_edges]
                # loop over warp edge targets
                for wet in warp_edge_targets:
                    for n, tcn in enumerate(target_chain_nodes):
                        if wet == tcn[0]:
                            if n > start_of_window or start_of_window == -1:
                                start_of_window = n
                            node_connected = True

                # if the node is not connected to the target chain, we
                # need to find the end of the window
                if not node_connected:
                    print("Node: {}".format(node[0]))
                    print("Start of window: {}".format(start_of_window))

                    end_of_window = None
                    for n, tcn in enumerate(target_chain_nodes):
                        if n >= start_of_window:
                            if tcn[0] == current_chain_nodes[-1][0]:
                                end_of_window = n
                            tcn_warp_edges = self.NodeWarpEdges(tcn[0],
                                                                data=False)
                            tcn_warp_edge_targets = [we[1] for we \
                                                     in tcn_warp_edges]
                            for twet in tcn_warp_edge_targets:
                                if (twet in [cn[0] for cn \
                                             in current_chain_nodes]):
                                    end_of_window = n
                                    break
                        if end_of_window:
                            break

                    if start_of_window != -1 and end_of_window != None:
                        if end_of_window == len(target_chain_nodes)-1:
                            window = target_chain_nodes[start_of_window:]
                        else:
                            window = target_chain_nodes[start_of_window: \
                                                        end_of_window+1]

                        print("End of window: {}".format(end_of_window))

                        self._create_second_pass_warp_connection(
                                                            current_chain_nodes,
                                                            k,
                                                            window,
                                                            precise=False,
                                                            verbose=True)


        # INVOKE SECOND PASS FOR TARGET ---> SOURCE ----------------------------

        for i, current_chain in enumerate(target_to_source):
            print("-----------------------------------------------------------")
            print("T>S Current Chain: {}".format(current_chain))
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
                node_neighbours = self[node[0]]
                node_connected = False
                if k == 0 or k == len(current_chain_nodes)-1:
                    node_connected = True

                # find out if the current node is already connected to the
                # target chain
                node_warp_edges = self.NodeWarpEdges(node[0], data=False)
                warp_edge_targets = [we[1] for we in node_warp_edges]
                for wet in warp_edge_targets:
                    for n, tcn in enumerate(target_chain_nodes):
                        if wet == tcn[0]:
                            if n > start_of_window or start_of_window == -1:
                                start_of_window = n
                            node_connected = True

                # if the node is not connected to the target chain, we
                # need to find the end of the window
                if not node_connected:
                    print("Node: {}".format(node[0]))
                    print("Start of window: {}".format(start_of_window))

                    end_of_window = None
                    for n, tcn in enumerate(target_chain_nodes):
                        if n >= start_of_window:
                            if tcn[0] == current_chain_nodes[-1][0]:
                                end_of_window = n
                            tcn_warp_edges = self.NodeWarpEdges(tcn[0],
                                                                data=False)
                            tcn_warp_edge_targets = [we[1] for we \
                                                     in tcn_warp_edges]
                            for twet in tcn_warp_edge_targets:
                                if (twet in [cn[0] for cn \
                                             in current_chain_nodes]):
                                    end_of_window = n
                                    break
                        if end_of_window:
                            break

                    if start_of_window != -1 and end_of_window != None:
                        if end_of_window == len(target_chain_nodes)-1:
                            window = target_chain_nodes[start_of_window:]
                        else:
                            window = target_chain_nodes[start_of_window: \
                                                        end_of_window+1]

                        print("End of window: {}".format(end_of_window))
                        self._create_second_pass_warp_connection(
                                                            current_chain_nodes,
                                                            k,
                                                            window,
                                                            precise=False,
                                                            verbose=False)

# MAIN -------------------------------------------------------------------------
if __name__ == '__main__':
    pass
