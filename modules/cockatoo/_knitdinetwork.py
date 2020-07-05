# PYTHON STANDARD LIBRARY IMPORTS ---------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from collections import deque
from collections import OrderedDict
import math
from operator import itemgetter

# DUNDER ----------------------------------------------------------------------
__all__ = [
    "KnitDiNetwork"
]

# LOCAL MODULE IMPORTS --------------------------------------------------------
from cockatoo._knitnetworkbase import KnitNetworkBase
from cockatoo.environment import RHINOINSIDE
from cockatoo.exception import KnitNetworkTopologyError
from cockatoo.utilities import is_ccw_xy
from cockatoo.utilities import pairwise
from cockatoo.utilities import tween_planes

# THIRD PARTY MODULE IMPORTS --------------------------------------------------
import networkx as nx

# RHINO IMPORTS ---------------------------------------------------------------
if RHINOINSIDE:
    import rhinoinside
    rhinoinside.load()
    from Rhino.Geometry import Mesh as RhinoMesh
    from Rhino.Geometry import MeshNgon as RhinoMeshNgon
    from Rhino.Geometry import NurbsSurface as RhinoNurbsSurface
    from Rhino.Geometry import Plane as RhinoPlane
    from Rhino.Geometry import Point3d as RhinoPoint3d
    from Rhino.Geometry import Vector3d as RhinoVector3d
else:
    from Rhino.Geometry import Mesh as RhinoMesh
    from Rhino.Geometry import MeshNgon as RhinoMeshNgon
    from Rhino.Geometry import NurbsSurface as RhinoNurbsSurface
    from Rhino.Geometry import Plane as RhinoPlane
    from Rhino.Geometry import Point3d as RhinoPoint3d
    from Rhino.Geometry import Vector3d as RhinoVector3d

