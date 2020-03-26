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
        SegmentContourEdges = [(f, t, d) for f, t, d in self.edges_iter(data=True) \
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
        # TODO: implement segment index value
        nodes = [(n, d) for n, d in self.nodes_iter(data=True) \
                 if d["segment"] == segment]

        nodes.sort(key=lambda x: x[1]["num"])

        if data:
            return nodes
        else:
            return [n[0] for n in nodes]

    def AllNodesBySegment(self, data=False):
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
                anbs.append((segval, segnodes))
            else:
                anbs.append((segval, [sn[0] for sn in segnodes]))

        return anbs

    def EndNodeSegments(self, node):
        """
        Get all the segments which share a given 'end' node at the start
        and sort them by their 'segment' value
        """

        connected_segments = self.SegmentContourEdges
        connected_segments = [cs for cs in connected_segments \
                              if cs[2]["segment"][0] == node]
        connected_segments.sort(key=lambda x: x[2]["segment"])

        return connected_segments

    # SAMPLING OF SEGMENT CONTOURS ---------------------------------------------

    def SampleSegmentContours(self, stitch_width):
        """
        Sample the segment contours of the mapping network with the given
        stitch width. Add the resulting points as nodes to the network.
        """

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
            geo.Domain = Rhino.Geometry.Interval(0.0, 1.0)

            crvlen = geo.GetLength()
            density = int(round(crvlen / stitch_width))
            if density == 0:
                continue
            divT = geo.DivideByCount(density, False)
            divPts = [geo.PointAt(t) for t in divT]
            # add all the nodes to the network
            for j, pt in enumerate(divPts):
                # add node to network
                self.NodeFromPoint3d(nodeindex,
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
        for this network. Discard segment contour edges afterwards.
        """

        # get all nodes by segment contour
        SegmentValues, AllNodesBySegment = zip(*self.AllNodesBySegment(True))

        # loop through all the segment contours
        for i, segment in enumerate(AllNodesBySegment):
            segval = SegmentValues[i]
            firstNode = (segval[0], self.node[segval[0]])
            lastNode = (segval[1], self.node[segval[1]])

            if len(segment) == 0:
                print("Segment is empty!")
                self.CreateWeftEdge(firstNode, lastNode, segval)
            elif len(segment) == 1:
                self.CreateWeftEdge(firstNode, segment[0], segval)
                self.CreateWeftEdge(segment[0], lastNode, segval)
            else:
                # loop through all nodes on the current segment
                for j, node in enumerate(segment):
                    if j == 0:
                        self.CreateWeftEdge(firstNode, node, segval)
                        self.CreateWeftEdge(node, segment[j+1], segval)
                    elif j < len(segment)-1:
                        self.CreateWeftEdge(node, segment[j+1], segval)
                    elif j == len(segment)-1:
                        self.CreateWeftEdge(node, lastNode, segval)

    # CREATION OF WARP EDGES ---------------------------------------------------

    def _attempt_warp_connection_to_candidate(self, node, candidate, segment_nodes, verbose=False):
        """
        Private method for attempting a 'warp' connection to a candidate
        node.
        """

        connecting_neighbours = self[candidate[0]]
        if len(connecting_neighbours) < 4:
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

    def _create_initial_warp_connections(self, segment_pair, precise=False, verbose=False):
        """
        Private method for creating initial 'warp' connections for the supplied
        set of segment contours, starting from the first segment contour in the
        set and propagating to the last contour in the set.
        """

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
                                                key = operator.itemgetter(0)))

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
                self._attempt_warp_connection_to_candidate(node,
                                                           fCand,
                                                           initial_nodes,
                                                           verbose)
                continue

            # get the segment contours current direction
            if k < len(initial_nodes)-1:
                contourDir = Rhino.Geometry.Line(thisPt,
                         initial_nodes[k+1][1]["geo"]).Direction
            elif k == len(initial_nodes)-1:
                contourDir = Rhino.Geometry.Line(
                 initial_nodes[k-1][1]["geo"], thisPt).Direction
            contourDir.Unitize()

            # get the directions of the possible connections
            candidatePoints = [pc[1]["geo"] \
                               for pc in possible_connections]
            candidateDirections = [Rhino.Geometry.Line(
                    thisPt, cp).Direction for cp in candidatePoints]
            [cd.Unitize() for cd in candidateDirections]

            # get the angles between segment contour dir and possible conn dir
            normals = [Rhino.Geometry.Vector3d.CrossProduct(
                      contourDir, cd) for cd in candidateDirections]
            angles = [Rhino.Geometry.Vector3d.VectorAngle(
                      contourDir, cd, n) for cd, n in zip(
                                      candidateDirections, normals)]

            # compute deltas as a measure of perpendicularity
            deltas = [abs(a - (0.5 * math.pi)) for a in angles]

            # sort possible connections first by distance, then by delta
            allDists, deltas, angles, most_perpendicular = zip(
                                *sorted(zip(allDists,
                                            deltas,
                                            angles,
                                            possible_connections[:]),
                                            key = operator.itemgetter(0, 1)))

            # compute angle difference
            aDelta = angles[0] - angles[1]

            # get node neighbours
            nNeighbours = self[node[0]]

            # CONNECTION FOR LEAST ANGLE CHANGE --------------------------------
            if len(nNeighbours) > 2 and aDelta < math.radians(6.0):
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
                dirA = Rhino.Geometry.Line(thisPt, mpA[1]["geo"]).Direction
                dirB = Rhino.Geometry.Line(thisPt, mpB[1]["geo"]).Direction
                dirA.Unitize()
                dirB.Unitize()

                # get normals for angle measurement
                normalA = Rhino.Geometry.Vector3d.CrossProduct(prevDir, dirA)
                normalB = Rhino.Geometry.Vector3d.CrossProduct(prevDir, dirB)

                # measure the angles
                angleA = Rhino.Geometry.Vector3d.VectorAngle(prevDir,
                                                             dirA,
                                                             normalA)
                angleB = Rhino.Geometry.Vector3d.VectorAngle(prevDir,
                                                             dirB,
                                                             normalB)

                # select final candidate for connection
                if angleA < angleB:
                    fCand = mpA
                else:
                    fCand = mpB

                # attempt connection to final candidate
                self._attempt_warp_connection_to_candidate(node,
                                                           fCand,
                                                           initial_nodes,
                                                           verbose)

            # CONNECTION FOR MOST PERPENDICULAR --------------------------------
            else:
                # print info on verbose setting
                if verbose:
                    print("Using procedure for most " +
                          "perpendicular connection...")
                # define final candidate node
                fCand = most_perpendicular[0]
                # attempt connection to final candidate
                self._attempt_warp_connection_to_candidate(node,
                                                           fCand,
                                                           initial_nodes,
                                                           verbose)

    def CreateWarpConnections(self, precise=False, verbose=False):
        """
        Loop through all the segment contours and create all 'warp' connections
        for this network.
        """

        # get all nodes by segment
        SegmentValues, AllNodesBySegment = zip(*self.AllNodesBySegment(True))

        # for each segment, get the 'next' segment as in the segment that is
        # connected to to the current segment via two 'end' nodes or a shared
        # 'end' node.
        # if there is no connection at the end of the segment, we have to
        # look for a connected segment and include the nodes on this segment

        for i, segment in enumerate(AllNodesBySegment):
            # get the 'segment' value attribute from the first node on the seg
            segval = SegmentValues[i]
            # get the first and last node ('end' nodes not included in the seg)
            firstNode = (segval[0], self.node[segval[0]])
            lastNode = (segval[1], self.node[segval[1]])

            # CASES:
            # 1: <======>
            # 2: <======/
            # 3: /======/
            # 4: /======>
            # 5: />
            # 6: </

            # get the segment that is connected to the first node either by
            # sharing this node or being connected through a 'warp' edge
            connected_segments = self.EndNodeSegments(firstNode[0])
            
            # TODO: sort the connected segments by their id and compare
            # with the current segments id. only consider segments with a higher
            # id (summing up the tuple should be sufficient)
            # print connected_segments

            if len(connected_segments) == 1:
                # obviously only this segment is connected to the end node at
                # its start. So we traverse the connected 'weft' edge
                cwe = self.NodeWarpEdges(firstNode[0])
                if len(cwe) > 1:
                    if verbose:
                        vStr = ("More than one warp edge connected to " +
                                "segment {} at start!")
                        vStr = vStr.format(segval)
                        print(vStr)
                    cwe_indices = [(c[0], c[1]) for c in cwe]
                    cwe_indices, cwe = zip(*sorted(zip(cwe_indices, cwe),
                                                   key=operator.itemgetter(0)))
                    cwe = cwe[-1]
                else:
                    cwe = cwe[0]
                next_segment_start = self.TraverseEdge(firstNode[0], cwe)
                next_connected_segments = self.EndNodeSegments(
                                                        next_segment_start[0])
                # the first segment in this list should be at least the start
                # of our target
                target_segment = next_connected_segments[0]
                targetLastNode = target_segment[2]["segment"][1]
                # check if the target segment shares an 'end' node with the
                # current segment
                shared_end_node = targetLastNode == lastNode[0]
                if shared_end_node:
                    # we have successfully verified our target segment and
                    # can create some warp edges! we start by getting all
                    # nodes on the target segment
                    target_nodes = [next_segment_start]
                    target_nodes.extend(self.NodesOnSegment(
                                        target_segment[2]["segment"], True))
                    target_nodes.append(targetLastNode)
                    current_nodes = [firstNode]
                    current_nodes.extend(segment)
                    current_nodes.append(lastNode)
                    segment_pair = [current_nodes, target_nodes]
                    self._create_initial_warp_connections(segment_pair,
                                                          precise,
                                                          verbose)
                else:
                    # check if the 'end' node at the end of the target shares
                    # a 'warp' edge with the current segment 'end' node at the
                    # end. Traverse all 'warp' edges connected to the
                    # targetLastNode to determine if there is a connection
                    tln_cwe = self.NodeWarpEdges(targetLastNode)
                    tln_cwe_other = [self.TraverseEdge(targetLastNode, c)[0] \
                                     for c in tln_cwe]
                    if lastNode[0] in tln_cwe_other:
                        # we have successfully verified our target segment and
                        # can create some warp edges! we start by getting all
                        # nodes on the target segment
                        target_nodes = [next_segment_start]
                        target_nodes.extend(self.NodesOnSegment(
                                            target_segment[2]["segment"], True))
                        target_nodes.append(targetLastNode)
                        current_nodes = [firstNode]
                        current_nodes.extend(segment)
                        current_nodes.append(lastNode)
                        segment_pair = [current_nodes, target_nodes]
                        self._create_initial_warp_connections(segment_pair,
                                                              precise,
                                                              verbose)
                    else:
                        # we have no connection between the current segment and
                        # the target segment at the end. we have to traverse the
                        # connected segment to the targets last 'end' node
                        # to find some more nodes
                        pass
            elif len(connected_segments) > 1:
                # look for the next segment that shares this node
                target_segment = self.EndNodeSegments(firstNode[0])[1]
