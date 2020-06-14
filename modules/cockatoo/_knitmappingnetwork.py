# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from collections import deque
import math
from operator import itemgetter

# DUNDER -----------------------------------------------------------------------
__all__ = [
    "KnitMappingNetwork"
]

# THIRD PARTY MODULE IMPORTS ---------------------------------------------------
import networkx as nx

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from cockatoo._knitnetworkbase import KnitNetworkBase
from cockatoo.utilities import is_ccw_xy

# CLASS DECLARATION ------------------------------------------------------------
class KnitMappingNetwork(nx.MultiGraph, KnitNetworkBase):
    """
    Datastructure representing a mapping between connected chains of 'weft'
    edges in a KnitNetwork for final creation of 'weft' and 'warp' edges.

    Inherits from :class:`networkx.MultiGraph`, :class:`KnitNetworkBase`
    For more info, see *NetworkX* [13]_.

    Notes
    -----
    Not intended to be instantiated separately. Should only be instantiated
    by the KnitNetwork.create_mapping_network method!

    The implemented algorithms are strongly based on the paper
    *Automated Generation of Knit Patterns for Non-developable Surfaces* [1]_.
    Also see *KnitCrete - Stay-in-place knitted formworks for complex concrete
    structures* [2]_.

    The implementation was further influenced by concepts and ideas presented
    in the papers *Automatic Machine Knitting of 3D Meshes* [3]_,
    *Visual Knitting Machine Programming* [4]_ and
    *A Compiler for 3D Machine Knitting* [5]_.
    """

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
            name = "KnitMappingNetwork"

        nn = len(self.nodes())
        ce = len(self.contour_edges)
        wee = len(self.weft_edges)
        wae = len(self.warp_edges)
        data = ("({} Nodes, {} Segment Contours, {} Weft, {} Warp)")
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

    # SEGMENT CONTOUR METHODS --------------------------------------------------

    def traverse_segments_until_warp(self, way_segments, down=False, by_end=False):
        """
        Method for traversing a path of 'segment' edges until a 'warp'
        edge is discovered which points to the previous or the next segment.
        Returns the ids of the segment array.

        Parameters
        ----------
        way_segments : :obj:`list`
            List of segments that is filled during method execution. The list
            should contain the start segment when calling this method!

        down : bool, optional
            If ``True``, will traverse until a downwards 'warp' edge is
            discovered, otherwise will traverse antil an upwards 'warp' edge
            is discovered.

            Defaults to ``False``

        by_end : bool, optional
            If ``True``, will traverse the 'segment' edges in the opposite
            direction.

            Defaults to ``False``.

        Returns
        -------
        segments : :obj:`list`
            List of segments representing a chain.

        Raises
        ------
        ValueError:
            If ``way_segments`` is empty at call.
        """
        if len(way_segments) == 0:
            errMsg = "Argument way_segments has to contain the starting " + \
                     "segment when calling this method!"
            raise ValueError(errMsg)

        segment_list = way_segments
        flag = False
        while flag == False:
            # set the current segment
            current_segment = segment_list[-1]
            # traversal by segment endnode
            if by_end:
                # check that segment for 'warp' edges at the start
                warp_edges = self.node_warp_edges(current_segment[0])
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
                warp_edges = self.node_warp_edges(current_segment[1])
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
                connected_segments = self.end_node_segments_by_end(
                                                  current_segment[0], data=True)
            else:
                connected_segments = self.end_node_segments_by_start(
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

    def build_chains(self, source_as_dict=False, target_as_dict=False):
        """
        Method for building source and target chains from segment
        contour edges.

        Parameters
        ----------
        source_as_dict : bool
            If ``True``, will return the source chains as a dictionary indexed
            by their chain value.

        target_as_dict : bool
            If ``True``, will return the target chains as a dictionary indexed
            by their chain value.

        Returns
        -------
        chains : :obj:`tuple` of :obj:`list`
            2-tuple in the form of (source_chains, target_chains).
        """

        # get all warp edges of this mappingnetwork
        AllWarpEdges = self.warp_edges
        AllWarpEdges.sort(key=lambda e: e[0])

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
            warpStartLeafFlag = self.node[warpStart]["leaf"]
            connected_start_segments = self.end_node_segments_by_start(warpStart,
                                                                   data=True)

            # TODO:
            # 1) build plane for reference. plane should be fit through warp
            #    edge points and points on the connecting segments.
            #    for example use the end of the first segment of the underlying
            #    polyline geometry
            # 2) for every pt get pt on the reference plane
            # 3) order all segments in reference to the warp edges direction
            #    all segment endpts

            # if len(connected_start_segments) > 1:
            #     # get start node geo of warp edge
            #     ws_pt = self.node[warpStart]["geo"]
            #     # css geo is always a polyline
            #     css_pls = [css[2]["geo"] for css in connected_start_segments]
            #     # get the endpt of the first segment from the polyline as reference
            #     # for the direction of the segment
            #     css_refpts = [csspl[1] for csspl in css_pls]
            #
            #     # construct local reference plane
            #     # x-axis is an arbitrary dir of the connected segments
            #     # y-axis is the warp edge
            #     local_x = css_refpts[0] - ws_pt
            #     local_x = RhinoVector3d(local_x)
            #     local_y = warp_edge[2]["geo"].To - warp_edge[2]["geo"].From
            #     local_y = RhinoVector3d(local_y)
            #     localplane = RhinoPlane(ws_pt, local_x, local_y)
            #
            #     # fit plane to points
            #     fitplane = RhinoPlane.FitPlaneToPoints(css_refpts + [ws_pt])[1]
            #     fitplane_origin = fitplane.ClosestPoint(ws_pt)
            #     fitplane.Origin = fitplane_origin
            #     if fitplane.Normal * localplane.Normal < 0:
            #         fitplane.Flip()
            #
            #     # map all the points to the plane space
            #     a = fitplane.RemapToPlaneSpace(fitplane_origin)[1]
            #     css_refpts_remapped = []
            #     for csspt in css_refpts:
            #         cp = fitplane.ClosestPoint(csspt)
            #         rmp = fitplane.RemapToPlaneSpace(cp)[1]
            #         css_refpts_remapped.append(rmp)
            #
            #     # zip the segments and the refpts
            #     zipped_segs = zip(css_refpts_remapped, connected_start_segments)
            #
            #     # append first item to ordered list
            #     ordered_zippedsegs = zipped_segs[0:1]
            #
            #     # loop over all items except the first one and compare
            #     # sort the zipped segs in ccw order
            #     for j, zipseg in enumerate(zipped_segs[1:]):
            #         c = zipseg[0]
            #         pos = 0
            #         b = ordered_zippedsegs[pos][0]
            #         while not is_ccw_xy(a, b, c):
            #             pos += 1
            #             if pos > j:
            #                 break
            #             b = ordered_zippedsegs[pos][0]
            #         if pos == 0:
            #             pos -= 1
            #             b = ordered_zippedsegs[pos][0]
            #             while is_ccw_xy(a, b, c):
            #                 pos -= 1
            #                 if pos < -len(ordered_zippedsegs):
            #                     break
            #                 b = ordered_zippedsegs[pos][0]
            #             pos += 1
            #         ordered_zippedsegs.insert(pos, zipseg)
            #
            #     ordered_pts, connected_start_segments = zip(*ordered_zippedsegs)

            # traverse segments from start node of 'warp' edge
            if len(connected_start_segments) > 0:
                for j, cs in enumerate(connected_start_segments):
                    # travel the connected segments at the start of the 'warp'
                    # edge until a 'upwards' connection is found and append
                    # it to the source chains of this pass
                    segment_chain = self.traverse_segments_until_warp(
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
                        segment_chain = self.traverse_segments_until_warp(
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
            warpEndLeafFlag = self.node[warpEnd]["leaf"]
            connected_end_segments = self.end_node_segments_by_start(warpEnd,
                                                                data=True)
            # traverse segments from end node of 'warp' edge
            if len(connected_end_segments) > 0:
                for j, cs in enumerate(connected_end_segments):
                    # if this is a 'leaf' node, first travel the segments until
                    # a 'upwards' connection is found and append this to the
                    # source (!) chains of this pass
                    if warpEndLeafFlag:
                        segment_chain = self.traverse_segments_until_warp(
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
                    segment_chain = self.traverse_segments_until_warp(
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
