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

    # INITIAL CONNECTION METHODS -----------------------------------------------

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

    def CreateLeafConnections(self):
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

    # WEFT CONNECTION CREATION -------------------------------------------------

    def _create_initial_weft_connections(self, contourSet, precise=False, verbose=False):
        """
        Private method for creating initial 'weft' connections for the supplied
        set of contours, starting from the first contour in the set and
        propagating to the last contour in the set.
        """

        if len(contourSet) < 2:
            if verbose:
                print("Not enough contours in contour set!")
            return

        # print info on verbose output
        if verbose:
            print("Creating initial 'weft' connections for contour set...")

        # loop over all vertices of positions (list of lists of tuples)
        for i, pos in enumerate(contourSet):
            # pos is a list of tuples (nodes)
            if i < len(contourSet):
                j = i + 1
                if j == len(contourSet):
                    break
                # get initial and target vertices without 'leaf' nodes
                initial_vertices = contourSet[i][1:-1]
                target_vertices = contourSet[j][1:-1]

                # loop through all nodes on the current position
                for k, node in enumerate(initial_vertices):
                    # find four closest vertices on target
                    thisPt = node[1]["geo"]

                    # print info on verbose setting
                    if verbose:
                        vStr = "Processing node {} on position {}:"
                        vStr = vStr.format(node[0], node[1]["position"])
                        print(vStr)

                    # get four closest verts on adjacent contour
                    if precise:
                        allDists = [thisPt.DistanceTo(tv[1]["geo"]) \
                                    for tv in target_vertices]
                    else:
                        allDists = [thisPt.DistanceToSquared(tv[1]["geo"]) \
                                    for tv in target_vertices]
                    allDists, sorted_target_vertices = zip(
                                *sorted(zip(allDists,
                                            target_vertices),
                                            key = operator.itemgetter(0)))
                    possible_connections = sorted_target_vertices[:4]

                    # print info on verbose setting
                    if verbose:
                        vStr = "Possible connections: {}"
                        vStr = vStr.format([pc[0] for pc in \
                                           possible_connections])
                        print(vStr)

                    # get the contours current direction
                    if k < len(initial_vertices)-1:
                        contourDir = Rhino.Geometry.Line(thisPt,
                                 initial_vertices[k+1][1]["geo"]).Direction
                    elif k == len(initial_vertices)-1:
                        contourDir = Rhino.Geometry.Line(
                         initial_vertices[k-1][1]["geo"], thisPt).Direction
                    contourDir.Unitize()

                    # get the directions of the possible connections
                    candidatePoints = [pc[1]["geo"] \
                                       for pc in possible_connections]
                    candidateDirections = [Rhino.Geometry.Line(
                            thisPt, cp).Direction for cp in candidatePoints]
                    [cd.Unitize() for cd in candidateDirections]

                    # get the angles between contour dir and possible dir
                    normals = [Rhino.Geometry.Vector3d.CrossProduct(
                              contourDir, cd) for cd in candidateDirections]
                    angles = [Rhino.Geometry.Vector3d.VectorAngle(
                              contourDir, cd, n) for cd, n in zip(
                                              candidateDirections, normals)]

                    # compute deltas as a mesaure of perpendicularity
                    deltas = [abs(a - (0.5 * math.pi)) for a in angles]

                    # sort possible connections by delta and distance
                    allDists, deltas, angles, most_perpendicular = zip(
                            *sorted(zip(allDists,
                                        deltas,
                                        angles,
                                        possible_connections[:]),
                                        key = operator.itemgetter(0, 1)))

                    # get node neighbours
                    nNeighbours = self[node[0]]

                    # compute angle difference
                    aDelta = angles[0] - angles[1]

                    # CONNECTION FOR LEAST ANGLE CHANGE --------------------
                    if len(nNeighbours) > 2 and aDelta < math.radians(6.0):
                        # print info on verbose setting
                        if verbose:
                            print("Using procedure for least angle " +
                                  "change connection...")

                        # get previous pos verts, indices and connections
                        prevPos = contourSet[i-1]
                        prevIndices = [n[0] for n in prevPos]

                        # get previous connected edge and its direction
                        prevEdges = self.NodeWeftEdges(node[0], data=True)

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
                        dirA = Rhino.Geometry.Line(
                                            thisPt, mpA[1]["geo"]).Direction
                        dirA.Unitize()
                        dirB = Rhino.Geometry.Line(
                                            thisPt, mpB[1]["geo"]).Direction
                        dirB.Unitize()

                        # get normals for angle measurement
                        normalA = Rhino.Geometry.Vector3d.CrossProduct(
                                                              prevDir, dirA)
                        normalB = Rhino.Geometry.Vector3d.CrossProduct(
                                                              prevDir, dirB)

                        # measure the angles
                        angleA = Rhino.Geometry.Vector3d.VectorAngle(
                                                     prevDir, dirA, normalA)
                        angleB = Rhino.Geometry.Vector3d.VectorAngle(
                                                     prevDir, dirB, normalB)

                        # select final candidate for connection
                        if angleA < angleB:
                            fCand = mpA
                        else:
                            fCand = mpB

                        # connect to final candidate
                        connecting_neighbours = self[fCand[0]]
                        if len(connecting_neighbours) < 4:
                            isConnected = False
                            for cn in connecting_neighbours:
                                if cn in [v[0] for v in initial_vertices]:
                                    isConnected = True
                                    # print info on verbose setting
                                    if verbose:
                                        vStr = ("Candidate node {} is " +
                                                "already connected! " +
                                                "Skipping to next " +
                                                "node...")
                                        vStr = vStr.format(fCand[0])
                                        print(vStr)
                            if not isConnected:
                                # print info on verbose setting
                                if verbose:
                                    vStr = ("Connecting node {} to best " +
                                            "candidate {}.")
                                    vStr = vStr.format(node[0], fCand[0])
                                    print(vStr)
                                self.CreateWeftEdge(node, fCand)

                    # CONNECTION FOR MOST PERPENDICULAR --------------------
                    else:
                        # print info on verbose setting
                        if verbose:
                            print("Using procedure for most " +
                                  "perpendicular connection...")
                        fCand = most_perpendicular[0]
                        connecting_neighbours = self[fCand[0]]
                        if len(connecting_neighbours) < 4:
                            isConnected = False
                            for cn in connecting_neighbours:
                                if cn in [v[0] for v in initial_vertices]:
                                    isConnected = True
                                    # print info on verbose setting
                                    if verbose:
                                        vStr = ("Candidate node {} is " +
                                                "already connected! " +
                                                "Skipping to next " +
                                                "node...")
                                        vStr = vStr.format(fCand[0])
                                        print(vStr)
                            if not isConnected:
                                fCand = most_perpendicular[0]
                                if verbose:
                                    vStr = ("Connecting node {} to best " +
                                            "candidate {}.")
                                    vStr = vStr.format(node[0], fCand[0])
                                    print(vStr)
                                self.CreateWeftEdge(node, fCand)

    def _create_second_pass_weft_connections(self, contourSet, precise=False, verbose=False):
        """
        Private method for creating second pass 'weft' connections for the
        given set of contours.
        """

        # TODO: check if its better to connect to the least connected node in window!

        if len(contourSet) < 2:
            if verbose:
                print("Not enough contours in contour set!")
            return

        # print info on verbose output
        if verbose:
            print("Creating second pass 'weft' connections for contour set...")

        # get attributes only once
        position_attributes = nx.get_node_attributes(self, "position")
        num_attributes = nx.get_node_attributes(self, "num")

        # loop over all vertices of positions (list of lists of tuples)
        for i, pos in enumerate(contourSet):
            j = i + 1

            # get initial vertices without 'leaf' nodes
            initial_vertices = contourSet[i]

            # get target position candidates
            if (i > 0 and i < len(contourSet)-1 and \
                i != 0 and i != len(contourSet)-1):
                target_positionA = contourSet[i-1][0][1]["position"]
                target_positionB = contourSet[i+1][0][1]["position"]
            elif i == 0:
                target_positionA = None
                target_positionB = contourSet[i+1][0][1]["position"]
            elif i == len(contourSet)-1:
                target_positionA = contourSet[i-1][0][1]["position"]
                target_positionB = None

            # loop through all nodes on current position
            for k, node in enumerate(initial_vertices):
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
                    target_vertices = self.NodesOnPosition(target_position,
                                                           True)

                    # get the point geo of this node
                    thisPt = node[1]["geo"]

                    # get a window of possible connections on the target
                    # position by looking for the previos vertex on this contour
                    # connected to target position, then propagating along
                    # the target position to the next node that is connected
                    # to this position. these two nodes will define the window

                    # NOTE: the current vertex should never have a connection
                    # to target position (theoertically), otherwise it should
                    # have fallen through the checks by now

                    # print info on verbose setting
                    if verbose:
                        vStr = "Target position is {}. Computing window..."
                        vStr = vStr.format(target_position)
                        print(vStr)

                    # get the previous node on this contour
                    prevNode = initial_vertices[k-1]

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
                                           target_vertices[prevNodeTargetIndex])

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
                    if k < len(initial_vertices)-1:
                        future_nodes = initial_vertices[k+1:]
                        for futurenode in future_nodes:
                            filteredWeftEdges = []
                            futureWeftEdges = self.NodeWeftEdges(futurenode[0],
                                                                 data=True)
                            for futureweft in futureWeftEdges:
                                fwn = (futureweft[1], self.node[futureweft[1]])
                                # NOTE: OLD VERSION BELOW
                                # fwn = self.nodes(data=True)[futureweft[1]]
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
                            # NOTE: OLD VERSION BELOW
                            # end_of_window = self.nodes(
                            #                 data=True)[filteredWeftEdges[0][1]]
                            break
                    else:
                        end_of_window = None

                    # define the window
                    if end_of_window == None:
                        window = [start_of_window]
                    elif end_of_window == start_of_window:
                        window = [start_of_window]
                    else:
                        window = self.nodes(
                               data=True)[start_of_window[0]:end_of_window[0]+1]

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

                        # get four closest verts on adjacent contour
                        if precise:
                            allDists = [thisPt.DistanceTo(pc[1]["geo"]) \
                                        for pc in window]
                        else:
                            allDists = [thisPt.DistanceToSquared(pc[1]["geo"]) \
                                        for pc in window]
                        allDists, window = zip(*sorted(zip(allDists, window),
                                               key = operator.itemgetter(0)))

                        # get the contours current direction
                        if k < len(initial_vertices)-1:
                            contourDir = Rhino.Geometry.Line(
                                    thisPt,
                                    initial_vertices[k+1][1]["geo"]).Direction
                        elif k == len(initial_vertices)-1:
                            contourDir = Rhino.Geometry.Line(
                                    initial_vertices[k-1][1]["geo"],
                                    thisPt).Direction
                        contourDir.Unitize()

                        # get the directions of the possible connections
                        candidatePoints = [pc[1]["geo"] \
                                           for pc in window]
                        candidateDirections = [Rhino.Geometry.Line(
                                                thisPt, cp).Direction \
                                                for cp in candidatePoints]
                        [cd.Unitize() for cd in candidateDirections]

                        # get the angles between contour dir and possible dir
                        normals = [Rhino.Geometry.Vector3d.CrossProduct(
                                   contourDir, cd) \
                                   for cd in candidateDirections]
                        angles = [Rhino.Geometry.Vector3d.VectorAngle(
                                  contourDir, cd, n) for cd, n in zip(
                                                candidateDirections, normals)]

                        # compute deltas as a mesaure of perpendicularity
                        deltas = [abs(a - (0.5 * math.pi)) for a in angles]

                        # sort possible connections by delta
                        allDists, deltas, angles, most_perpendicular = zip(
                                *sorted(zip(allDists,
                                            deltas,
                                            angles,
                                            window),
                                            key = operator.itemgetter(0, 1)))

                        # print info on verbose setting
                        if verbose:
                            vStr = ("Connecting to node {} on " +
                                    "position {}...")
                            vStr = vStr.format(most_perpendicular[0][0],
                                        most_perpendicular[0][1]["position"])
                            print(vStr)

                        # connect weft edge to best target
                        self.CreateWeftEdge(node, most_perpendicular[0])

    def _create_initial_warp_connections(self, contourSet, verbose=False):
        """
        Private method for initializing first 'warp' connections once
        all 'weft' connections are made.
        """

        for i, pos in enumerate(contourSet):
            # get all vertices on current contour
            initial_vertices = contourSet[i]

            # loop through all nodes on this contour
            for k, node in enumerate(initial_vertices):
                connected_edges = self.edges(node[0], data=True)
                numweft = len(self.NodeWeftEdges(node[0]))
                if len(connected_edges) > 4 or numweft > 2 or i == 0 or i == len(contourSet)-1:
                    # set 'end' attribute for this node
                    self.node[node[0]]["end"] = True
                    # NOTE: OLD VERSION BELOW
                    # self.nodes(data=True)[node[0]][1]["end"] = True

                    # loop through all candidate edges
                    for j, edge in enumerate(connected_edges):

                        # if it's not a 'weft' edge, assign attributes
                        if not edge[2]["weft"]:
                            connected_node = edge[1]
                            # set 'end' attribute to conneted node
                            self.node[connected_node]["end"] = True
                            # NOTE: OLD VERSION BELOW
                            # self.nodes(data=True)[connected_node][1]["end"] = True
                            # set 'warp' attribute to current edge
                            self[edge[0]][edge[1]]["warp"] = True

    def CreateWeftConnections(self, startIndex=None, precise=False, verbose=False):
        """
        Attempts to create all the 'weft' connections for the network.
        """

        # get all the positions / contours
        AllPositions = self.AllNodesByPosition(True)

        if startIndex == None:
            # get index of longest contour
            startIndex = self.LongestPositionContour()[0]
        elif startIndex >= len(AllPositions):
            raise RuntimeError("Supplied splitting index is too high!")

        # split position list into two sets based on start index
        leftContours = AllPositions[0:startIndex+1]
        leftContours.reverse()
        rightContours = AllPositions[startIndex:]

        # create the initial weft connections
        self._create_initial_weft_connections(leftContours, precise, verbose)
        self._create_initial_weft_connections(rightContours, precise, verbose)

        # create second pass weft connections
        self._create_second_pass_weft_connections(leftContours,
                                                  precise,
                                                  verbose)
        self._create_second_pass_weft_connections(rightContours,
                                                  precise,
                                                  verbose)

        # initialize first warp connections once all weft connections are made
        self._create_initial_warp_connections(AllPositions)

        return True

    # SEGMENTATION FOR LOOP GENERATION -----------------------------------------

    def _traverse_edge_until_end(self, startEndNode, startNode, wayNodes=None, wayEdges=None, endNodes=None):
        """
        Private method for traversing a path of 'weft' edges until another
        'end' node is discoverd.
        """

        # initialize output lists
        if wayNodes == None:
            wayNodes = deque()
            wayNodes.append(startNode[0])
        if wayEdges == None:
            wayEdges = deque()
        if endNodes == None:
            endNodes = deque()

        connected_weft_edges = self.edges(startNode[0], data=True)
        filtered_weft_edges = []
        for cwe in connected_weft_edges:
            if cwe[2]["segment"] != None:
                continue
            if cwe in wayEdges:
                continue
            elif (cwe[1], cwe[0], cwe[2]) in wayEdges:
                continue
            filtered_weft_edges.append(cwe)

        if len(filtered_weft_edges) > 1:
            print(filtered_weft_edges)
            print("More than one filtered candidate weft edge!")
        elif len(filtered_weft_edges) == 1:
            fwec = filtered_weft_edges[0]

            connected_node = self.TraverseEdge(startNode[0],
                                                 fwec)

            # if the connected node is an end node, the segment is finished
            if connected_node[1]["end"]:
                # find out which order to set segment attributes
                if startEndNode > connected_node[0]:
                    segStart = connected_node[0]
                    segEnd = startEndNode
                else:
                    segStart = startEndNode
                    segEnd = connected_node[0]

                endNodes.append(connected_node[0])
                wayEdges.append(fwec)

                # TODO: implement third value in tuple for index of segment
                for waynode in wayNodes:
                    self.node[waynode]["segment"] = (segStart, segEnd)
                for wayedge in wayEdges:
                    self[wayedge[0]][wayedge[1]]["segment"] = (segStart, segEnd)

            else:
                # TODO: implement third value in tuple for index of segment
                # set the initial segment attribute to the node
                self.node[connected_node[0]]["segment"] = (startEndNode, None)

                # set the initial segment attribute to the edge
                self[fwec[0]][fwec[1]]["segment"] = (startEndNode, None)

                wayNodes.append(connected_node[0])
                wayEdges.append(fwec)

                self._traverse_edge_until_end(startEndNode,
                                              connected_node,
                                              wayNodes,
                                              wayEdges,
                                              endNodes)
        else:
            return None

    def _get_segmentation_for_end_node(self, node):
        """
        Traverse a path of 'weft' edges starting from an 'end' node until
        another 'end' node is discovered. Set 'segment' attributes to nodes
        and egdes on the way.
        """

        # get connected weft edges
        weft_connections = self.edges(node[0], data=True)

        # loop through all connected weft edges
        seen_segments = []
        for cwe in weft_connections:
            if cwe[2]["segment"]:
                continue

            # check the next connected node. if it is an end vertex,
            # set the respective keys
            connected_node = self.TraverseEdge(node[0], cwe)

            if connected_node[1]["end"]:
                if node[0] > connected_node[0]:
                    segStart = connected_node[0]
                    segEnd = node[0]
                else:
                    segStart = node[0]
                    segEnd = connected_node[0]

                # set the final segment attribute to the edge
                # TODO: segment attribute needs a third value as index to cope
                # with the special edge case <====> (two segments have the
                # same start and end)
                self[cwe[0]][cwe[1]]["segment"] = (segStart, segEnd)

            else:
                self._traverse_edge_until_end(node[0],
                                              connected_node,
                                              wayEdges=[cwe])

    def GetWeftEdgeSegmentation(self):
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

        # get all 'end' vertices ordered by poition
        all_ends_by_position = self.AllEndsByPosition(data=True)

        # loop through all 'end' vertices
        for position in all_ends_by_position:
            for endnode in position:
                self._get_segmentation_for_end_node(endnode)

        # add all previously removed edges back into the network

        [self.add_edge(edge[0], edge[1], edge[2]) for edge in \
         warp_storage + contour_storage]

    # CREATE MAPPING NETWORK ---------------------------------------------------

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

        segment_ids = deque()
        for edge in WeftEdges:
            segment_id = edge[2]["segment"]
            if not segment_id in segment_ids:
                segment_ids.append(segment_id)

        for id in segment_ids:
            segment_edges = [e for e in WeftEdges if e[2]["segment"] == id]
            segment_edges.sort(key=lambda x: x[0])

            startNode = (id[0], self.node[id[0]])
            endNode = (id[1], self.node[id[1]])

            segment_geo = [e[2]["geo"] for e in segment_edges]

            res = MappingNetwork.CreateSegmentContourEdge(startNode,
                                                          endNode,
                                                          segment_geo)

            # half-assed bug checking
            if not res:
                print id

        [MappingNetwork.add_edge(e[0], e[1], e[2]) for e in WarpEdges]

        return MappingNetwork
