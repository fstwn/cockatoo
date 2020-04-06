# PYTHON LIBRARY IMPORTS
from __future__ import division
import math
from operator import itemgetter
from collections import deque

# RHINO IMPORTS
from Rhino.Geometry import Line as RGLine
from Rhino.Geometry import Vector3d as RGVector3d

# CUSTOM MODULE IMPORTS
import networkx as nx

# SUBMODULE IMPORTS
from KnitNetworkBase import KnitNetworkBase
from KnitMappingNetwork import KnitMappingNetwork

class KnitNetwork(KnitNetworkBase):

    """
    Class for representing a network that facilitates the automatic generation
    of knitting patterns based on Rhino geometry.
    """

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
        Creates all initial position contour edges as neither 'warp' nor 'weft'.
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
        Creates all initial connections of the 'leaf' nodes.
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
        node. Returns True if the connection has been made, otherwise false.
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
        mathPi = math.pi
        mathRadians = math.radians
        selfAttemptWeftConnection = self.AttemptWeftConnectionToCandidate
        selfNodeWeftEdges = self.NodeWeftEdges

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
                        res = selfAttemptWeftConnection(node,
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
                        contourDir = RGLine(thisPt,
                                         initial_nodes[k+1][1]["geo"]).Direction
                    elif k == len(initial_nodes)-1:
                        contourDir = RGLine(
                                 initial_nodes[k-1][1]["geo"], thisPt).Direction
                    contourDir.Unitize()

                    # get the directions of the possible connections
                    candidatePoints = [pc[1]["geo"] \
                                       for pc in possible_connections]
                    candidateDirections = [RGLine(
                                thisPt, cp).Direction for cp in candidatePoints]
                    [cd.Unitize() for cd in candidateDirections]

                    # get the angles between contour dir and possible conn dir
                    normals = [RGVector3d.CrossProduct(
                                  contourDir, cd) for cd in candidateDirections]
                    angles = [RGVector3d.VectorAngle(
                              contourDir, cd, n) for cd, n in zip(
                              candidateDirections, normals)]

                    # compute deltas as a mesaure of perpendicularity
                    deltas = [abs(a - (0.5 * mathPi)) for a in angles]

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
                    if len(nNeighbours) > 2 and aDelta < mathRadians(6.0):
                        # print info on verbose setting
                        if verbose:
                            print("Using procedure for least angle " +
                                  "change connection...")

                        # get previous pos verts, indices and connections
                        prevPos = contour_set[i-1]
                        prevIndices = [n[0] for n in prevPos]

                        # get previous connected edge and its direction
                        prevEdges = selfNodeWeftEdges(node[0], data=True)
                        if len(prevEdges) > 1:
                            raise RuntimeError("More than one previous " +
                                  "weft connection! This was unexpected...")
                            prevDir = prevEdges[0][2]["geo"].Direction
                        else:
                            prevDir = prevEdges[0][2]["geo"].Direction
                        prevDir.Unitize()

                        # get directions for the best two candidates
                        mpA = most_perpendicular[0]
                        mpB = most_perpendicular[1]
                        dirA = RGLine(thisPt, mpA[1]["geo"]).Direction
                        dirB = RGLine(thisPt, mpB[1]["geo"]).Direction
                        dirA.Unitize()
                        dirB.Unitize()

                        # get normals for angle measurement
                        normalA = RGVector3d.CrossProduct(prevDir, dirA)
                        normalB = RGVector3d.CrossProduct(prevDir, dirB)

                        # measure the angles
                        angleA = RGVector3d.VectorAngle(prevDir, dirA, normalA)
                        angleB = RGVector3d.VectorAngle(prevDir, dirB, normalB)

                        # select final candidate for connection by angle
                        if angleA < angleB:
                            fCand = mpA
                        else:
                            fCand = mpB

                        # attempt to connect to final candidate
                        res = selfAttemptWeftConnection(node,
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
                        res = selfAttemptWeftConnection(node,
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
        mathPi = math.pi
        selfNode = self.node
        selfNodeWeftEdges = self.NodeWeftEdges
        selfNodesOnPosition = self.NodesOnPosition
        selfCreateWeftEdge= self.CreateWeftEdge

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
                conWeftEdges = selfNodeWeftEdges(node[0], data=True)
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
                    target_nodes = selfNodesOnPosition(target_position, True)

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
                    prevCon = selfNodeWeftEdges(prevNode[0], data=True)

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
                            futureWeftEdges = selfNodeWeftEdges(futurenode[0],
                                                                 data=True)
                            for futureweft in futureWeftEdges:
                                fwn = (futureweft[1], selfNode[futureweft[1]])
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
                                             selfNode[filteredWeftEdges[0][1]])

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
                        selfCreateWeftEdge(node, window[0])
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
                                contourDir = RGLine(
                                        thisPt,
                                        initial_nodes[k+1][1]["geo"]).Direction
                            elif k == len(initial_nodes)-1:
                                contourDir = RGLine(
                                        initial_nodes[k-1][1]["geo"],
                                        thisPt).Direction
                            contourDir.Unitize()

                            # get the directions of the possible connections
                            candidatePoints = [pc[1]["geo"] \
                                               for pc in window]
                            candidateDirections = [RGLine(
                                                    thisPt, cp).Direction \
                                                    for cp in candidatePoints]
                            [cd.Unitize() for cd in candidateDirections]

                            # get the angles between contour dir and window dir
                            normals = [RGVector3d.CrossProduct(
                                       contourDir, cd) \
                                       for cd in candidateDirections]
                            angles = [RGVector3d.VectorAngle(
                                      contourDir, cd, n) for cd, n in zip(
                                                candidateDirections, normals)]

                            # compute deltas as a mesaure of perpendicularity
                            deltas = [abs(a - (0.5 * mathPi)) for a in angles]

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
                        selfCreateWeftEdge(node, fCand)

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
            raise RuntimeError("Supplied splitting index is too high!")

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

        # namespace mapping for performance gains
        selfEdges = self.edges
        selfNode = self.node
        selfNodeWeftEdges = self.NodeWeftEdges

        # if no contour set is provided, use all contours of this network
        if contour_set == None:
            contour_set = self.AllNodesByPosition(True)

        # loop through all positions in the set of contours
        for i, pos in enumerate(contour_set):
            # get all vertices on current contour
            initial_nodes = contour_set[i]

            # loop through all nodes on this contour
            for k, node in enumerate(initial_nodes):
                connected_edges = selfEdges(node[0], data=True)
                numweft = len(selfNodeWeftEdges(node[0]))
                if (len(connected_edges) > 4 or numweft > 2 \
                    or i == 0 or i == len(contour_set)-1):
                    # set 'end' attribute for this node
                    selfNode[node[0]]["end"] = True

                    # loop through all candidate edges
                    for j, edge in enumerate(connected_edges):
                        # if it's not a 'weft' edge, assign attributes
                        if not edge[2]["weft"]:
                            connected_node = edge[1]
                            # set 'end' attribute to conneted node
                            selfNode[connected_node]["end"] = True
                            # set 'warp' attribute to current edge
                            self[edge[0]][edge[1]]["warp"] = True

    # ASSIGNING OF 'SEGMENT' ATTRIBUTES FOR LOOP GENERATION --------------------

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

    # TRANSLATION TO MAPPING NETWORK -------------------------------------------

    def CreateMappingNetwork(self):
        """
        Creates a KnitMappingNetwork from a KnitNetwork with fully
        assigned 'weft' edge segmentation.
        """

        # copy the input network to not mess with previous components
        MappingNetwork = KnitMappingNetwork()

        # get all edges by segment
        WeftEdges = sorted(self.WeftEdges, key=lambda x: x[2]["segment"])
        WarpEdges = self.WarpEdges

        # initialize deque container for segment ids
        segment_ids = deque()
        # loop through all 'weft' edges and fill container with unique ids
        for edge in WeftEdges:
            segment_id = edge[2]["segment"]
            if not segment_id in segment_ids:
                segment_ids.append(segment_id)

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

            # half-assed bug checking
            if not res:
                print id

        [MappingNetwork.add_edge(e[0], e[1], attr_dict=e[2]) for e in WarpEdges]

        return MappingNetwork
