def _traverse_edge(self, startNode, connectedEdge):
    """
    Traverse an edge from a start node and return the other node.
    """

    if startNode != connectedEdge[0]:
        target_node = connectedEdge[0]
    elif startNode != connectedEdge[1]:
        target_node = connectedEdge[1]

    return self.nodes(data=True)[target_node]

def _traverse_weft_edge_until_end(self, startNode, lastEdge, wayNodes=None, wayEdges=None, endNodes=None):
    """
    Traverse a 'weft' edge segment until an 'end' vertex is hit.
    """

    # initialize output lists
    if wayNodes == None:
        wayNodes = [startNode[0]]
    if wayEdges == None:
        wayEdges = [lastEdge]
    if endNodes == None:
        endNodes = []

    connected_weft_edges = self.NodeWeftEdges(startNode[0], data=True)
    filtered_weft_edges = []
    for cwe in connected_weft_edges:
        if cwe[2]["segment"]:
            continue
        if cwe[0] == lastEdge[0] and cwe[1] == lastEdge[1]:
            continue
        elif cwe[1] == lastEdge[0] and cwe[0] == lastEdge[1]:
            continue
        filtered_weft_edges.append(cwe)

    if len(filtered_weft_edges) > 1:
        print(filtered_weft_edges)
        print("more than one filtered candidate weft edge!")
        return wayNodes, wayEdges, endNodes
    else:
        connected_node = self._traverse_edge(startNode[0],
                                             filtered_weft_edges[0])

        # if the connected node is an end node, the segment is finished
        if connected_node[1]["end"]:
            wayEdges.append(filtered_weft_edges[0])
            endNodes.append(connected_node[0])
            return wayNodes, wayEdges, endNodes

        else:
            # otherwise, append it to the return list and move on
            wayEdges.append(filtered_weft_edges[0])
            wayNodes.append(connected_node[0])
            return self._traverse_weft_edge_until_end(connected_node,
                                                     filtered_weft_edges[0],
                                                     wayNodes,
                                                     wayEdges,
                                                     endNodes)

def GetWeftEdgeSegmentation(self):
    """
    Get the segmentation for loop generation and assign segment attributes
    to 'weft' edges and vertices.
    """

    # get all contours of the network
    AllPositions = self.AllNodesByPosition(data=True)

    # get node and segment attributes
    node_segment_attributes = nx.get_node_attributes(self, "segment")
    edge_segment_attributes = nx.get_edge_attributes(self, "segment")

    # get all 'end' vertices ordered by poition
    all_ends_by_position = self.AllEndsByPosition(data=True)

    for i, position in enumerate(all_ends_by_position):
        for k, node in enumerate(position):

            # get connected weft edges
            weft_connections = self.NodeWeftEdges(node[0], data=True)

            # loop through all connected weft edges
            for cwe in weft_connections:
                if cwe[2]["segment"]:
                    continue

                # check the next connected node. if it is an end vertex,
                # set the respective keys
                connected_node = self._traverse_edge(node[0], cwe)

                if connected_node[1]["end"]:
                    if node[0] > connected_node[0]:
                        segStart = connected_node[0]
                        segEnd = node[0]
                    else:
                        segStart = node[0]
                        segEnd = connected_node[0]

                    edge_segment_attributes[(cwe[0], cwe[1])] = (segStart,
                                                                 segEnd)

                else:
                    res = self._traverse_weft_edge_until_end(connected_node,
                                                             cwe)
                    wayNodes, wayEdges, endNodes = res

                    if node[0] > endNodes[0]:
                        segStart = endNodes[0]
                        segEnd = node[0]
                    else:
                        segStart = node[0]
                        segEnd = endNodes[0]

                    for wayedge in wayEdges:
                        edge_segment_attributes[(wayedge[0],
                                           wayedge[1])] = (segStart, segEnd)
                    for waynode in wayNodes:
                        node_segment_attributes[waynode] = (segStart,
                                                            segEnd)

    nx.set_edge_attributes(self, "segment", edge_segment_attributes)
    nx.set_node_attributes(self, "segment", node_segment_attributes)