# CLASS DECLARATION -----------------------------------------------------------
class KnitDiNetwork(nx.DiGraph, KnitNetworkBase):
    """
    Datastructure representing a directed graph of nodes aswell as 'weft'
    and 'warp' edges. Used in the automatic generation of knitting patterns.

    Inherits from :class:`networkx.DiGraph`, :class:`KnitNetworkBase`.
    For more info, see *NetworkX* [13]_.

    Notes
    -----
    The implemented algorithms are strongly based on the paper
    *Automated Generation of Knit Patterns for Non-developable Surfaces* [1]_.
    Also see *KnitCrete - Stay-in-place knitted formworks for complex concrete
    structures* [2]_.

    The implementation was further influenced by concepts and ideas presented
    in the papers *Automatic Machine Knitting of 3D Meshes* [3]_,
    *Visual Knitting Machine Programming* [4]_ and
    *A Compiler for 3D Machine Knitting* [5]_.
    """

    # INITIALIZATION ----------------------------------------------------------

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
        super(KnitDiNetwork, self).__init__(data=data, **attr)

        # also copy the mapping_network attribute if it is already available
        if data and isinstance(data, KnitDiNetwork) and data.mapping_network:
            self.mapping_network = data.mapping_network
        else:
            self.mapping_network = None

        # also copy or initialize the halfedge dict for finding faces
        if data and isinstance(data, KnitDiNetwork) and data.halfedge:
            self.halfedge = data.halfedge
        else:
            self.halfedge = {}

    # TEXTUAL REPRESENTATION OF NETWORK ---------------------------------------

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
            name = "KnitDiNetwork"

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

    # NODE WEFT EDGE METHODS --------------------------------------------------

    def node_weft_edges_out(self, node, data=False):
        """
        Gets the outgoing 'weft' edges connected to the given node.

        Parameters
        ----------
        node : hashable
            Hashable identifier of the node to check for outgoing 'weft' edges.

        data : bool, optional
            If ``True``, will also return the edges associated data attribute
            dictionary.

            Defaults to ``False``.

        Returns
        -------
        weft_edges : :obj:`list`
            List of outgoing 'weft' edges.
        """

        weft_edges = [(s, e, d) for s, e, d in \
                     self.edges_iter(node, data=True) if d["weft"]]

        if data:
            return weft_edges
        else:
            return [(e[0], e[1]) for e in weft_edges]

    def node_weft_edges_in(self, node, data=False):
        """
        Gets the incoming 'weft' edges connected to the given node.

        Parameters
        ----------
        node : hashable
            Hashable identifier of the node to check for incoming 'weft' edges.

        data : bool, optional
            If ``True``, will also return the edges associated data attribute
            dictionary.

            Defaults to ``False``.

        Returns
        -------
        weft_edges : :obj:`list`
            List of incoming 'weft' edges.
        """

        weft_edges = [(s, e, d) for s, e, d in \
                     self.in_edges_iter(node, data=True) if d["weft"]]

        if data:
            return weft_edges
        else:
            return [(e[0], e[1]) for e in weft_edges]

    def node_weft_edges(self, node, data=False):
        """
        Gets incoming and outgoing 'weft' edges connected to the given node.

        Parameters
        ----------
        node : hashable
            Hashable identifier of the node to check for incoming and outgoing
            'weft' edges.

        data : bool, optional
            If ``True``, will also return the edges associated data attribute
            dictionary.

            Defaults to ``False``.

        Returns
        -------
        weft_edges : :obj:`list`
            List of incoming and outgoing 'weft' edges.
        """

        weft_edges = [(s, e, d) for s, e, d in \
                     self.edges_iter(node, data=True) if d["weft"]]
        weft_edges.extend((s, e, d) for s, e, d in \
                     self.in_edges_iter(node, data=True) if d["weft"])

        if data:
            return weft_edges
        else:
            return [(e[0], e[1]) for e in weft_edges]

    # NODE WARP EDGE METHODS --------------------------------------------------

    def node_warp_edges_out(self, node, data=False):
        """
        Gets the outgoing 'warp' edges connected to the given node.

        Parameters
        ----------
        node : hashable
            Hashable identifier of the node to check for outgoing 'warp' edges.

        data : bool, optional
            If ``True``, will also return the edges associated data attribute
            dictionary.

            Defaults to ``False``.

        Returns
        -------
        weft_edges : :obj:`list`
            List of outgoing 'warp' edges.
        """

        warp_edges = [(s, e, d) for s, e, d in \
                     self.edges_iter(node, data=True) if d["warp"]]

        if data:
            return warp_edges
        else:
            return [(e[0], e[1]) for e in warp_edges]

    def node_warp_edges_in(self, node, data=False):
        """
        Gets the incoming 'warp' edges connected to the given node.

        Parameters
        ----------
        node : hashable
            Hashable identifier of the node to check for incoming 'warp' edges.

        data : bool, optional
            If ``True``, will also return the edges associated data attribute
            dictionary.

            Defaults to ``False``.

        Returns
        -------
        weft_edges : :obj:`list`
            List of incoming 'warp' edges.
        """

        warp_edges = [(s, e, d) for s, e, d in \
                     self.in_edges_iter(node, data=True) if d["warp"]]

        if data:
            return warp_edges
        else:
            return [(e[0], e[1]) for e in warp_edges]

    def node_warp_edges(self, node, data=False):
        """
        Gets the incoming and outgoing 'warp' edges connected to the given node.

        Parameters
        ----------
        node : hashable
            Hashable identifier of the node to check for incoming and outgoing
            'warp' edges.

        data : bool, optional
            If ``True``, will also return the edges associated data attribute
            dictionary.

            Defaults to ``False``.

        Returns
        -------
        weft_edges : :obj:`list`
            List of incoming and outgoing 'warp' edges.
        """

        warp_edges = [(s, e, d) for s, e, d in \
                     self.edges_iter(node, data=True) if d["warp"]]
        warp_edges.extend((s, e, d) for s, e, d in \
                     self.in_edges_iter(node, data=True) if d["warp"])

        if data:
            return warp_edges
        else:
            return [(e[0], e[1]) for e in warp_edges]

    # NODE CONTOUR EDGE METHODS -----------------------------------------------

    def node_contour_edges_out(self, node, data=False):
        """
        Gets the outgoing edges marked neither 'warp' nor 'weft' connected to
        the given node.

        Parameters
        ----------
        node : hashable
            Hashable identifier of the node to check for outgoing edges neither
            'weft' nor 'warp'.

        data : bool, optional
            If ``True``, will also return the edges associated data attribute
            dictionary.

            Defaults to ``False``.

        Returns
        -------
        weft_edges : :obj:`list`
            List of outgoing edges neither 'weft' nor 'warp'.
        """

        contour_edges = [(s, e, d) for s, e, d in \
                        self.edges_iter(node, data=True) \
                        if not d["warp"] and not d["weft"]]

        if data:
            return contour_edges
        else:
            return [(e[0], e[1]) for e in contour_edges]

    def node_contour_edges_in(self, node, data=False):
        """
        Gets the incoming edges marked neither 'warp' nor 'weft' connected to
        the given node.

        Parameters
        ----------
        node : hashable
            Hashable identifier of the node to check for incoming edges neither
            'weft' nor 'warp'.

        data : bool, optional
            If ``True``, will also return the edges associated data attribute
            dictionary.

            Defaults to ``False``.

        Returns
        -------
        weft_edges : :obj:`list`
            List of incoming edges neither 'weft' nor 'warp'.
        """

        contour_edges = [(s, e, d) for s, e, d in
                         self.in_edges_iter(node, data=True)
                         if not d["warp"] and not d["weft"]]

        if data:
            return contour_edges
        else:
            return [(e[0], e[1]) for e in contour_edges]

    def node_contour_edges(self, node, data=False):
        """
        Gets the incoming and outcoing edges marked neither 'warp' nor 'weft'
        connected to the given node.

        Parameters
        ----------
        node : hashable
            Hashable identifier of the node to check for incoming and outgoing
            edges neither 'weft' nor 'warp'.

        data : bool, optional
            If ``True``, will also return the edges associated data attribute
            dictionary.

            Defaults to ``False``.

        Returns
        -------
        weft_edges : :obj:`list`
            List of incoming and outgoing edges neither 'weft' nor 'warp'.
        """

        contour_edges = [(s, e, d) for s, e, d in \
                        self.edges_iter(node, data=True) \
                        if not d["warp"] and not d["weft"]]
        contour_edges.extend([(s, e, d) for s, e, d in \
                        self.in_edges_iter(node, data=True) \
                        if not d["warp"] and not d["weft"]])

        if data:
            return contour_edges
        else:
            return [(e[0], e[1]) for e in contour_edges]

    # FIND FACES (CYCLES) OF NETWORK -------------------------------------------

    def _sort_node_neighbors(self, key, nbrs, xyz, geo, cbp, nrm, mode=-1, ccw=True):
        """
        Sort the neighbors of a network node.

        Notes
        -----
        Based on an implementation inside the COMPAS framework.
        For more info see [7]_.

        References
        ----------
        .. [7] Van Mele, Tom et al. *COMPAS: A framework for computational
               research in architecture and structures*.

               See: `sort_node_neighbors() inside COMPAS <https://github.com/compas-dev/compas/blob/e313502995b0dd86d460f86e622cafc0e29d1b75/src/compas/datastructures/network/duality.py#L132>`_
        """

        # if there is only one neighbor we don't need to sort anything
        if len(nbrs) == 1:
            return nbrs

        # initialize the ordered list of neighbors with the first node
        ordered_nbrs = nbrs[0:1]

        # retrieve coordinates for current node
        a = xyz[key]

        # compute local orientation if reference geometry data is present
        # CASE 1: Plane is determined by mesh normal of origin node
        if cbp and nrm and mode == 0:
            # construct local reference plane and map coordinates to plane space
            a_geo = geo[key]
            localplane = RhinoPlane(a_geo, nrm[key])
            a_local = localplane.RemapToPlaneSpace(a_geo)[1]
            a = (a_local.X, a_local.Y, a_local.Z)
            # compute local plane coordinates for all neighbors
            xyz_local = {}
            for nbr in nbrs:
                # find closest point on plane and remap to plane space
                nbr_cp = localplane.ClosestPoint(geo[nbr])
                local_nbr = localplane.RemapToPlaneSpace(nbr_cp)[1]
                nbr_coords = (local_nbr.X, local_nbr.Y, local_nbr.Z)
                # set coordinate dict value
                xyz_local[nbr] = nbr_coords
            # reassign coordinate dictionary for neighbor sorting
            xyz = xyz_local
        # CASE 2: Plane is determined by average normal of origin node and nbrs
        elif cbp and nrm and mode == 1:
            # construct local reference plane and map coordinates to plane space
            a_geo = geo[key]
            # get average normal
            avg_nrm = nrm[key]
            nbr_nrms = [nrm[n] for n in nbrs]
            for nv in nbr_nrms:
                avg_nrm += nv
            # construct plane based on average normal
            localplane = RhinoPlane(a_geo, avg_nrm)
            a_local = localplane.RemapToPlaneSpace(a_geo)[1]
            a = (a_local.X, a_local.Y, a_local.Z)
            # compute local plane coordinates for all neighbors
            xyz_local = {}
            for nbr in nbrs:
                # find closest point on plane and remap to plane space
                nbr_cp = localplane.ClosestPoint(geo[nbr])
                local_nbr = localplane.RemapToPlaneSpace(nbr_cp)[1]
                nbr_coords = (local_nbr.X, local_nbr.Y, local_nbr.Z)
                # set coordinate dict value
                xyz_local[nbr] = nbr_coords
            # reassign coordinate dictionary for neighbor sorting
            xyz = xyz_local
        # CASE 3: Plane is determined by avg between fitplane and avg meshplane
        elif cbp and nrm and mode == 2:
            # construct local reference plane and map coordinates to plane space
            a_geo = geo[key]
            # get average normal
            avg_nrm = nrm[key]
            nbr_nrms = [nrm[n] for n in nbrs]
            for nv in nbr_nrms:
                avg_nrm += nv
            # construct plane based on average normal
            localplane = RhinoPlane(a_geo, avg_nrm)
            fitplane = RhinoPlane.FitPlaneToPoints([geo[n] for n in nbrs])[1]
             # align fitplane with localplane
            if fitplane.Normal * localplane.Normal < 0:
                fitplane.Flip()
            # tween the planes and set origin
            tweenplane = tween_planes(localplane, fitplane, 0.5)
            tweenplane.Origin = a_geo
            # remap origin node to plane space
            a_local = tweenplane.RemapToPlaneSpace(a_geo)[1]
            a = (a_local.X, a_local.Y, a_local.Z)
            # compute local plane coordinates for all neighbors
            xyz_local = {}
            for nbr in nbrs:
                # find closest point on plane and remap to plane space
                nbr_cp = tweenplane.ClosestPoint(geo[nbr])
                local_nbr = tweenplane.RemapToPlaneSpace(nbr_cp)[1]
                nbr_coords = (local_nbr.X, local_nbr.Y, local_nbr.Z)
                # set coordinate dict value
                xyz_local[nbr] = nbr_coords
            # reassign coordinate dictionary for neighbor sorting
            xyz = xyz_local

        # loop over all neighbors except the first one
        for i, nbr in enumerate(nbrs[1:]):
            c = xyz[nbr]
            pos = 0
            b = xyz[ordered_nbrs[pos]]
            while not is_ccw_xy(a, b, c):
                pos += 1
                if pos > i:
                    break
                b = xyz[ordered_nbrs[pos]]
            if pos == 0:
                pos -= 1
                b = xyz[ordered_nbrs[pos]]
                while is_ccw_xy(a, b, c):
                    pos -= 1
                    if pos < -len(ordered_nbrs):
                        break
                    b = xyz[ordered_nbrs[pos]]
                pos += 1
            ordered_nbrs.insert(pos, nbr)

        # return the ordered neighbors in cw or ccw order
        if not ccw:
            return ordered_nbrs[::-1]
        return ordered_nbrs

    def _sort_neighbors(self, mode=-1, ccw=True):
        """
        Sort the neighbors of all network nodes.

        Notes
        -----
        Based on an implementation inside the COMPAS framework.
        For more info see [8]_.

        References
        ----------
        .. [8] Van Mele, Tom et al. *COMPAS: A framework for computational
               research in architecture and structures*.

               See: `sort_neighbors() inside COMPAS <https://github.com/compas-dev/compas/blob/e313502995b0dd86d460f86e622cafc0e29d1b75/src/compas/datastructures/network/duality.py#L121>`_
        """

        # initialize sorted neighbors dict
        sorted_neighbors = {}

        # get dictionary of all coordinates by node index
        xyz = {k: (d["x"], d["y"], d["z"]) for k, d in self.nodes_iter(True)}
        geo = {k: d["geo"] for k, d in self.nodes_iter(True)}

        # compute local orientation data when reference geometry is present
        try:
            reference_geometry = self.graph["reference_geometry"]
        except KeyError:
            reference_geometry = None

        if not reference_geometry:
            cbp = None
            nrm = None
        elif isinstance(reference_geometry, RhinoMesh):
            cbp = {k: reference_geometry.ClosestMeshPoint(geo[k], 0) \
                   for k in self.nodes_iter()}
            nrm = {k: reference_geometry.NormalAt(cbp[k]) \
                   for k in self.nodes_iter()}
        elif isinstance(reference_geometry, RhinoNurbsSurface):
            cbp = {k: reference_geometry.ClosestPoint(geo[k])[1:] \
                   for k in self.nodes_iter()}
            nrm = {k: reference_geometry.NormalAt(cbp[k][0], cbp[k][1]) \
                   for k in self.nodes_iter()}

        # loop over all nodes in network
        for key in self.nodes_iter():
            nbrs = self[key].keys()
            sorted_neighbors[key] = self._sort_node_neighbors(
                                                            key,
                                                            nbrs,
                                                            xyz,
                                                            geo,
                                                            cbp,
                                                            nrm,
                                                            mode=mode,
                                                            ccw=ccw)

        # set the sorted neighbors list as an attribute to the nodes
        for key, nbrs in sorted_neighbors.items():
            self.node[key]["sorted_neighbors"] = nbrs[::-1]

        # return the sorted neighbors dict
        return sorted_neighbors

    def _find_first_node_neighbor(self, key):
        """
        Find the first neighbor for a given node in the network.

        Notes
        -----
        Based on an implementation inside the COMPAS framework.
        For more info see [9]_.

        References
        ----------
        .. [9] Van Mele, Tom et al. *COMPAS: A framework for computational
               research in architecture and structures*.

               See: `find_first_node_neighbor() inside COMPAS <https://github.com/compas-dev/compas/blob/e313502995b0dd86d460f86e622cafc0e29d1b75/src/compas/datastructures/network/duality.py#L103>`_
        """

        # get all node neighbors
        nbrs = self[key].keys()

        # if there is only one neighbor, we have already found our candidate
        if len(nbrs) == 1:
            return nbrs[0]

        ab = [-1.0, -1.0, 0.0]
        rhino_ab = RhinoVector3d(*ab)
        a = self.node_coordinates(key)
        b = [a[0] + ab[0], a[1] + ab[1], 0]

        angles = []
        for nbr in nbrs:
            c = self.node_coordinates(nbr)
            ac = [c[0] - a[0], c[1] - a[1], 0]
            rhino_ac = RhinoVector3d(*ac)
            alpha = RhinoVector3d.VectorAngle(rhino_ab, rhino_ac)
            if is_ccw_xy(a, b, c, True):
                alpha = (2 * math.pi) - alpha
            angles.append(alpha)

        return nbrs[angles.index(min(angles))]

    def _find_edge_cycle(self, u, v):
        """
        Find a cycle based on the given edge.

        Parameters
        ----------
        u : hashable
            Index of the start node of the origin edge for the cycle.

        v : hashable
            Index of the end node of the origin edge for the cycle.

        Notes
        -----
        Based on an implementation inside the COMPAS framework.
        For more info see [6]_.

        References
        ----------
        .. [6] Van Mele, Tom et al. *COMPAS: A framework for computational
               research in architecture and structures*.

               See: `find_edge_cycle() inside COMPAS <https://github.com/compas-dev/compas/blob/09153de6718fb3d49a4650b89d2fe91ea4a9fd4a/src/compas/datastructures/network/duality.py#L161>`_
        """
        cycle = [u]
        while True:
            cycle.append(v)
            nbrs = self.node[v]["sorted_neighbors"]
            nbr = nbrs[nbrs.index(u) - 1]
            u, v = v, nbr
            if v == cycle[0]:
                break
        return cycle

    def find_cycles(self, mode=-1):
        """
        Finds the cycles (faces) of this network by utilizing a wall-follower
        mechanism.

        Parameters
        ----------
        mode : int, optional
            Determines how the neighbors of each node are sorted when finding
            cycles for the network.

            ``-1`` equals to using the world XY plane.

            ``0`` equals to using a plane normal to the origin nodes closest
            point on the reference geometry.

            ``1`` equals to using a plane normal to the average of the origin
            and neighbor nodes' closest points on the reference geometry.

            ``2`` equals to using an average plane between a plane fit to the
            origin and its neighbor nodes and a plane normal to the origin
            nodes closest point on the reference geometry.

            Defaults to ``-1``.

        Warning
        -------
        Modes other than -1 (default) are only possible if this network has an
        underlying reference geometry in form of a Mesh or NurbsSurface. The
        reference geometry should be assigned when initializing the network by
        assigning the geometry to the "reference_geometry" attribute of the network.

        Notes
        -----
        Based on an implementation inside the COMPAS framework.
        For more info see [17]_.

        References
        ----------
        .. [17] Van Mele, Tom et al. *COMPAS: A framework for computational
               research in architecture and structures*.

               See: `find_cycles() inside COMPAS <https://github.com/compas-dev/compas/blob/09153de6718fb3d49a4650b89d2fe91ea4a9fd4a/src/compas/datastructures/network/duality.py#L20>`_
        """

        # initialize the halfedge dict of the directed network
        for u, v in self.edges_iter():
            try:
                self.halfedge[u][v] = None
            except KeyError:
                self.halfedge[u] = {}
                self.halfedge[u][v] = None
            try:
                self.halfedge[v][u] = None
            except KeyError:
                self.halfedge[v] = {}
                self.halfedge[v][u] = None

        # sort the all the neighbors for each node of the network
        self._sort_neighbors(mode=mode)

        # find start node
        # sort leaf nodes by y and x coordinates
        # leaves = self.leaf_nodes
        # if leaves:
        #     u = sorted(leaves, key=lambda n: (n[1]["y"], n[1]["x"]))[0][0]
        # else:
        #     u = sorted(self.nodes_iter(data=True), key=lambda n: (n[1]["y"], n[1]["x"]))[0][0]

        # find start node
        # sort leaf nodes by node identifier / index
        leaves = self.leaf_nodes
        if leaves:
            u = sorted(leaves, key=lambda n: n[0])[0][0]
        else:
            u = sorted(self.nodes_iter(data=True), key=lambda n: n[0])[0][0]

        # initialize found and cycles dict
        cycles = {}
        found = {}
        ckey = 0

        # find the very first cycle
        v = self._find_first_node_neighbor(u)
        cycle = self._find_edge_cycle(u, v)
        frozen = frozenset(cycle)
        found[frozen] = ckey
        cycles[ckey] = cycle

        # set halfedge dict
        for a, b in pairwise(cycle + cycle[:1]):
            self.halfedge[a][b] = ckey
        ckey += 1

        # loop over all edges and find cycles
        for u, v in self.edges_iter():
            # find cycles for u -> v edges
            if self.halfedge[u][v] is None:
                cycle = self._find_edge_cycle(u, v)
                frozen = frozenset(cycle)
                if frozen not in found:
                    found[frozen] = ckey
                    cycles[ckey] = cycle
                    ckey += 1
                for a, b in pairwise(cycle + cycle[:1]):
                    self.halfedge[a][b] = found[frozen]
            # find cycles for v -> u edges
            if self.halfedge[v][u] is None:
                cycle = self._find_edge_cycle(v, u)
                frozen = frozenset(cycle)
                if frozen not in found:
                    found[frozen] = ckey
                    cycles[ckey] = cycle
                    ckey += 1
                for a, b in pairwise(cycle + cycle[:1]):
                    self.halfedge[a][b] = found[frozen]

        return cycles

    # MESHING ------------------------------------------------------------------

    def create_mesh(self, mode=-1, max_valence=4):
        """
        Constructs a mesh from this network by finding cycles and using them as
        mesh faces.

        Parameters
        ----------
        mode : int, optional
            Determines how the neighbors of each node are sorted when finding
            cycles for the network.

            ``-1`` equals to using the world XY plane.

            ``0`` equals to using a plane normal to the origin nodes closest
            point on the reference geometry.

            ``1`` equals to using a plane normal to the average of the origin
            and neighbor nodes' closest points on the reference geometry.

            ``2`` equals to using an average plane between a plane fit to the
            origin and its neighbor nodes and a plane normal to the origin
            nodes closest point on the reference geometry.

            Defaults to ``-1``.

        max_valence : int, optional
            Sets the maximum edge valence of the faces. If this is set to > 4,
            n-gon faces (more than 4 edges) are allowed. Otherwise, their cycles
            are treated as invalid and will be ignored.

            Defaults to ``4``.

        Warning
        -------
        Modes other than ``-1`` are only possible if this network has an
        underlying reference geometry in form of a Mesh or NurbsSurface. The
        reference geometry should be assigned when initializing the network by
        assigning the geometry to the "reference_geometry" attribute of the
        network.
        """

        # get cycles dict of this network
        cycles = self.find_cycles(mode=mode)

        # create an empty mesh
        Mesh = RhinoMesh()

        # intialize mapping of network nodes to mesh vertices
        node_to_vertex = {}
        vcount = 0

        # fill mesh and map network nodes to mesh vertices
        for node, data in self.nodes_iter(data=True):
            node_to_vertex[node] = vcount
            Mesh.Vertices.Add(data["x"], data["y"], data["z"])
            vcount += 1

        # loop over cycles and add faces to the mesh
        fcount = 0
        for ckey in cycles.keys():
            cycle = cycles[ckey]
            c_len = len(cycle)
            if c_len > 4:
                if c_len > max_valence:
                    continue
                # find centroid of ngon nodes
                cycle_coords = [ [ self.node[k]["x"],
                                   self.node[k]["y"],
                                   self.node[k]["z"] ] for k in cycle ]
                # compute centroid
                c_x, c_y, c_z = zip(*cycle_coords)
                centroid = [sum(c_x) / c_len,
                            sum(c_y) / c_len,
                            sum(c_z) / c_len]
                # add centroid to mesh
                Mesh.Vertices.Add(*centroid)
                # create triangle with centroid for every pair in cycle
                closed_cycle = cycle[:]
                closed_cycle.append(cycle[0])
                ngon_faces = []
                for a, b in pairwise(closed_cycle):
                    Mesh.Faces.AddFace(node_to_vertex[a],
                                       node_to_vertex[b],
                                       vcount)
                    ngon_faces.append(fcount)
                    fcount += 1
                ngon_cycle = [node_to_vertex[n] for n in cycle]
                RhinoMeshNgon.Create(ngon_cycle, ngon_faces)
                # increment mesh vertex counter
                vcount += 1
            elif c_len < 3:
                continue
            else:
                mesh_cycle = [node_to_vertex[n] for n in cycle]
                Mesh.Faces.AddFace(*mesh_cycle)
                fcount += 1

        # unify the normals of the mesh
        Mesh.UnifyNormals()

        return Mesh

    # CONVERSION TO 2D-KNITTINGPATTERN (PIXEL IMAGE) ---------------------------

    def verify_dual_form(self):
        """
        Verifies this network to have the correct form of a dual as needed for
        representing this network as a 2d knitting pattern.

        Returns
        -------
        bool
            ``True`` on success, ``False`` otherwise.
        """

        # check every single node
        for node in self.nodes_iter():
            # verify if all nodes have the correct keys for attributes
            try:
                start = self.node[node]["start"]
                end = self.node[node]["end"]
                inc = self.node[node]["increase"]
                dec = self.node[node]["decrease"]
                lfn = self.node[node]["leaf"]
                geo = self.node[node]["geo"]
            except KeyError:
                return False

            # get all neighbors
            prd = self.predecessors(node)
            lpr = len(prd)
            # check for nodes with more than two predecessors
            if lpr > 2:
                return False

            suc = self.successors(node)
            lsu = len(suc)
            # check for nodes with more than two successors
            if lsu > 2:
                return False

            nbr = prd + suc
            lnn = len(nbr)
            # check for disconnected nodes
            if not lnn:
                return False

            # maximum connections per node is four
            elif lnn > 4:
                return False

        return True

    def make_pattern_data(self, consolidate=False):
        """
        Topological sort this network to represent it as 2d knitting pattern
        consisting of rows and columns.

        Parameters
        ----------
        consolidate : bool
            If ``True``, will consolidate the final pattern data.
            Defaulst to ``False``.

        Returns
        -------
        pattern_data : :obj:`list` of :obj:`list`
            List (rows) of lists (column values) where every value represents
            a node.

        Raises
        ------
        KnitNetworkTopologyError
            if the network does not satisfy the topology constraints needed for
            this operation and the outcome would be unfeasible or unpredictable.

        Notes
        -----
        Closely resembles the implementation described in Automated Generation
        of Knit Patterns for Non-developable Surfaces* [1]_. Also see *KnitCrete
        - Stay-in-place knitted formworks for complex concrete structures* [2]_.
        """

        # initialize dict for seen nodes and list for storage of rows
        seenrows = {}
        seencols = {}
        rows = []
        cols = []

        # initialize mapping dicts for ordering of rows and columns
        id2row= OrderedDict()
        id2col = OrderedDict()
        node2rowid = OrderedDict()
        node2colid = OrderedDict()

        # BUILD ROWS -----------------------------------------------------------

        # every 'end' node defines the start of a row
        # loop over all 'end' nodes
        for node, data in self.end_nodes:
            # continue if this node has already been visited
            if node in seenrows:
                continue

            # get outgoing 'weft' edges of the current 'end' node
            nodeweft_out = self.node_weft_edges_out(node, data=True)
            nodeweft_in = self.node_weft_edges_in(node, data=True)

            # skip 'end' nodes which have only incoming 'weft' edges
            if nodeweft_in and not nodeweft_out:
                continue

            # if there is more than one outgoing 'weft' edge, we have a problem
            if len(nodeweft_out) > 1:
                errMsg = "More than one outgoing 'weft' edge at " + \
                         "first row node {}!".format(node)
                raise KnitNetworkTopologyError(errMsg)
            # if this is a singular node, it is a separate row.
            elif len(nodeweft_out) == 0 and len(nodeweft_in) == 0:
                # append it as a row to the list of rows
                rows.append([node])
                # set the mapping dictionaries
                row_id = (node, node)
                id2row[row_id] = [node]
                node2rowid.update({node : row_id})
                # set the seen marker and continue to next 'end' node
                seenrows[node] = True
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
                    next_weft = self.node_weft_edges_out(row_nodes[-1])
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
                            seenrows[row_nodes[-1]] = True
                            break
                        # if there are no next 'weft' edges but this is not
                        # an 'end' node, we have a problem
                        else:
                            # see if there are incoming 'weft' edges at the
                            # current node which are not the way we came from
                            next_weft = [nw for nw in self.node_weft_edges_in(
                                         row_nodes[-1], data=True) \
                                         if nw[0] != row_nodes[-2]]

                            # try to reverse them as a failsafe for imperfect
                            # topological dual graphs
                            if len(next_weft) == 1:
                                # flip geometry first, then the graph edge
                                nwe = next_weft[0]
                                nw_attr = nwe[2].copy()
                                nw_attr["geo"].Flip()
                                self.remove_edge(nwe[0], nwe[1])
                                self.add_edge(nwe[1], nwe[0], attr_dict=nw_attr)
                            else:
                                errMsg = "Unexpected end of row. Missing " + \
                                         "'end' attribute at node {}!"
                                errMsg.format(row_nodes[-1])
                                raise KnitNetworkTopologyError(errMsg)

                    # if there is a next node over a 'weft' edge, append to
                    # row and continue
                    if len(next_weft) == 1:
                        row_nodes.append(next_weft[0][1])
                        continue
                # append the completed row to the list of rows
                rows.append(row_nodes)
                # set the mapping dictionaries
                row_id = (row_nodes[0], row_nodes[-1])
                id2row[row_id] = row_nodes
                node2rowid.update({node : row_id for node in row_nodes})
                # finally, set the current node as seen
                seenrows[node] = True

        # BUILD COLUMNS --------------------------------------------------------

        # every 'end' node defines the start of a row
        # loop over all 'end' nodes
        col_sources = [(n, d) for n, d in self.nodes_iter(data=True) \
                       if d["increase"] or d["leaf"] or d["end"]]
        for node, data in col_sources:
            # continue if this node has already been visited
            if node in seencols:
                continue

            # get outgoing 'warp' edges of the current node
            nodewarp_out = self.node_warp_edges_out(node, data=True)
            nodewarp_in = self.node_warp_edges_in(node, data=True)

            # skip nodes which have incoming 'warp' edges
            if nodewarp_in:
                continue

            # if there is more than one outgoing 'warp' edge, we have a problem
            if len(nodewarp_out) > 1:
                errMsg = "More than one outgoing 'warp' edge at " + \
                         "first column node {}!".format(node)
                raise KnitNetworkTopologyError(errMsg)
            # if this is a singular node, it is a separate column (?)
            elif len(nodewarp_out) == 0 and len(nodewarp_in) == 0:
                # errMsg = "Absolutely no 'warp' edges at node {}!".format(node)
                # raise KnitNetworkTopologyError(errMsg)

                # append it as a column to the list of columns
                cols.append([node])
                # set the mapping dictionaries
                col_id = (node, node)
                id2col[col_id] = [node]
                node2colid.update({node : col_id})
                # set the seen marker and continue to next node
                seencols[node] = True
                continue
            # if there is exactly one 'warp' edge, traverse until next node
            elif len(nodewarp_out) == 1:
                # get the connected node to the current node
                connected_node = (nodewarp_out[0][1],
                                  self.node[nodewarp_out[0][1]])
                # define initial column nodes with nodes of the first edge
                col_nodes = [node, connected_node[0]]
                # traverse as long as there is an outgoing next 'warp' edge
                while True:
                    # get 'warp' edges of last node in row nodes
                    next_warp = self.node_warp_edges_out(col_nodes[-1])
                    # if there is more than one connected 'warp' edge, we
                    # have a problem
                    if len(next_warp) > 1:
                        errMsg = "More than one outgoing 'warp' edge at " + \
                                 "col node {}!".format(node)
                        raise KnitNetworkTopologyError(errMsg)
                    # if there are no next 'warp' edges, column is complete
                    elif len(next_warp) == 0:
                        seencols[col_nodes[-1]] = True
                        break
                    # if there is a next node over a 'warp' edge, append to
                    # column and continue
                    elif len(next_warp) == 1:
                        col_nodes.append(next_warp[0][1])
                        continue
                # append the completed column to the list of columns
                cols.append(col_nodes)
                # set the mapping dictionaries
                col_id = (col_nodes[0], col_nodes[-1])
                id2col[col_id] = col_nodes
                node2colid.update({node : col_id for node in col_nodes})
                # finally, set the current node as seen
                seencols[node] = True

        # BUILD ROW MAPPING FOR TOPOLOGICAL SORT -------------------------------

        # initialize mapping for topological sort of rows
        row_map = nx.DiGraph()
        row_ids = id2row.keys()
        # find all targets of all rows by checking all row nodes
        # for targets and getting the corresponding row
        for row_id in row_ids:
            # get row from mapping dict
            row = id2row[row_id]
            # initialize list for storage of targets
            target_ids = []
            # loop over all nodes in the current row
            for node in row:
                # check the node for outgoing 'warp' edges and get its successor
                try:
                    node_suc = self.node_warp_edges_out(node)[0][1]
                except IndexError:
                    continue
                # find the id of the row which contains the 'warp' edge
                # successor node
                target_id = node2rowid[node_suc]
                # if we already found this id before, continue
                if target_id in target_ids:
                    continue
                # if its a new id, append it to the list of found target ids
                target_ids.append(target_id)

            [row_map.add_edge(row_id, tid) for tid in target_ids]

        # BUILD COLUMN MAPPING FOR TOPOLOGICAL SORT ----------------------------

        # initialize mapping for backtracking of columns
        col_map = nx.DiGraph()
        col_ids = id2col.keys()
        # find all targets of all columns by checking all column nodes
        # for targets and getting the corresponding column
        for col_id in col_ids:
            # get column from mapping dict
            col = id2col[col_id]
            # initialize list for storage of targets
            target_ids = []
            # loop over all nodes in the current column
            for node in col:
                # check the node for outgoing 'weft' edges and get its successor
                try:
                    node_suc = self.node_weft_edges_out(node)[0][1]
                except IndexError:
                    continue
                # find the id of the column which contains the 'weft' edge
                # successor node
                target_id = node2colid[node_suc]
                # if we already found this id before, continue
                if target_id in target_ids:
                    continue
                # if its a new id, append it to the list of found target ids
                target_ids.append(target_id)

            [col_map.add_edge(col_id, tid) for tid in target_ids]

        # TOPOLOGICAL SORT OF ROWS ---------------------------------------------

        # own method of topological sort for rows (in utilities)
        # ordered_row_stack = resolve_order_by_backtracking(row_map)

        # use nx topological sort for rows
        try:
            ordered_row_ids = nx.topological_sort_recursive(row_map)
        except nx.NetworkXError as e:
            raise KnitNetworkTopologyError(str(e.message))
        except nx.NetworkXUnfeasible as e:
            raise KnitNetworkTopologyError(str(e.message))

        # get the rows with the backtracking result
        toposort_rows = [id2row[id] for id in ordered_row_ids]
        for i, row in enumerate(toposort_rows):
            for n in row:
                self.node[n]["chain"] = i

        # TOPOLOGICAL SORT OF COLUMNS ------------------------------------------

        # own method of topological sort for columns (in utilities)
        # ordered_column_stack = resolve_order_by_backtracking(col_map)

        # use nx topological sort for columns
        try:
            ordered_column_stack = nx.topological_sort_recursive(col_map)
        except nx.NetworkXError as e:
            raise KnitNetworkTopologyError(str(e.message))
        except nx.NetworkXUnfeasible as e:
            raise KnitNetworkTopologyError(str(e.message))

        # SPREAD OUT BY FILLING WITH -1 FILLER ---------------------------------

        # fill all the rows to minimum row length with placeholder values (-1)
        minrl = max([len(row) for row in rows])
        # loop over all rows and fill until minimum length
        for key in id2row.keys():
            row = id2row[key]
            for j in range(minrl):
                try:
                    node = row[j]
                except IndexError:
                    row.append(-2)
            id2row[key] = row

        for i, col in enumerate(ordered_column_stack):
            # get column nodes
            colnodes = id2col[col]
            # loop over all rows
            for j, row in enumerate(toposort_rows):
                # check the entry at the current column index
                # if this entry is not in colnodes, shift it to the right
                entry = row[i]
                if entry in colnodes:
                    toposort_rows[j].append(-2)
                elif entry not in colnodes:
                    toposort_rows[j].insert(i, -1)

        # trim final topological sorted rows
        trim = toposort_rows[0].index(-2)
        toposort_rows = [btr[:trim] for btr in toposort_rows]

        # TODO: tune consolidation routine to new idea:
        #       if a row is discovered don't touch it until its start is found
        #       then find the previous row to which it connects
        #       'pull' the row to the connection index

        # NOTE: handle increases on the way!

        if consolidate:
            # swap / transpose rows and columns
            spread_columns = list(map(list, zip(*toposort_rows[:])))

            row_has_started = {i : False for i in range(len(toposort_rows))}
            row_has_ended = {i : False for i in range(len(toposort_rows))}

            consolidated_rows = [[] for i in range(len(toposort_rows))]
            toposort_rows = [deque(row) for row in toposort_rows]



            # while len(spread_columns) > 0:
            #     popped_column = spread_columns.popleft()
            #
            #     insert_all_unstarted = False
            #     insert_all_started = False
            #
            #     # for each column, loop over all row indices
            #     for j in range(len(popped_column)):
            #
            #         popped_row_item = toposort_rows[j].popleft()
            #
            #         if popped_row_item != -1:
            #             if self.node[popped_row_item]["start"]:
            #                 row_has_started[j] = True
            #                 insert_all_unstarted = True
            #             elif (not self.node[popped_row_item]["start"] \
            #                   and self.node[popped_row_item]["end"]):
            #                 row_has_ended[j] = True
            #                 insert_all_unstarted = True
            #             elif (self.node[popped_row_item]["start"] \
            #                   and self.node[popped_row_item]["end"]):
            #                 row_has_ended[j] = True
            #                 insert_all_unstarted = True
            #
            #             consolidated_rows[j].append(popped_row_item)
            #
            #         elif popped_row_item == -1:
            #             if row_has_started[j] and not row_has_ended[j]:
            #                 continue
            #             elif row_has_started[j] and row_has_ended[j]:
            #                 consolidated_rows[j].append(-1)
            #             elif not row_has_started[j] and not row_has_ended[j]:
            #                 continue
            #
            #     if insert_all_unstarted:
            #         for k, row in enumerate(consolidated_rows):
            #             if not row_has_started[k]:
            #                 consolidated_rows[k].append(-1)

            return consolidated_rows

        # return all sorted rows
        return toposort_rows

# MAIN -------------------------------------------------------------------------
if __name__ == '__main__':
    pass
