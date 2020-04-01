# PYTHON LIBRARY IMPORTS
from __future__ import division
import math
from operator import itemgetter
from collections import deque

# RHINO IMPORTS
from Rhino.Geometry import Line as RGLine
from Rhino.Geometry import Vector3d as RGVector3d
from Rhino.Geometry import Interval as RGInterval
from Rhino.Geometry import PolylineCurve as RGPolylineCurve

# CUSTOM MODULE IMPORTS
import networkx as nx

# SUBMODULE IMPORTS
from KnitNetworkBase import KnitNetworkBase

class KnitMappingNetwork(nx.MultiGraph, KnitNetworkBase):

    """
    Class for representing a mapping network that facilitates the automatic
    generation of knitting patterns based on Rhino geometry.
    This is intended only to be instanced by a fully segmented instance of
    KnitNetwork.
    """

    def ToString(self):
        """
        Return a textual description of the network.
        """

        name = "KnitMappingNetwork"
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
        SegmentContourEdges = [(f, t, d) for f, t, d \
                               in self.edges_iter(data=True) \
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

    # NODE METHODS -------------------------------------------------------------

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

    def AllNodesBySegment(self, data=False, edges=False):
        """
        Returns all 'segment' nodes of the network ordered by 'segment'
        attribute.
        Note: 'end' nodes are not included!
        """

        allSegments = self.SegmentContourEdges

        anbs = []
        for i, segment in enumerate(allSegments):
            segval = segment[2]["segment"]
            segnodes = self.NodesOnSegment(segment[2]["segment"], data=True)
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

    def EndNodeSegmentsByStart(self, node, data=False):
        """
        Get all the segments which share a given 'end' node at the start
        and sort them by their 'segment' value
        """

        connected_segments = [(s, e, d) for s, e, d \
                              in self.edges_iter(node, data=True) if
                              not d["warp"] and not d["weft"]]
        connected_segments = [cs for cs in connected_segments \
                              if cs[2]["segment"] != None]
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
                              if cs[2]["segment"] != None]
        connected_segments = [cs for cs in connected_segments \
                              if cs[2]["segment"][1] == node]

        connected_segments.sort(key=lambda x: x[2]["segment"])

        if data:
            return connected_segments
        else:
            return [(cs[0], cs[1]) for cs in connected_segments]

    # SAMPLING OF SEGMENT CONTOURS ---------------------------------------------

    def SampleSegmentContours(self, stitch_width):
        """
        Sample the segment contours of the mapping network with the given
        stitch width. Add the resulting points as nodes to the network.
        """

        # namespace mapping for performance gains
        selfNodeFromPoint3d = self.NodeFromPoint3d
        selfNode = self.node

        # get the highest index of all the nodes in the network
        maxNode = max(self.nodes())

        # get all the segment geometry ordered by segment number
        segment_contours = self.SegmentContourEdges

        # sample all segments with the stitch width
        nodeindex = maxNode + 1
        newPts = []
        for i, seg in enumerate(segment_contours):
            # get the geometry of the contour and reparametreize its domain
            geo = seg[2]["geo"]
            geo = geo.ToPolylineCurve()
            geo.Domain = RGInterval(0.0, 1.0)

            # compute the division points
            crvlen = geo.GetLength()
            density = int(round(crvlen / stitch_width))
            if density == 0:
                continue
            divT = geo.DivideByCount(density, False)
            divPts = [geo.PointAt(t) for t in divT]

            # set leaf attribute
            if selfNode[seg[0]]["leaf"] and selfNode[seg[1]]["leaf"]:
                nodeLeaf = True
            else:
                nodeLeaf = False

            # add all the nodes to the network
            for j, pt in enumerate(divPts):
                # add node to network

                selfNodeFromPoint3d(nodeindex,
                                    pt,
                                    position = None,
                                    num = j,
                                    leaf = nodeLeaf,
                                    end = False,
                                    segment = seg[2]["segment"])
                # increment node index
                nodeindex += 1

    # CREATION OF WEFT CONNECTIONS ---------------------------------------------

    def CreateWeftConnections(self):
        """
        Loop through all the segment contours and create all 'weft' connections
        for this network.
        """

        # namespace mapping for performance gains
        selfNode = self.node
        selfCreateWeftEdge = self.CreateWeftEdge

        # get all nodes by segment contour
        SegmentValues, AllNodesBySegment = zip(*self.AllNodesBySegment(True))

        # loop through all the segment contours
        for i, segment in enumerate(AllNodesBySegment):
            segval = SegmentValues[i]
            firstNode = (segval[0], selfNode[segval[0]])
            lastNode = (segval[1], selfNode[segval[1]])

            if len(segment) == 0:
                print("Segment is empty!")
                selfCreateWeftEdge(firstNode, lastNode, segval)
            elif len(segment) == 1:
                selfCreateWeftEdge(firstNode, segment[0], segval)
                selfCreateWeftEdge(segment[0], lastNode, segval)
            else:
                # loop through all nodes on the current segment
                for j, node in enumerate(segment):
                    if j == 0:
                        selfCreateWeftEdge(firstNode, node, segval)
                        selfCreateWeftEdge(node, segment[j+1], segval)
                    elif j < len(segment)-1:
                        selfCreateWeftEdge(node, segment[j+1], segval)
                    elif j == len(segment)-1:
                        selfCreateWeftEdge(node, lastNode, segval)

    # CREATION OF WARP CONNECTIONS ---------------------------------------------

    def _attempt_warp_connection_to_candidate(self, node, candidate, segment_nodes, max_connections=4, verbose=False):
        """
        Private method for attempting a 'warp' connection to a candidate
        node.
        """

        connecting_neighbours = self[candidate[0]]
        if len(connecting_neighbours) < max_connections:
            isConnected = False
            for cn in connecting_neighbours:
                if cn in [v[0] for v in segment_nodes]:
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

                self.CreateWarpEdge(node, candidate)

    def _create_warp_connections(self, segment_pair, max_connections=4, precise=False, verbose=False):
        """
        Private method for creating initial 'warp' connections for the supplied
        pair of segment chains.
        The pairs are only defined as a set of nodes
        """

        # TODO: use forbidden node setting to avoid crossing connections!
        # see _create_initial_weft_connections for reference

        # namespace mapping for performance gains
        mathPi = math.pi
        mathRadians = math.radians
        selfAttemptWarpConnection = self._attempt_warp_connection_to_candidate

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
                # attempt to connct to only possible candidate
                fCand = possible_connections[0]
                selfAttemptWarpConnection(node,
                                          fCand,
                                          initial_nodes,
                                          max_connections=max_connections,
                                          verbose=verbose)
                continue

            # get the segment contours current direction
            if k < len(initial_nodes)-1:
                contourDir = RGLine(thisPt,
                                         initial_nodes[k+1][1]["geo"]).Direction
            elif k == len(initial_nodes)-1:
                contourDir = RGLine(
                                 initial_nodes[k-1][1]["geo"], thisPt).Direction
            contourDir.Unitize()

            # get the directions of the possible connections
            candidatePoints = [pc[1]["geo"] for pc in possible_connections]
            candidateDirections = [RGLine(
                                thisPt, cp).Direction for cp in candidatePoints]
            [cd.Unitize() for cd in candidateDirections]

            # get the angles between segment contour dir and possible conn dir
            normals = [RGVector3d.CrossProduct(
                                  contourDir, cd) for cd in candidateDirections]
            angles = [RGVector3d.VectorAngle(
                      contourDir, cd, n) for cd, n in zip(
                      candidateDirections, normals)]

            # compute deltas as a measure of perpendicularity
            deltas = [abs(a - (0.5 * mathPi)) for a in angles]

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
            if len(nNeighbours) > 2 and aDelta < mathRadians(6.0):
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

                # select final candidate for connection
                if angleA < angleB:
                    fCand = mpA
                else:
                    fCand = mpB

                # attempt connection to final candidate
                selfAttemptWarpConnection(node,
                                          fCand,
                                          initial_nodes,
                                          max_connections=max_connections,
                                          verbose=verbose)

            # CONNECTION FOR MOST PERPENDICULAR --------------------------------
            else:
                # print info on verbose setting
                if verbose:
                    print("Using procedure for most " +
                          "perpendicular connection...")
                # define final candidate node
                fCand = most_perpendicular[0]
                # attempt connection to final candidate
                selfAttemptWarpConnection(node,
                                          fCand,
                                          initial_nodes,
                                          max_connections=max_connections,
                                          verbose=verbose)

    def _traverse_segment_until_warp(self, waySegments, down=False):
        """
        Private method for traversing a path of 'segment' edges until a 'warp'
        edge is discovered which points to the previous or the next segment.
        Returns the ids of the segment array
        """

        segment_list = waySegments
        flag = False
        i = 0
        while flag == False and i < 10000:
            # set the current segment
            current_segment = segment_list[-1]

            # check that segment for a 'warp' edge
            warp_edges_at_end = self.NodeWarpEdges(current_segment[1])
            if down:
                filtered_warp_edges = [we for we in warp_edges_at_end \
                                       if we[1] == current_segment[1]-1]
            else:
                filtered_warp_edges = [we for we in warp_edges_at_end \
                                       if we[1] == current_segment[1]+1]

            # if there is a warp edge at the end, return the segment_list
            if len(filtered_warp_edges) != 0 or (len(warp_edges_at_end) == 1 and self.node[current_segment[1]]["leaf"]):
                flag = True
                break

            # get all connected segments at the last point of the segment
            connected_segments_at_end = self.EndNodeSegmentsByStart(current_segment[1], data=True)

            # from these, only get the segment with the lowest id
            if len(connected_segments_at_end) > 0:
                if down:
                    candidate_segment = connected_segments_at_end[0]
                else:
                    candidate_segment = connected_segments_at_end[-1]
                # append the segment to the segment_list
                segment_list.append(candidate_segment[2]["segment"])
            else:
                break

            i += 1

        return segment_list

    def CreateWarpConnections(self, max_connections=4, include_end_nodes=True, precise=False, verbose=False):
        """
        Create the final 'warp' connection by looping through all initial 'warp'
        edges of the mapping network. Traverse all connected segment contour
        edges to build chains of segment contour edges.
        Loop through all the found chains and find a target chain to connect
        to using an 'educated guessing' strategy. This means that the possible
        ids of the target segment chain are guessed by using known topology
        facts about the network. and its special 'end' nodes.

        Parameters
        ----------
        max_connections : integer
            The number of maximum previous connections a candidate node for a
            'warp' connection is allowed to have.

        Returns
        -------
        None

        Notes
        -----
        None

        Examples
        --------
        None
        """

        # TODO: Still some unsolved cases and first solving approach was
        #       yielding duplicate segments and "reverse" connections.
        #       New idea: split the dicts and lists in source and target chains,
        #       only loop through source chains and only search in target
        #       chains?

        # TODO 2: include 'end' nodes between segments in a chain of segments
        #         in the current and target nodes for 'warp' edge creation

        # TODO 3: store all connections that were made as a mapping for the
        #         second pass loop.


        # namespace mapping for performance gains
        selfNode = self.node
        selfEndNodeSegmentsByStart = self.EndNodeSegmentsByStart
        self_traverse_segment_until_warp = self._traverse_segment_until_warp
        self_create_warp_connections = self._create_warp_connections

        # get all segment ids, nodes per segment and edges
        SegmentValues, AllNodesBySegment, SegmentContourEdges = zip(
                                 *self.AllNodesBySegment(data=True, edges=True))

        # build a dictionary of the segments by their index
        SegmentDict = dict(zip(SegmentValues,
                               zip(SegmentContourEdges, AllNodesBySegment)))

        # initialize list and dictionary for storage of chains
        segment_chains = []
        segment_chain_dict = dict()

        # initialize deque for mapping of segment chains
        segment_mapping = deque()

        # BUILD SEGMENT CHAINS BY LOOPING THROUGH 'WARP' EDGES -----------------

        # get all warp edges of the mappingnetwork
        AllWarpEdges = self.WarpEdges

        # loop through all warp edges and build segment chains
        for i, warp_edge in enumerate(AllWarpEdges):
            # get the connected segments at the start and traverse them until
            # a 'warp' edge up is hit to build the segment chains
            warpStart = warp_edge[0]
            warpStartLeafFlag = False #selfNode[warp_edge[0]]["leaf"]
            connected_start_segments = selfEndNodeSegmentsByStart(warpStart,
                                                                  data=True)

            # traverse segments from start node of 'warp' edge
            source_chains = []
            if len(connected_start_segments) > 0:
                for j, cs in enumerate(connected_start_segments):
                    # travel the connected segments until a 'upwards'
                    # connection is found
                    segment_chain = self_traverse_segment_until_warp(
                                                            [cs[2]["segment"]],
                                                            down=False)
                    index = len([c for c in source_chains \
                                 if c[0][0][0] == segment_chain[0][0] \
                                 and c[0][-1][1] == segment_chain[-1][1]])
                    chain_value = (segment_chain[0][0],
                                   segment_chain[-1][1],
                                   index)
                    chain_tuple = (segment_chain, chain_value)
                    all_found_chains.append(chain_tuple)

                    # if this is a 'leaf' node, also travel the segments until
                    # a 'downwards' connection is found
                    if warpStartLeafFlag:
                        segment_chain = self_traverse_segment_until_warp(
                                                            [cs[2]["segment"]],
                                                            down=True)
                        index = len([c for c in source_chains \
                                     if c[0][0][0] == segment_chain[0][0] \
                                     and c[0][-1][1] == segment_chain[-1][1]])
                        chain_value = (segment_chain[0][0],
                                       segment_chain[-1][1],
                                       index)
                        chain_tuple = (segment_chain, chain_value)
                        all_found_chains.append(chain_tuple)


            # get the connected segments at the end and traverse them until
            # a 'warp' edge down is hit to build the segment chain
            warpEnd = warp_edge[1]
            warpEndLeafFlag = False #selfNode[warp_edge[1]]["leaf"]
            connected_end_segments = selfEndNodeSegmentsByStart(warpEnd,
                                                                data=True)

            # traverse segments from end node of 'warp' edge
            target_chains = []
            if len(connected_end_segments) > 0:
                for j, cs in enumerate(connected_end_segments):
                    # if this is a 'leaf' node, first travel the segments until
                    # a 'upwards' connection is found
                    if warpEndLeafFlag:
                        segment_chain = self_traverse_segment_until_warp(
                                                            [cs[2]["segment"]],
                                                            down=False)
                        index = len([c for c in target_chains \
                                     if c[0][0][0] == segment_chain[0][0] \
                                     and c[0][-1][1] == segment_chain[-1][1]])
                        chain_value = (segment_chain[0][0],
                                       segment_chain[-1][1],
                                       index)
                        chain_tuple = (segment_chain, chain_value)
                        all_found_chains.append(chain_tuple)

                    # travel the connected segments until a 'downwards'
                    # connection is found
                    segment_chain = self_traverse_segment_until_warp(
                                                             [cs[2]["segment"]],
                                                             down=True)
                    index = len([c for c in target_chains \
                                 if c[0][0][0] == segment_chain[0][0] \
                                 and c[0][-1][1] == segment_chain[-1][1]])
                    chain_value = (segment_chain[0][0],
                                   segment_chain[-1][1],
                                   index)
                    chain_tuple = (segment_chain, chain_value)
                    all_found_chains.append(chain_tuple)

            # join the list of found chains and add them to the collection
            all_found_chains = source_chains + target_chains
            for chain in all_found_chains:
                if chain[1] not in segment_chain_dict:
                    segment_chains.append(chain)
                    segment_chain_dict[chain[1]] = chain[0]

        # LOOPING THROUGH FOUND SEGMENT CHAINS ---------------------------------

        # loop through the set of chains and search targets using educated
        # guess strategy
        for i, segment_chain in enumerate(segment_chains):
            # get the first and last node ('end' nodes)
            firstNode = (segment_chain[0][0][0],
                         selfNode[segment_chain[0][0][0]])
            lastNode = (segment_chain[0][-1][1],
                        selfNode[segment_chain[0][-1][1]])
            # get the chain value of the current chain
            chain_value = segment_chain[1]
            # extract the ids of the current chain
            current_ids = segment_chain[0]
            # retrieve the current nodes from the segment dictionary by id
            current_nodes = [SegmentDict[id][1] for id in current_ids]
            current_nodes = [n for seg in current_nodes for n in seg]

            print("Processing segment chain {} ...".format(segment_chain))

            # CASE 1 - ENCLOSED SHORT ROW <=====> ------------------------------

            # define our educated guess for the target
            target_guess = (chain_value[0], chain_value[1], chain_value[2]+1)
            if target_guess in segment_chain_dict:
                # get the guessed target chai from the chain dictionary
                target_chain = segment_chain_dict[target_guess]
                # extract the ids for node retrieval
                target_ids = [seg for seg in target_chain]
                # retrieve the target nodes from the segment dictionary by id
                target_nodes = [SegmentDict[id][1] for id in target_ids]
                target_nodes = [n for seg in target_nodes for n in seg]

                print("<=====> detected. Connecting to segment chain {} ...".format(target_guess))

                # we have successfully verified our target segment and
                # can create some warp edges!
                segment_pair = [current_nodes, target_nodes]
                self_create_warp_connections(segment_pair,
                                             max_connections=max_connections,
                                             precise=precise,
                                             verbose=verbose)
                continue

            # CASE 2 - SHORT ROW TO THE RIGHT <=====/ --------------------------

            # define out educated guess for the target
            target_guess = (chain_value[0], chain_value[1]+1, chain_value[2])
            if target_guess in segment_chain_dict:
                # get the guessed target chai from the chain dictionary
                target_chain = segment_chain_dict[target_guess]
                # extract the ids for node retrieval
                target_ids = [seg for seg in target_chain]
                # retrieve the target nodes from the segment dictionary by id
                target_nodes = [SegmentDict[id][1] for id in target_ids]
                target_nodes = [n for seg in target_nodes for n in seg]

                targetFirstNode = target_ids[0][0]
                targetLastNode = target_ids[-1][1]

                # check if firstNode and targetFirstNode are connected via a
                # 'warp' edge to verify
                if (not targetFirstNode == firstNode[0] \
                    and not targetLastNode in self[lastNode[0]]):
                    print("No real connection for /=====/. Skipping...")
                    continue

                print("<=====/ detected. Connecting to segment {} ...".format(target_guess))

                # we have successfully verified our target segment and
                # can create some warp edges!
                segment_pair = [current_nodes, target_nodes]
                self_create_warp_connections(segment_pair,
                                             max_connections=max_connections,
                                             precise=precise,
                                             verbose=verbose)
                continue

            # CASE 3 - SHORT ROW TO THE RIGHT <=====/ SPECIAL CASE -------------

            # define out educated guess for the target
            target_guess = (chain_value[0], chain_value[1]+1, chain_value[2]-1)
            if target_guess in segment_chain_dict:
                # get the guessed target chai from the chain dictionary
                target_chain = segment_chain_dict[target_guess]
                # extract the ids for node retrieval
                target_ids = [seg for seg in target_chain]
                # retrieve the target nodes from the segment dictionary by id
                target_nodes = [SegmentDict[id][1] for id in target_ids]
                target_nodes = [n for seg in target_nodes for n in seg]

                targetFirstNode = target_ids[0][0]
                targetLastNode = target_ids[-1][1]

                # check if firstNode and targetFirstNode are connected via a
                # 'warp' edge to verify
                if (not targetFirstNode == firstNode[0] \
                    and not targetLastNode in self[lastNode[0]]):
                    print("No real connection for /=====/. Skipping...")
                    continue

                print("<=====/ detected. Connecting to segment {} ...".format(target_guess))

                # we have successfully verified our target segment and
                # can create some warp edges!
                segment_pair = [current_nodes, target_nodes]
                self_create_warp_connections(segment_pair,
                                             max_connections=max_connections,
                                             precise=precise,
                                             verbose=verbose)
                continue

            # CASE 4 - SHORT ROW TO THE LEFT /====> ----------------------------

            # define out educated guess for the target
            target_guess = (chain_value[0]+1, chain_value[1], chain_value[2])
            if target_guess in segment_chain_dict:
                # get the guessed target chai from the chain dictionary
                target_chain = segment_chain_dict[target_guess]
                # extract the ids for node retrieval
                target_ids = [seg for seg in target_chain]
                # retrieve the target nodes from the segment dictionary by id
                target_nodes = [SegmentDict[id][1] for id in target_ids]
                target_nodes = [n for seg in target_nodes for n in seg]

                targetFirstNode = target_ids[0][0]
                targetLastNode = target_ids[-1][1]

                # check if firstNode and is connected to targetFirstNode via
                # a 'warp' edge and if lastNode equals targetLastNode
                if (not targetFirstNode in self[firstNode[0]] \
                    and not targetLastNode == lastNode[0]):
                    print("No real connection for /=====/. Skipping...")
                    continue

                print("/=====> detected. Connecting to segment {} ...".format(target_guess))

                # we have successfully verified our target segment and
                # can create some warp edges!
                segment_pair = [current_nodes, target_nodes]
                self_create_warp_connections(segment_pair,
                                             max_connections=max_connections,
                                             precise=precise,
                                             verbose=verbose)
                continue

            # CASE 5 - SHORT ROW TO THE LEFT /====> SPECIAL CASE ---------------

            # define out educated guess for the target
            target_guess = (chain_value[0]+1, chain_value[1], chain_value[2]-1)
            if target_guess in segment_chain_dict:
                # get the guessed target chai from the chain dictionary
                target_chain = segment_chain_dict[target_guess]
                # extract the ids for node retrieval
                target_ids = [seg for seg in target_chain]
                # retrieve the target nodes from the segment dictionary by id
                target_nodes = [SegmentDict[id][1] for id in target_ids]
                target_nodes = [n for seg in target_nodes for n in seg]

                targetFirstNode = target_ids[0][0]
                targetLastNode = target_ids[-1][1]

                # check if firstNode and is connected to targetFirstNode via
                # a 'warp' edge and if lastNode equals targetLastNode
                if (not targetFirstNode in self[firstNode[0]] \
                    and not targetLastNode == lastNode[0]):
                    print("No real connection for /=====/. Skipping...")
                    continue

                print("/=====> detected. Connecting to segment {} ...".format(target_guess))

                # we have successfully verified our target segment and
                # can create some warp edges!
                segment_pair = [current_nodes, target_nodes]
                self_create_warp_connections(segment_pair,
                                             max_connections=max_connections,
                                             precise=precise,
                                             verbose=verbose)
                continue

            # CASE 6 - STANDARD ROW /=====/ ------------------------------------

            # define out educated guess for the target
            target_guess = (chain_value[0]+1, chain_value[1]+1, chain_value[2])
            if target_guess in segment_chain_dict:
                # get the guessed target chai from the chain dictionary
                target_chain = segment_chain_dict[target_guess]
                # extract the ids for node retrieval
                target_ids = [seg for seg in target_chain]
                # retrieve the target nodes from the segment dictionary by id
                target_nodes = [SegmentDict[id][1] for id in target_ids]
                target_nodes = [n for seg in target_nodes for n in seg]

                # set target first and last node ('end' nodes)
                targetFirstNode = target_ids[0][0]
                targetLastNode = target_ids[-1][1]

                # check if firstNode and targetFirstNode are connected via a
                # 'warp' edge to verify
                if (not targetFirstNode in self[firstNode[0]] \
                    and not targetLastNode in self[lastNode[0]]):
                    print("No real connection for /=====/. Skipping...")
                    continue

                print("/=====/ detected. Connecting to segment {} ...".format(target_guess))

                # we have successfully verified our target segment and
                # can create some warp edges!
                segment_pair = [current_nodes, target_nodes]
                self_create_warp_connections(segment_pair,
                                             max_connections=max_connections,
                                             precise=precise,
                                             verbose=verbose)
                continue

            # CASE 7 - STANDARD ROW /=====/ SPECIAL CASE -----------------------

            # define out educated guess for the target id
            target_guess = (chain_value[0]+1, chain_value[1]+1, chain_value[2]-1)
            if target_guess in segment_chain_dict:
                # get the guessed target chai from the chain dictionary
                target_chain = segment_chain_dict[target_guess]
                # extract the ids for node retrieval
                target_ids = [seg for seg in target_chain]
                # retrieve the target nodes from the segment dictionary by id
                target_nodes = [SegmentDict[id][1] for id in target_ids]
                target_nodes = [n for seg in target_nodes for n in seg]

                # set target first and last node ('end' nodes)
                targetFirstNode = target_ids[0][0]
                targetLastNode = target_ids[-1][1]

                # check if firstNode and targetFirstNode are connected via a
                # 'warp' edge to verify
                if (not targetFirstNode in self[firstNode[0]] \
                    and not targetLastNode in self[lastNode[0]]):
                    print("No real connection for /=====/. Skipping...")
                    continue

                print("/=====/ detected. Connecting to segment {} ...".format(target_guess))

                # we have successfully verified our target segment and
                # can create some warp edges!
                segment_pair = [current_nodes, target_nodes]
                self_create_warp_connections(segment_pair,
                                             max_connections=max_connections,
                                             precise=precise,
                                             verbose=verbose)
                continue