def GetWeftEdgeSegmentationParallel(self):
    """
    Get the segmentation for loop generation and assign segment attributes
    to 'weft' edges and vertices.
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

    for position in all_ends_by_position:
        # loop through all 'end' vertices
        for node in position:
            def threaded_func():
                self._get_segmentation_for_end_node(node)
            thread = Thread(target=threaded_func)
            thread.start()

    # add all previously removed edges back into the network

    [self.add_edge(edge[0], edge[1], edge[2]) for edge in \
     warp_storage + contour_storage]


# MAPPING NETWORK ----------------------------------------------------------

def _MAP_traverse_edge_until_end(self, startEndNode, startNode, wayNodes=None, wayEdges=None, endNodes=None):
    """
    Traverse a 'weft' edge segment until an 'end' vertex is hit.
    """

    # initialize output lists
    if wayNodes == None:
        wayNodes = deque(startNode[0])
    if wayEdges == None:
        wayEdges = deque()
    if endNodes == None:
        endNodes = deque()

    connected_weft_edges = self.edges(startNode[0], data=True)
    filtered_weft_edges = deque()
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

        connected_node = self._traverse_edge(startNode[0],
                                             fwec)

        # if the connected node is an end node, the segment is finished
        if connected_node[1]["end"]:

            endNodes.append(connected_node[0])
            wayEdges.append(fwec)

            return wayNodes, wayEdges, endNodes

        else:
            wayNodes.append(connected_node[0])
            wayEdges.append(fwec)

            return self._MAP_traverse_edge_until_end(startEndNode,
                                                 connected_node,
                                                 wayNodes,
                                                 wayEdges,
                                                 endNodes)
    else:
        return None

def _MAP_get_segmentation_for_end_node(self, node):
    """
    Function for finding and assigning 'segment' attributes
    to 'weft' edges and contained vertices.
    """

    # get connected weft edges
    weft_connections = self.edges(node[0], data=True)

    # loop through all connected weft edges
    for cwe in weft_connections:
        if cwe[2]["segment"]:
            continue

        # check the next connected node. if it is an end vertex,
        # set the respective keys
        connected_node = self._traverse_edge(node[0], cwe)

        if connected_node[1]["end"]:
            return [], [cwe], [connected_node[0]]

        else:
            return self._MAP_traverse_edge_until_end(node[0],
                                                     connected_node,
                                                     wayEdges=[cwe])

def GetSegmentationAndMappingNetwork(self):
    """
    Get the segmentation for loop generation and assign segment attributes
    to 'weft' edges and vertices. Create a mapping network out of it.
    """

    # remove contour and 'warp' edges and store them
    warp_storage = []
    for edge in self.edges(data=True):
        if not edge[2]["weft"]:
            if edge[2]["warp"]:
                warp_storage.append(edge)
            self.remove_edge(edge[0], edge[1])

    mapping_network = KnitMeshNetwork()

    # get all 'end' vertices ordered by poition
    all_ends_by_position = self.AllEndsByPosition(data=True)

    # loop through all 'end' vertices
    for position in all_ends_by_position:
        for node in position:
            result = self._MAP_get_segmentation_for_end_node(node)
            wayNodes, wayEdges, endNodes = result

            startNode = node
            endNode = (endnodes[0], self.node[endNodes[0]])
            # NOTE: OLD VERSION BELOW
            # endNode = self.nodes(data=True)[endNodes[0]]

            segment_geo = [e[2]["geo"] for e in wayEdges]
            mapping_network.CreateMappingWeftEdge(startNode,
                                                  endNode,
                                                  segment_geo)

    [mapping_network.add_edge(e[0], e[1], e[2]) for e in warp_storage]

    return mapping_network

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

            print("Processing Segment {} ...".format(segval))

            # CASE 1 - ENCLOSED SHORT ROW <=====> ------------------------------

            # define our educated guess for the target
            target_guess = (segval[0], segval[1], segval[2]+1)
            if target_guess in SegmentDict:
                # if this condition is True, we have found our target!
                target_segment = SegmentDict[target_guess][0]
                targetLastNode = target_segment[2]["segment"][1]

                print("<=====> detected. Connecting to segment {} ...".format(target_guess))

                # we have successfully verified our target segment and
                # can create some warp edges!
                target_nodes = SegmentDict[target_guess][1]
                current_nodes = segment
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
                target_nodes = SegmentDict[target_guess][1]
                current_nodes = segment
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
                target_nodes = SegmentDict[target_guess][1]
                current_nodes = segment
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
                # if this condition is True, we have found out target but need
                # to verify it geometrically to avoid weird connections
                target_segment = SegmentDict[target_guess][0]
                targetFirstNode = target_segment[2]["segment"][0]
                targetLastNode = target_segment[2]["segment"][1]

                # check if firstNode and targetFirstNode are connected via a
                # 'warp' edge to verify
                if (not targetFirstNode in self[firstNode[0]] \
                    and not targetLastNode in self[lastNode[0]]):
                    print("No real connection for /=====/. Skipping...")
                    continue

                print("/=====/ detected. Connecting to segment {} ...".format(target_guess))

                # we have successfully verified our target segment and
                # can create some warp edges!
                target_nodes = SegmentDict[target_guess][1]
                current_nodes = segment
                segment_pair = [current_nodes, target_nodes]
                selfCreateWarpConnections(segment_pair,
                                          max_connections=max_connections,
                                          precise=precise,
                                          verbose=verbose)
                continue

            # CASE 5 - TRAVERSAL NEEDED ----------------------------------------

            print("Traversal needed...")

            # we need to check if the current segment has a 'warp' edge
            # at the start whose target node index is exactly +1 (...=====/)
            warp_up_at_start = [nwe for nwe in selfNodeWarpEdges(firstNode[0]) \
                                if nwe[1] == firstNode[0]+1]
            if len(warp_up_at_start) > 0 or firstNode[1]["leaf"]:
                wupStartFlag = True
            else:
                wupStartFlag = False
                continue

            print("WUP START: ", wupStartFlag)

            # we need to check if the current segment has a 'warp' edge
            # at the end whose target node index is exactly +1 (...=====/)
            warp_up_at_end = [nwe for nwe in selfNodeWarpEdges(lastNode[0]) \
                              if nwe[1] == lastNode[0]+1]
            if len(warp_up_at_end) > 0 or lastNode[1]["leaf"]:
                wupEndFlag = True
            else:
                wupEndFlag = False

            print("WUP END: ", wupEndFlag)

            if wupEndFlag == True and wupStartFlag == True:
                # if there is a 'warp' edge up at the end of this segment, our
                # current segment is verified but we defintely need to traverse
                # our target
                current_nodes = segment
            else:
                # if there is no 'warp' edge up at the en of the segment, we need
                # to traverse this segment until we find one.

                print("Traversing current segment...")

                current_segment = (SegmentContourEdges[i][0], SegmentContourEdges[i][1])
                current_segment_array = self._traverse_segment_until_warp([current_segment], False)

                if len(current_segment_array) > 0:
                    print("Segment array: ", current_segment_array)
                else:
                    print("Segment array is empty....?!")

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
            connected_segments = selfEndNodeSegmentsByStart(firstNode[0], True)
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
                                                          next_segment_start[0], True)

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


# DINETWORK --------------------------------------------------------------------

def MakeCsvData(self):
    """
    Stuctures this network in a way that it can be represented as rows and
    columns to produce a 2d knitting pattern.

    Returns
    -------
    CSV Data
        List of lists (rows) where every value represents a node
    """

    # initialize dict for seen nodes and list for storage of rows
    seen = {}
    rows = []

    # initialize mapping dicts for ordering of rows and columns
    id2row= OrderedDict()
    node2id = OrderedDict()

    # every 'end' node defines the start of a row
    # loop over all 'end' nodes
    for node, data in self.EndNodes:
        # continue if this node has already been visited
        if node in seen:
            continue

        # get outgoing 'weft' edges of the current 'end' node
        nodeweft_out = self.NodeWeftEdgesOut(node, data=True)
        nodeweft_in = self.NodeWeftEdgesIn(node, data=True)

        # skip 'end' nodes which have only incoming 'weft' edges
        if nodeweft_in and not nodeweft_out:
            continue

        # if there is more than one outgoing weft edge, we have a problem
        if len(nodeweft_out) > 1:
            errMsg = "More than one outgoing 'weft' edge at " + \
                     "first row node {}!".format(node)
            raise KnitNetworkDualTopologyError(errMsg)
        # if this is a singular node, it is a separate row.
        elif len(nodeweft_out) == 0 and len(nodeweft_in) == 0:
            # append it as a row to the list of rows
            rows.append([node])
            # set the mapping dictionaries
            row_id = (node, node)
            id2row[row_id] = [node]
            node2id.update({node : row_id})
            # set the seen marker and continue to next 'end' node
            seen[node] = True
            continue
        # if there is exactly one 'weft' edge, traverse until next node
        elif len(nodeweft_out) == 1:
            # get the connected node to the current node
            connected_node = (nodeweft_out[0][1],
                              self.node[nodeweft_out[0][1]])
            # define initial row nodes with nodes of the first edge
            row_nodes = [node, connected_node[0]]
            # traverse as long as there is an outgoing next 'weft' edge
            # until an 'end' node is discovered
            while True:
                # get 'weft' edges of last node in row nodes
                next_weft = self.NodeWeftEdgesOut(row_nodes[-1])
                # if there is more than one connected 'weft' edge, we
                # have a problem
                if len(next_weft) > 1:
                    errMsg = "More than one outgoing 'weft' edge at " + \
                             "row node {}!".format(node)
                    raise KnitNetworkTopologyError(errMsg)
                # if there are no next 'weft' edges, row is complete
                elif len(next_weft) == 0:
                    if self.node[row_nodes[-1]]["end"]:
                        # this is the finishing 'end' node; set it seen
                        # and complete this row by breaking
                        seen[row_nodes[-1]] = True
                        break
                    # if there are no next 'weft' edges but this is not
                    # an 'end' node, we have a problem
                    else:
                        errMsg = "Unexpected end of row. Missing 'end' " + \
                               "attribute at node {}!".format(row_nodes[-1])
                        raise KnitNetworkTopologyError(errMsg)
                # if there is a next node over a weft edge, append to
                # row and continue
                elif len(next_weft) == 1:
                    row_nodes.append(next_weft[0][1])
                    continue
            # append the completed row to the list of rows
            rows.append(row_nodes)
            # set the mapping dictionaries
            row_id = (row_nodes[0], row_nodes[-1])
            id2row[row_id] = row_nodes
            node2id.update({node : row_id for node in row_nodes})
            # finally, set the current node as seen
            seen[node] = True

    # fill all the rows to minimum row length with placeholder values (-1)
    minrl = max([len(row) for row in rows])

    # loop over all rows and fill until minimum length
    for key in id2row.keys():
        row = id2row[key]
        for j in range(minrl):
            try:
                node = row[j]
            except IndexError:
                row.append(-1)
        id2row[key] = row

    # order all rows based network topology

    # loop over all rows and check warp edge connectivity
    # start with the first row in the list ...

    # order the sources and destinations
    # each row has to be "on top" of all of its sources and "below" all
    # of its destinations

    row_ids = id2row.keys()

    rowtarget = {}

    # TODO: same principle in reverse has also to be applied to the sources
    #       if this approach is valid at all
    # NOTE: establish "local order" by computing the maximum shortest path
    #       lengths between the current row and all its direct targets

    # NOTE: approach B: make a comparison function that compares two
    #       arbitrary rows and can decide if they should be swapped
    #       after that, a bubble sort or similar algorithm could be used

    # initialize mapping for dfs tree
    gmap = nx.DiGraph()

    for row_id in row_ids[:]:
        # find all targets of this particular row by checking all nodes
        # for targets and getting the corresponding row

        # get row from mapping dict
        row = id2row[row_id]
        # initialize list for storage of targets
        target_ids = []
        # loop over all nodes in the current row
        for node in row:
            # continue on -1 marker
            if node < 0:
                continue

            # check the node for outgoing warp edges and get its successor
            try:
                node_suc = self.NodeWarpEdgesOut(node)[0][1]
            except IndexError:
                continue

            # find the id of the row which contains the 'warp' edge
            # successor node
            target_id = node2id[node_suc]

            # if we already found this id before, continue
            if target_id in target_ids:
                continue

            # if its a new id, append it to the list of found target ids
            target_ids.append(target_id)

        [gmap.add_edge(row_id, tid) for tid in target_ids]

        # if there are no target ids, we have found an 'absolute end'
        if len(target_ids) == 0:
            # the absolute end can be extracted at its index and appended
            # to the end of the ordering
            row_ids.append(row_ids.pop(row_ids.index(row_id)))
        # if there are multiple targets, we need to build a local order (?)
        elif len(target_ids) > 1:
            # move all targets behind the current row
            # establish order by using the current index of the targets
            row_index = row_ids.index(row_id)
            initial_indices = [row_ids.index(r) for r in target_ids]
            initial_indices, target_ids = zip(*sorted(zip(initial_indices,
                                                          target_ids)))

            # move all the target ids behind the current row in order
            for i, tid in enumerate(target_ids):
                # remove the target ids from the list
                row_ids.pop(row_ids.index(tid))
                # insert the id after the current row / the last inserted id
                row_ids.insert(row_ids.index(row_id)+i, tid)

        # store all the sources in the mapping dict
        rowtarget[row_id] = target_ids

    ordered_rows = [id2row[id] for id in row_ids]

    # find roots of the mapping for dfs
    gmap.reverse(copy=False)
    leaves = []
    for node in gmap.nodes_iter():
        if not gmap.in_edges(node):
            leaves.append(node)

    # if there is a single leaf, we only need to execute one dfs
    if len(leaves) == 1:
        dfs_edges = list(nx.dfs_edges(gmap, leaves[0]))
    elif len(leaves) > 1:
        raise NotImplementedError("Multiple leaves are not implemented yet")

    dfs_rows = []

    for i, dfse in enumerate(dfs_edges):
        dfs_rows.append(id2row[dfse[0]])
        dfs_rows.append(id2row[dfse[1]])

    # return all rows
    return rows, ordered_rows, dfs_rows
