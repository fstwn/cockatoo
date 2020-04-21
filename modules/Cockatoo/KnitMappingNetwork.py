# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import division
from collections import deque
import math
from operator import itemgetter

# THIRD PARTY MODULE IMPORTS ---------------------------------------------------
import networkx as nx

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from .KnitNetworkBase import KnitNetworkBase

# ALL DICTIONARY ---------------------------------------------------------------
__all__ = [
    "KnitMappingNetwork"
]

# ACTUAL CLASS -----------------------------------------------------------------
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

    # SEGMENT CONTOUR METHODS --------------------------------------------------

    def TraverseSegmentsUntilWarp(self, way_segments, down=False, by_end=False):
        """
        Method for traversing a path of 'segment' edges until a 'warp'
        edge is discovered which points to the previous or the next segment.
        Returns the ids of the segment array

        Parameters
        ----------
        way_segments : list
            list of way segments

        down : bool

        by_end : bool
        """

        segment_list = way_segments
        flag = False
        while flag == False:
            # set the current segment
            current_segment = segment_list[-1]
            # traversal by segment endnode
            if by_end:
                # check that segment for 'warp' edges at the start
                warp_edges = self.NodeWarpEdges(current_segment[0])
                if down:
                    filtered_warp_edges = [we for we in warp_edges \
                                           if we[1] == current_segment[0]-1]
                else:
                    filtered_warp_edges = [we for we in warp_edges \
                                           if we[1] == current_segment[0]+1]

                # if there is a warp edge at the start, return the segment_list
                if (len(filtered_warp_edges) != 0 or (len(warp_edges) == 1 \
                    and self.node[current_segment[0]]["leaf"])):
                    flag = True
                    break
            # traversal by segment start node
            else:
                # check that segment for 'warp' edges at the end
                warp_edges = self.NodeWarpEdges(current_segment[1])
                if down:
                    filtered_warp_edges = [we for we in warp_edges \
                                           if we[1] == current_segment[1]-1]
                else:
                    filtered_warp_edges = [we for we in warp_edges \
                                           if we[1] == current_segment[1]+1]

                # if there is a warp edge at the end, our chain is finished
                if (len(filtered_warp_edges) != 0 or (len(warp_edges) == 1 \
                    and self.node[current_segment[1]]["leaf"])):
                    flag = True
                    break

            # get all connected segments at the last point of the segment
            if by_end:
                connected_segments = self.EndNodeSegmentsByEnd(
                                                  current_segment[0], data=True)
            else:
                connected_segments = self.EndNodeSegmentsByStart(
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

    # CREATION OF FINAL 'WARP' CONNECTIONS -------------------------------------

    def BuildChains(self, source_as_dict=False, target_as_dict=False):
        """
        Method for building source and target chains from segment
        contour edges.
        """

        # get all warp edges of this mappingnetwork
        AllWarpEdges = self.WarpEdges

        # initialize lists and dictionaries for storage of chains
        source_chains = []
        target_chains = []
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
            warpStartLeafFlag = self.node[warp_edge[0]]["leaf"]
            connected_start_segments = self.EndNodeSegmentsByStart(warpStart,
                                                                   data=True)
            # traverse segments from start node of 'warp' edge
            if len(connected_start_segments) > 0:
                for j, cs in enumerate(connected_start_segments):
                    # travel the connected segments at the start of the 'warp'
                    # edge until a 'upwards' connection is found and append
                    # it to the source chains of this pass
                    segment_chain = self.TraverseSegmentsUntilWarp(
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
                        segment_chain = self.TraverseSegmentsUntilWarp(
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
            warpEndLeafFlag = self.node[warp_edge[1]]["leaf"]
            connected_end_segments = self.EndNodeSegmentsByStart(warpEnd,
                                                                data=True)
            # traverse segments from end node of 'warp' edge
            if len(connected_end_segments) > 0:
                for j, cs in enumerate(connected_end_segments):
                    # if this is a 'leaf' node, first travel the segments until
                    # a 'upwards' connection is found and append this to the
                    # source (!) chains of this pass
                    if warpEndLeafFlag:
                        segment_chain = self.TraverseSegmentsUntilWarp(
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
                    segment_chain = self.TraverseSegmentsUntilWarp(
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
                    target_chains.append(chain)
                    target_chain_dict[chain[1]] = chain[0]

        # prepare the results and return them
        if source_as_dict:
            ret_source = source_chain_dict
        else:
            ret_source = source_chains

        if target_as_dict:
            ret_target = target_chain_dict
        else:
            ret_target = target_chains

        return (ret_source, ret_target)

# MAIN -------------------------------------------------------------------------
if __name__ == '__main__':
    pass
