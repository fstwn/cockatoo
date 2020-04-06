# PYTHON LIBRARY IMPORTS
from __future__ import division
import math
from operator import itemgetter
from collections import deque

# RHINO IMPORTS
from Rhino.Geometry import Line as RGLine
from Rhino.Geometry import Curve as RGCurve
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
        # SegmentContourEdges.sort(key=lambda x: x[2]["segment"])
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

    # SEGMENT CONTOUR METHODS --------------------------------------------------

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

    def TraverseSegmentUntilWarp(self, way_segments, down=False, by_end=False):
        """
        Private method for traversing a path of 'segment' edges until a 'warp'
        edge is discovered which points to the previous or the next segment.
        Returns the ids of the segment array
        """

        # namespace mapping for performance gains
        selfNode = self.node
        selfNodeWarpEdges = self.NodeWarpEdges
        selfEndNodeSegmentsByStart = self.EndNodeSegmentsByStart
        selfEndNodeSegmentsByEnd = self.EndNodeSegmentsByEnd

        segment_list = way_segments
        flag = False
        while flag == False:
            # set the current segment
            current_segment = segment_list[-1]
            # traversal by segment endnode
            if by_end:
                # check that segment for 'warp' edges at the start
                warp_edges = selfNodeWarpEdges(current_segment[0])
                if down:
                    filtered_warp_edges = [we for we in warp_edges \
                                           if we[1] == current_segment[0]-1]
                else:
                    filtered_warp_edges = [we for we in warp_edges \
                                           if we[1] == current_segment[0]+1]

                # if there is a warp edge at the start, return the segment_list
                if (len(filtered_warp_edges) != 0 or (len(warp_edges) == 1 \
                    and selfNode[current_segment[0]]["leaf"])):
                    flag = True
                    break
            # traversal by segment start node
            else:
                # check that segment for 'warp' edges at the end
                warp_edges = selfNodeWarpEdges(current_segment[1])
                if down:
                    filtered_warp_edges = [we for we in warp_edges \
                                           if we[1] == current_segment[1]-1]
                else:
                    filtered_warp_edges = [we for we in warp_edges \
                                           if we[1] == current_segment[1]+1]

                # if there is a warp edge at the end, our chain is finished
                if (len(filtered_warp_edges) != 0 or (len(warp_edges) == 1 \
                    and selfNode[current_segment[1]]["leaf"])):
                    flag = True
                    break

            # get all connected segments at the last point of the segment
            if by_end:
                connected_segments = selfEndNodeSegmentsByEnd(
                                                  current_segment[0], data=True)
            else:
                connected_segments = selfEndNodeSegmentsByStart(
                                                  current_segment[1], data=True)

            # from these, only get the segment with the lowest id
            if len(connected_segments) > 0:
                # define best candidate segment
                candidate_segment = connected_segments[0]
                # append the segment to the segment_list
                segment_list.append(candidate_segment[2]["segment"])
            else:
                break

        # if we are traversing by end, we need to reverse the resulting list
        if by_end:
            segment_list.reverse()

        return segment_list

    # CREATION OF FINAL 'WEFT' CONNECTIONS -------------------------------------

    def CreateFinalWeftConnections(self):
        """
        Loop through all the segment contour edges and create all 'weft'
        connections for this mapping network.
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
                # loop through all nodes on the current segment and create
                # the final 'weft' edges
                for j, node in enumerate(segment):
                    if j == 0:
                        selfCreateWeftEdge(firstNode, node, segval)
                        selfCreateWeftEdge(node, segment[j+1], segval)
                    elif j < len(segment)-1:
                        selfCreateWeftEdge(node, segment[j+1], segval)
                    elif j == len(segment)-1:
                        selfCreateWeftEdge(node, lastNode, segval)

    # CREATION OF FINAL 'WARP' CONNECTIONS -------------------------------------

    def AttemptWarpConnectionToCandidate(self, node, candidate, source_nodes, max_connections=4, verbose=False):
        """
        Private method for attempting a 'warp' connection to a candidate
        node. Returns True if the connection has been made, otherwise false.
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

    def _build_source_and_target_chains(self):
        """
        Private method for building source and target chains from segment
        contour edges.
        """

        # namespace mapping for performance gains
        selfNode = self.node
        selfEndNodeSegmentsByStart = self.EndNodeSegmentsByStart
        selfTraverseSegmentUntilWarp = self.TraverseSegmentUntilWarp

        # get all warp edges of this mappingnetwork
        AllWarpEdges = self.WarpEdges

        # initialize lists and dictionaries for storage of chains
        source_chains = []
        source_chain_dict = dict()
        target_chain_dict = dict()

        # BUILD SEGMENT CHAINS BY LOOPING THROUGH 'WARP' EDGES -----------------

        # loop through all warp edges and build segment chains
        for i, warp_edge in enumerate(AllWarpEdges):
            # initialize temporary lists for source and target chains
            source_pass_chains = []
            target_pass_chains = []

            # START OF 'WARP' EDGE ---------------------------------------------

            # get the connected segments at the start of the 'warp edge'
            warpStart = warp_edge[0]
            warpStartLeafFlag = selfNode[warp_edge[0]]["leaf"]
            connected_start_segments = selfEndNodeSegmentsByStart(warpStart,
                                                                  data=True)
            # traverse segments from start node of 'warp' edge
            if len(connected_start_segments) > 0:
                for j, cs in enumerate(connected_start_segments):
                    # travel the connected segments at the start of the 'warp'
                    # edge until a 'upwards' connection is found and append
                    # it to the source chains of this pass
                    segment_chain = selfTraverseSegmentUntilWarp(
                                                            [cs[2]["segment"]],
                                                            down=False)
                    index = len([c for c in source_pass_chains \
                                 if c[0][0][0] == segment_chain[0][0] \
                                 and c[0][-1][1] == segment_chain[-1][1]])
                    chain_value = (segment_chain[0][0],
                                   segment_chain[-1][1],
                                   index)
                    chain_tuple = (segment_chain, chain_value)
                    source_pass_chains.append(chain_tuple)

                    # if this is a 'leaf' node, also travel the segments until
                    # a 'downwards' connection is found and append this to the
                    # target (!) chains of this pass
                    if warpStartLeafFlag:
                        segment_chain = selfTraverseSegmentUntilWarp(
                                                            [cs[2]["segment"]],
                                                            down=True)
                        index = len([c for c in target_pass_chains \
                                     if c[0][0][0] == segment_chain[0][0] \
                                     and c[0][-1][1] == segment_chain[-1][1]])
                        chain_value = (segment_chain[0][0],
                                       segment_chain[-1][1],
                                       index)
                        chain_tuple = (segment_chain, chain_value)
                        target_pass_chains.append(chain_tuple)

            # END OF 'WARP' EDGE -----------------------------------------------

            # get the connected segments at the end
            warpEnd = warp_edge[1]
            warpEndLeafFlag = selfNode[warp_edge[1]]["leaf"]
            connected_end_segments = selfEndNodeSegmentsByStart(warpEnd,
                                                                data=True)
            # traverse segments from end node of 'warp' edge
            if len(connected_end_segments) > 0:
                for j, cs in enumerate(connected_end_segments):
                    # if this is a 'leaf' node, first travel the segments until
                    # a 'upwards' connection is found and append this to the
                    # source (!) chains of this pass
                    if warpEndLeafFlag:
                        segment_chain = selfTraverseSegmentUntilWarp(
                                                            [cs[2]["segment"]],
                                                            down=False)
                        index = len([c for c in source_pass_chains \
                                     if c[0][0][0] == segment_chain[0][0] \
                                     and c[0][-1][1] == segment_chain[-1][1]])
                        chain_value = (segment_chain[0][0],
                                       segment_chain[-1][1],
                                       index)
                        chain_tuple = (segment_chain, chain_value)
                        source_pass_chains.append(chain_tuple)

                    # travel the connected segments until a 'downwards'
                    # connection is found and append to target pass chains
                    segment_chain = selfTraverseSegmentUntilWarp(
                                                             [cs[2]["segment"]],
                                                             down=True)
                    index = len([c for c in target_pass_chains \
                                 if c[0][0][0] == segment_chain[0][0] \
                                 and c[0][-1][1] == segment_chain[-1][1]])
                    chain_value = (segment_chain[0][0],
                                   segment_chain[-1][1],
                                   index)
                    chain_tuple = (segment_chain, chain_value)
                    target_pass_chains.append(chain_tuple)

            # append the source pass chains to the source collection
            for chain in source_pass_chains:
                if chain[1] not in source_chain_dict:
                    source_chains.append(chain)
                    source_chain_dict[chain[1]] = chain[0]

            # append the target pass chains to the target collection
            for chain in target_pass_chains:
                if chain[1] not in target_chain_dict:
                    target_chain_dict[chain[1]] = chain[0]

        return (source_chains, target_chain_dict)

    def _create_initial_warp_connections(self, segment_pair, max_connections=4, precise=False, verbose=False):
        """
        Private method for creating first pass 'warp' connections for the
        supplied pair of segment chains.
        The pair is only defined as a list of nodes, the nodes have to be
        supplied with their attribute data!
        """

        # namespace mapping for performance gains
        mathPi = math.pi
        mathRadians = math.radians
        selfAttemptWarpConnection = self.AttemptWarpConnectionToCandidate

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
                res = selfAttemptWarpConnection(node,
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
                res = selfAttemptWarpConnection(node,
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
                res = selfAttemptWarpConnection(node,
                                                fCand,
                                                initial_nodes,
                                                max_connections=max_connections,
                                                verbose=verbose)
                # set forbidden node
                if res:
                    forbidden_node = fCand[0]

    def _create_second_pass_warp_connections(self, precise=False, verbose=False):
        """
        Private method for creating second pass 'warp' connections.
        """
        pass

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

        include_end_nodes : boolean
            If True, 'end' nodes between adjacent segment contours in a source
            chain will be included in the first pass of connecting 'warp' edges.
            Defaults to True.

        precise : boolean
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

        # TODO 3: store all connections that were made as a mapping for the
        #         second pass

        # namespace mapping for performance gains
        selfNode = self.node
        self_create_initial_warp_connections = self._create_initial_warp_connections

        # get all segment ids, nodes per segment and edges
        SegmentValues, AllNodesBySegment, SegmentContourEdges = zip(
                                 *self.AllNodesBySegment(data=True, edges=True))

        # build a dictionary of the segments by their index
        SegmentDict = dict(zip(SegmentValues,
                               zip(SegmentContourEdges, AllNodesBySegment)))

        # build source and target chains
        source_chains, target_chain_dict = self._build_source_and_target_chains()

        # initialize container dict for connected chains
        connected_chains = dict()

        # LOOPING THROUGH SOURCE SEGMENT CHAINS --------------------------------

        # loop through all source chains and find targets in target chains
        # using an 'educated guess strategy'
        for i, source_chain in enumerate(source_chains):
            # get the first and last node ('end' nodes)
            firstNode = (source_chain[0][0][0],
                         selfNode[source_chain[0][0][0]])
            lastNode = (source_chain[0][-1][1],
                        selfNode[source_chain[0][-1][1]])
            # get the chain value of the current chain
            chain_value = source_chain[1]
            # extract the ids of the current chain
            current_ids = source_chain[0]
            # extract the current chains geometry
            current_chain_geo_list = [SegmentDict[id][0][2]["geo"] \
                                      for id in current_ids]
            current_chain_geo = RGCurve.JoinCurves([ccg.ToPolylineCurve() \
                                          for ccg in current_chain_geo_list])[0]
            current_chain_spt = current_chain_geo.PointAtNormalizedLength(0.5)
            # retrieve the current segments from the segment dictionary by id
            current_segment_nodes = [SegmentDict[id][1] for id in current_ids]
            # retrieve the current nodes from the list of current segments
            current_nodes = []
            for j, csn in enumerate(current_segment_nodes):
                if include_end_nodes and j > 0:
                    current_nodes.append((current_ids[j][0],
                                          selfNode[current_ids[j][0]]))
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
                    ptc_geo = RGCurve.JoinCurves([ptcg.ToPolylineCurve() \
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
                target_ids = [seg for seg in target_chain]
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
                connected_chains[target_key] = True
                self_create_initial_warp_connections(segment_pair,
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
                    ptc_geo = RGCurve.JoinCurves([pg.ToPolylineCurve() \
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
                target_ids = [seg for seg in target_chain]
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
                    self_create_initial_warp_connections(segment_pair,
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
                    ptc_geo = RGCurve.JoinCurves([pg.ToPolylineCurve() \
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
                target_ids = [seg for seg in target_chain]
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
                    self_create_initial_warp_connections(segment_pair,
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
                    ptc_geo = RGCurve.JoinCurves([pg.ToPolylineCurve() \
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
                target_ids = [seg for seg in target_chain]
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
                    self_create_initial_warp_connections(segment_pair,
                                                max_connections=max_connections,
                                                precise=precise,
                                                verbose=verbose)
                    continue
                else:
                    if verbose:
                        print("No real connection for /=====/. No cases match.")
