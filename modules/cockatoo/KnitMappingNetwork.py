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

    def EndNodeSegmentsByStart(self, node):
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

        return connected_segments

    def EndNodeSegmentsByEnd(self, node):
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

        return connected_segments

    # SAMPLING OF SEGMENT CONTOURS ---------------------------------------------

    def SampleSegmentContours(self, stitch_width):
        """
        Sample the segment contours of the mapping network with the given
        stitch width. Add the resulting points as nodes to the network.
        """

        selfNodeFromPoint3d = self.NodeFromPoint3d

        # get the highest index of all the nodes in the network
        maxNode = max(self.nodes())

        # get all the segment geometry ordered by segment number
        segment_contours = self.SegmentContourEdges

        # sample all segments with the stitch width
        nodeindex = maxNode + 1
        newPts = []
        for i, seg in enumerate(segment_contours):
            geo = seg[2]["geo"]
            geo = geo.ToPolylineCurve()
            geo.Domain = RGInterval(0.0, 1.0)

            crvlen = geo.GetLength()
            density = int(round(crvlen / stitch_width))
            if density == 0:
                continue
            divT = geo.DivideByCount(density, False)
            divPts = [geo.PointAt(t) for t in divT]
            # add all the nodes to the network
            for j, pt in enumerate(divPts):
                # add node to network
                selfNodeFromPoint3d(nodeindex,
                                    pt,
                                    position = None,
                                    num = j,
                                    leaf = False,
                                    end = False,
                                    segment = seg[2]["segment"])
                # increment node index
                nodeindex += 1

    # CREATION OF WEFT EDGES ---------------------------------------------------

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

    # CREATION OF WARP EDGES ---------------------------------------------------

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
        set of segment contours, starting from the first segment contour in the
        set and propagating to the last contour in the set.
        """

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
        initial_nodes = segment_pair[0][1:-1]
        target_nodes = segment_pair[1][1:-1]

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
                    raise RuntimeError("More than one previous " +
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

    def CreateWarpConnections(self, max_connections=4, precise=False, verbose=False):
        """
        Loop through all the segment contours and create all 'warp' connections
        for this network.
        """

        # namespace mapping for performance gains
        selfNode = self.node
        selfCreateWarpConnections = self._create_warp_connections
        selfEndNodeSegmentsByStart = self.EndNodeSegmentsByStart
        selfNodeWarpEdges = self.NodeWarpEdges
        selfNodesOnSegment = self.NodesOnSegment

        # get all nodes by segment
        SegmentValues, AllNodesBySegment = zip(*self.AllNodesBySegment(True))

        # for each segment, get the 'next' segment as in the segment that is
        # connected to to the current segment via two 'end' nodes or a shared
        # 'end' node.
        # if there is no connection at the end of the segment, we have to
        # look for a connected segment and include the nodes on this segment

        for i, segment in enumerate(AllNodesBySegment):
            # get the 'segment' value attribute
            segval = SegmentValues[i]
            # get the first and last node ('end' nodes not included in the seg)
            firstNode = (segval[0], selfNode[segval[0]])
            lastNode = (segval[1], selfNode[segval[1]])

            # CASES:
            # 1: <======>
            # 2: <======/
            # 3: /======/
            # 4: /======>
            # 5: />
            # 6: </

            # first we can make some educated guesses about possible targets:
            # segment[x, y, z] is most likely connected to
            # segment[x, y, z+1] or
            # segment[x, y+1, z] or
            # segment[x+1, y+1, z] or
            # segment[x+1, y, z]

            # we should find a way to check these cases quickly before we
            # resort to a more 'search and destroy' kind of practice

            # otherwise (new approach):
            # is there a weft edge at the end of the current segment which is
            # connected to a "higher" node?
            # if yes, this is an atomic segment chain.
            # if not, we have to travel along the segement until we find this
            # weft edge to build the current segment chain

            # get the segment that is connected to the first node either by
            # sharing this node or being connected through a 'warp' edge
            connected_segments = selfEndNodeSegmentsByStart(firstNode[0])
            connected_segments = [cs for cs in connected_segments \
                                  if cs[2]["segment"] > segval]

            # check for <=====> case
            csvals = [cs[2]["segment"] for cs in connected_segments]
            hypoval = (segval[0], segval[1], segval[2]+1)
            if hypoval in csvals:
                connected_segments = [cs for cs in connected_segments \
                                      if cs[2]["segment"] == hypoval]
            else:
                connected_segments = [cs for cs in connected_segments \
                                      if cs[2]["segment"][2] == 0]

            print("Filtered connected segments: ", [cs[2]["segment"] for cs in connected_segments])

            if len(connected_segments) > 1:
                connected_segments = connected_segments[:1]

            print "Current Segment: ", segval

            if len(connected_segments) == 0:
                # CASE /=====> OR /=====/
                # obviously only this segment is connected to the end node at
                # its start. So we traverse the connected 'weft' edge
                conwarpedges = selfNodeWarpEdges(firstNode[0])
                # only consider warp edges whose target node is greater
                # than the start node
                conwarpedges = [c for c in conwarpedges \
                                if c[1] > firstNode[0]]
                if len(conwarpedges) == 0:
                    # if there are no warp edges left, continue
                    # TODO: check if this is the right procedure here!
                    continue
                elif len(conwarpedges) > 1:
                    if verbose:
                        vStr = ("More than one warp edge connected to " +
                                "segment {} at start!")
                        vStr = vStr.format(segval)
                        print(vStr)
                    continue
                else:
                    conwarpedge = conwarpedges[0]

                print("Travelling connected warp edge: ", conwarpedge[:2])

                # define start of target segment
                next_segment_start = (conwarpedge[1], selfNode[conwarpedge[1]])
                next_connected_segments = selfEndNodeSegmentsByStart(
                                                          next_segment_start[0])

                # NOTE: only consider segments whose id is greater, neded here?
                #next_connected_segments = [ncs for ncs in next_connected_segments \
                #                           if ncs[2]["segment"] > segval]

                # the first segment in this list should be at least the start
                # of our target
                target_segment = next_connected_segments[0]
                targetLastNode = target_segment[2]["segment"][1]

                print("Target Segment: ", target_segment[2]["segment"])

                # check if the target segment shares an 'end' node with the
                # current segment
                shared_end_node = targetLastNode == lastNode[0]

                # check the different cases and act accordingly
                if shared_end_node:
                    # CASE /=====>
                    print("Shared 'end' node found. Connecting....")
                    # we have successfully verified our target segment and
                    # can create some warp edges! we start by getting all
                    # nodes on the target segment
                    target_nodes = [next_segment_start]
                    target_nodes.extend(selfNodesOnSegment(
                                        target_segment[2]["segment"], True))
                    target_nodes.append(targetLastNode)
                    current_nodes = [firstNode]
                    current_nodes.extend(segment)
                    current_nodes.append(lastNode)
                    segment_pair = [current_nodes, target_nodes]
                    selfCreateWarpConnections(segment_pair,
                                              max_connections=max_connections,
                                              precise=precise,
                                              verbose=verbose)
                else:
                    # CASE /====/
                    print("No shared 'end' node. Checking for 'weft' connection at end...")
                    # check if the 'end' node at the end of the target shares
                    # a 'warp' edge with the current segment 'end' node at the
                    # end. Traverse all 'warp' edges connected to the
                    # targetLastNode to determine if there is a connection
                    tln_cwe = selfNodeWarpEdges(targetLastNode)
                    tln_cwe_other = [c[1] for c in tln_cwe]
                    if lastNode[0] in tln_cwe_other:
                        print("Found shared 'weft' edge at end. Connecting...")
                        # we have successfully verified our target segment and
                        # can create some warp edges! we start by getting all
                        # nodes on the target segment
                        target_nodes = [next_segment_start]
                        target_nodes.extend(selfNodesOnSegment(
                                            target_segment[2]["segment"], True))
                        target_nodes.append(targetLastNode)
                        current_nodes = [firstNode] + segment + [lastNode]
                        segment_pair = [current_nodes, target_nodes]
                        selfCreateWarpConnections(segment_pair,
                                                  max_connections=max_connections,
                                                  precise=precise,
                                                  verbose=verbose)
                    else:
                        # we have no connection between the current segment and
                        # the target segment at the end. we have to traverse the
                        # connected segment to the targets last 'end' node
                        # to find some more nodes

                        # the target is still the first target

                        # we have to check if any of the following connected
                        # segments to the target (always lowest id) shares an
                        # end node with the current segment
                        # /=====*=====>
                        # if not, we have to check if the following segment
                        # connected to
                        # /=====.=====>

                        pass

            elif len(connected_segments) == 1:
                # CASE <=====> OR <=====/

                # the first segment in this list should be at least the start
                # of our target
                target_segment = connected_segments[0]
                targetLastNode = target_segment[2]["segment"][1]

                # check if the target segment shares an 'end' node with the
                # current segment
                shared_end_node = targetLastNode == lastNode[0]
                if shared_end_node:
                    # CASE <=====>
                    # we have successfully verified our target segment and
                    # can create some warp edges! we start by getting all
                    # nodes on the target segment
                    target_nodes = [firstNode]
                    target_nodes.extend(selfNodesOnSegment(
                                        target_segment[2]["segment"], True))
                    target_nodes.append(targetLastNode)
                    current_nodes = [firstNode]
                    current_nodes.extend(segment)
                    current_nodes.append(lastNode)
                    segment_pair = [current_nodes, target_nodes]
                    selfCreateWarpConnections(segment_pair,
                                              max_connections=max_connections,
                                              precise=precise,
                                              verbose=verbose)
                else:
                    # CASE <=====/
                    # check if the 'end' node at the end of the target shares
                    # a 'warp' edge with the current segment 'end' node at the
                    # end. Traverse all 'warp' edges connected to the
                    # targetLastNode to determine if there is a connection
                    tln_cwe = selfNodeWarpEdges(targetLastNode)
                    tln_cwe_other = [c[1] for c in tln_cwe]
                    if lastNode[0] in tln_cwe_other:
                        # we have successfully verified our target segment and
                        # can create some warp edges! we start by getting all
                        # nodes on the target segment
                        target_nodes = [firstNode]
                        target_nodes.extend(selfNodesOnSegment(
                                            target_segment[2]["segment"], True))
                        target_nodes.append(targetLastNode)
                        current_nodes = [firstNode] + segment + [lastNode]
                        segment_pair = [current_nodes, target_nodes]
                        selfCreateWarpConnections(segment_pair,
                                                  max_connections=max_connections,
                                                  precise=precise,
                                                  verbose=verbose)
                    else:
                        # we have no connection between the current segment and
                        # the target segment at the end. we have to traverse the
                        # connected segment to the targets last 'end' node
                        # to find some more nodes
                        pass



    def _traverse_segment_until_warp_down(self, segment_edge, wayNodes=None, wayEdges=None, endNodes=None):
        """
        Private method for traversing a path of 'segment' edges until a 'warp'
        edge is discovered which points to the previous segment
        """
        pass


    def CreateWarpConnections_v2(self, max_connections=4, precise=False, verbose=False):
        """
        Loop through all the segment contours and create all 'warp' connections
        for this network.
        """

        # namespace mapping for performance gains
        selfNode = self.node
        selfCreateWarpConnections = self._create_warp_connections
        selfEndNodeSegmentsByStart = self.EndNodeSegmentsByStart
        selfNodeWarpEdges = self.NodeWarpEdges
        selfNodesOnSegment = self.NodesOnSegment

        # get all nodes by segment
        SegmentValues, AllNodesBySegment, SegmentContourEdges = zip(*self.AllNodesBySegment(data=True, edges=True))

        # build a dictionary of the segments by their index
        SegmentDict = dict(zip(SegmentValues, zip(SegmentContourEdges, AllNodesBySegment)))

        # loop through all segments ordered by their id
        for i, segment in enumerate(AllNodesBySegment):
            # get the 'segment' value attribute
            segval = SegmentValues[i]
            # get the first and last node ('end' nodes not included in the seg)
            firstNode = (segval[0], selfNode[segval[0]])
            lastNode = (segval[1], selfNode[segval[1]])

            # first we can make some educated guesses about possible targets:
            # segment[x, y, z] is most likely connected to
            # segment[x, y, z+1] or

            # segment[x, y+1, z] or

            # segment[x+1, y+1, z] or
            # segment[x+1, y, z]

            # we should find a way to check these cases quickly before we
            # resort to a more 'search and destroy' kind of practice

            # otherwise (new approach):
            # is there a weft edge at the end of the current segment which is
            # connected to a "higher" node?
            # if yes, this is an atomic segment chain.
            # if not, we have to travel along the segement until we find this
            # weft edge to build the current segment chain

            # TODO: Check guessed targets if they really connect to the source!

            # CASE 1 - ENCLOSED SHORT ROW <=====> ------------------------------

            print("Processing Segment {} ...".format(segval))

            # define our educated guess for the target
            target_guess = (segval[0], segval[1], segval[2]+1)
            if target_guess in SegmentDict:
                # if this condition is True, we have found our target!
                target_segment = SegmentDict[target_guess][0]
                targetLastNode = target_segment[2]["segment"][1]

                print("<=====> detected. Connecting to segment {} ...".format(target_guess))

                # we have successfully verified our target segment and
                # can create some warp edges!
                target_nodes = [firstNode] + SegmentDict[target_guess][1]
                target_nodes = target_nodes + [targetLastNode]
                current_nodes = [firstNode] + segment + [lastNode]
                segment_pair = [current_nodes, target_nodes]
                selfCreateWarpConnections(segment_pair,
                                          max_connections=max_connections,
                                          precise=precise,
                                          verbose=verbose)
                continue

            # CASE 2 - SHORT ROW TO THE RIGHT <=====/ --------------------------

            # define out educated guess for the target
            target_guess = (segval[0], segval[1]+1, segval[2])
            if target_guess in SegmentDict:
                # if this condition is True, we have found out target!
                target_segment = SegmentDict[target_guess][0]
                targetLastNode = target_segment[2]["segment"][1]

                print("<=====/ detected. Connecting to segment {} ...".format(target_guess))

                # we have successfully verified our target segment and
                # can create some warp edges!
                target_nodes = [firstNode] + SegmentDict[target_guess][1]
                target_nodes = target_nodes + [targetLastNode]
                current_nodes = [firstNode] + segment + [lastNode]
                segment_pair = [current_nodes, target_nodes]
                selfCreateWarpConnections(segment_pair,
                                          max_connections=max_connections,
                                          precise=precise,
                                          verbose=verbose)
                continue

            # CASE 3 - SHORT ROW TO THE LEFT /====> ----------------------------

            # define out educated guess for the target
            target_guess = (segval[0]+1, segval[1], segval[2])
            if target_guess in SegmentDict:
                # if this condition is True, we have found out target!
                target_segment = SegmentDict[target_guess][0]
                targetFirstNode = target_segment[2]["segment"][0]
                targetLastNode = target_segment[2]["segment"][1]

                print("/=====> detected. Connecting to segment {} ...".format(target_guess))

                # we have successfully verified our target segment and
                # can create some warp edges!
                target_nodes = [targetFirstNode] + SegmentDict[target_guess][1]
                target_nodes = target_nodes + [targetLastNode]
                current_nodes = [firstNode] + segment + [lastNode]
                segment_pair = [current_nodes, target_nodes]
                selfCreateWarpConnections(segment_pair,
                                          max_connections=max_connections,
                                          precise=precise,
                                          verbose=verbose)
                continue

            # CASE 4 - STANDARD ROW /=====/ ------------------------------------

            # define our educated guess for the target
            target_guess = (segval[0]+1, segval[1]+1, segval[2])
            if target_guess in SegmentDict:
                # if this condition is True, we have found out target!
                target_segment = SegmentDict[target_guess][0]
                targetFirstNode = target_segment[2]["segment"][0]
                targetLastNode = target_segment[2]["segment"][1]

                print("/=====/ detected. Connecting to segment {} ...".format(target_guess))

                # we have successfully verified our target segment and
                # can create some warp edges!
                target_nodes = [targetFirstNode] + SegmentDict[target_guess][1]
                target_nodes = target_nodes + [targetLastNode]
                current_nodes = [firstNode] + segment + [lastNode]
                segment_pair = [current_nodes, target_nodes]
                selfCreateWarpConnections(segment_pair,
                                          max_connections=max_connections,
                                          precise=precise,
                                          verbose=verbose)
                continue

            # CASE 5 - TRAVERSAL NEEDED ----------------------------------------

            print("Traversal needed...")

            # we need to check if the current segment has a 'warp' edge
            # at the end whose target node index is exactly +1 (...=====/)
            warp_up_at_end = [nwe for nwe in selfNodeWarpEdges(lastNode[0]) \
                              if nwe[1] == lastNode[0]+1]
            wupFlag = len(warp_up_at_end) > 0

            print("WUP: ", wupFlag)

            # then we need to check if the current segment shares a start point
            # with any other segents (<=====...)
            shared_start_node = [seg for seg in SegmentContourEdges \
                                 if seg[0] == firstNode[0] \
                                 and seg[2]["segment"] != segval]
            ssnFlag = len(shared_start_node) > 0
            if ssnFlag:
                shared_start_node.sort(key=lambda x: x[2]["segment"])

            print("SSN: ", ssnFlag)

            continue

            if wupFlag == True:
                # if there is a 'weft' edge up at the end of this segment, our
                # current segment is verified but we defintely need to traverse
                # our target
                current_nodes = [firstNode] + segment + [lastNode]
            else:
                # if there is no 'weft' edge up at the en of the segment, we need
                # to traverse this segment until we find one.

                #current_nodes = self._traverse_segment_until_warp_up(current_segment)
                pass

            if ssnFlag == True:
                # if this segment shares a start node with any other segment,
                # the segment with the lowest id of these is our candidate
                target_segment = shared_start_node[0]
                if wupFlag:
                    # if the flag is set, we need to traverse the target segment
                    # until we find a downwards 'warp' edge

                    #target_nodes = self._traverse_segment_until_warp_down(target_segment)
                    pass
                else:
                    # if no flag is set, we have our target nodes ...?
                    target_nodes = []
                    pass
            else:
                # if there is no shared start node, our target is the segment
                # at the end of the 'warp' edge at the current segments start
                # node with the lowest id
                pass
