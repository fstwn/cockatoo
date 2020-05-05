"""
Directional KnitNetwork for finding faces (cycles) of a KnitNetwork.

Author: Max Eschenbach
License: Apache License 2.0
Version: 200503
"""

# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from collections import deque
import math
from operator import itemgetter

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from Cockatoo.Environment import IsRhinoInside
from Cockatoo.KnitNetworkBase import KnitNetworkBase
from Cockatoo.Utilities import is_ccw_xy
from Cockatoo.Utilities import pairwise
from Cockatoo.Utilities import TweenPlanes

# THIRD PARTY MODULE IMPORTS ---------------------------------------------------
import networkx as nx

# RHINO IMPORTS ----------------------------------------------------------------
if IsRhinoInside():
    import rhinoinside
    rhinoinside.load()
    from Rhino.Geometry import Mesh as RhinoMesh
    from Rhino.Geometry import NurbsSurface as RhinoNurbsSurface
    from Rhino.Geometry import Plane as RhinoPlane
    from Rhino.Geometry import Vector3d as RhinoVector3d
else:
    from Rhino.Geometry import Mesh as RhinoMesh
    from Rhino.Geometry import NurbsSurface as RhinoNurbsSurface
    from Rhino.Geometry import Plane as RhinoPlane
    from Rhino.Geometry import Vector3d as RhinoVector3d

# AUTHORSHIP -------------------------------------------------------------------
__author__ = """Max Eschenbach (post@maxeschenbach.com)"""

# ALL DICTIONARY ---------------------------------------------------------------
__all__ = [
    "KnitDiNetwork"
]

# ACTUAL CLASS -----------------------------------------------------------------
class KnitDiNetwork(nx.DiGraph, KnitNetworkBase):
    """
    Class for representing a mapping network that facilitates the automatic
    generation of knitting patterns based on Rhino geometry.
    This is intended only to be instanced by a fully segmented instance of
    KnitNetwork.
    """

    # INITIALIZATION -----------------------------------------------------------

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

        # also copy the MappingNetwork attribute if it is already available
        if data and isinstance(data, KnitDiNetwork) and data.MappingNetwork:
            self.MappingNetwork = data.MappingNetwork
        else:
            self.MappingNetwork = None

        # also copy or initialize the halfedge dict for finding faces
        if data and isinstance(data, KnitDiNetwork) and data.halfedge:
            self.halfedge = data.halfedge
        else:
            self.halfedge = {}

    # TEXTUAL REPRESENTATION OF NETWORK ----------------------------------------

    def ToString(self):
        """
        Return a textual description of the network.
        """

        name = "KnitDiNetwork"
        nn = len(self.nodes())
        ce = len(self.ContourEdges)
        wee = len(self.WeftEdges)
        wae = len(self.WarpEdges)
        data = ("({} Nodes, {} Segment Contours, {} Weft, {} Warp)")
        data = data.format(nn, ce, wee, wae)
        return name + data

    # FIND FACES (CYCLES) OF NETWORK -------------------------------------------

    def _sort_node_neighbors(self, key, nbrs, xyz, geo, cbp, nrm, mode=-1, ccw=True):
        """
        Sort the neighbors of a network node.

        Notes
        -----
        Based on an implementation inside the COMPAS framework.
        For more info see [1]_.

        References
        ----------
        .. [1] Van Mele, Tom et al. *COMPAS: A framework for computational research in architecture and structures*.
               See: https://github.com/compas-dev/compas/blob/e313502995b0dd86d460f86e622cafc0e29d1b75/src/compas/datastructures/network/duality.py#L132
        """

        # if there is only one neighbor we don't need to sort anything
        if len(nbrs) == 1:
            return nbrs

        # initialize the ordered list of neighbors with the first node
        ordered_nbrs = nbrs[0:1]

        # retrieve coordinates for current node
        a = xyz[key]

        # compute local orientation if geometrybase data is present
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
            tweenplane = TweenPlanes(localplane, fitplane, 0.5)
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
        For more info see [1]_.

        References
        ----------
        .. [1] Van Mele, Tom et al. *COMPAS: A framework for computational research in architecture and structures*.
               See: https://github.com/compas-dev/compas/blob/e313502995b0dd86d460f86e622cafc0e29d1b75/src/compas/datastructures/network/duality.py#L121
        """

        # initialize sorted neighbors dict
        sorted_neighbors = {}

        # get dictionary of all coordinates by node index
        xyz = {k: (d["x"], d["y"], d["z"]) for k, d in self.nodes_iter(True)}
        geo = {k: d["geo"] for k, d in self.nodes_iter(True)}

        # compute local orientation data when geometry base is present
        try:
            geometrybase = self.graph["geometrybase"]
        except KeyError:
            geometrybase = None

        if not geometrybase:
            cbp = None
            nrm = None
        elif isinstance(geometrybase, RhinoMesh):
            cbp = {k: geometrybase.ClosestMeshPoint(geo[k], 0) \
                   for k in self.nodes_iter()}
            nrm = {k: geometrybase.NormalAt(cbp[k]) \
                   for k in self.nodes_iter()}
        elif isinstance(geometrybase, RhinoNurbsSurface):
            cbp = {k: geometrybase.ClosestPoint(geo[k])[1:] \
                   for k in self.nodes_iter()}
            nrm = {k: geometrybase.NormalAt(cbp[k][0], cbp[k][1]) \
                   for k in self.nodes_iter()}

        # loop over all nodes in network
        for key in self.nodes_iter():
            nbrs = self[key].keys()
            sorted_neighbors[key] = self._sort_node_neighbors(key, nbrs, xyz, geo, cbp, nrm, mode=mode, ccw=ccw)

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
        For more info see [1]_.

        References
        ----------
        .. [1] Van Mele, Tom et al. *COMPAS: A framework for computational research in architecture and structures*.
               See: https://github.com/compas-dev/compas/blob/e313502995b0dd86d460f86e622cafc0e29d1b75/src/compas/datastructures/network/duality.py#L103
        """

        # get all node neighbors
        nbrs = self[key].keys()

        # if there is only one neighbor, we have already found our candidate
        if len(nbrs) == 1:
            return nbrs[0]

        ab = [-1.0, -1.0, 0.0]
        rhino_ab = RhinoVector3d(*ab)
        a = self.NodeCoordinates(key)
        b = [a[0] + ab[0], a[1] + ab[1], 0]

        angles = []
        for nbr in nbrs:
            c = self.NodeCoordinates(nbr)
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
        u : int
            Index of the start node of the origin edge for the cycle.

        v : int
            Index of the end node of the origin edge for the cycle.

        Notes
        -----
        Based on an implementation inside the COMPAS framework.
        For more info see [1]_.

        References
        ----------
        .. [1] Van Mele, Tom et al. *COMPAS: A framework for computational research in architecture and structures*.
               See: https://github.com/compas-dev/compas/blob/09153de6718fb3d49a4650b89d2fe91ea4a9fd4a/src/compas/datastructures/network/duality.py#L161
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

    def FindCycles(self, mode=-1):
        """
        Finds the cycles (faces) of this network by utilizing a wall-follower
        mechanism.

        Parameters
        ----------
        mode : int
            Determines how the neighbors of each node are sorted when finding
            cycles for the network.
            -1 equals to using the world XY plane (default)
             0 equals to using a plane normal to the origin nodes closest
               point on the geometrybase
             1 equals to using a plane normal to the average of the origin
               and neighbor nodes' closest points on the geometrybase
             2 equals to using an average plane between a plane fit to the
               origin and its neighbor nodes and a plane normal to the origin
               nodes closest point on the geometrybase
            Defaults to -1

        Warning
        -------
        Modes other than -1 (default) are only possible if this network has an
        underlying geometrybase in form of a Mesh or NurbsSurface. The
        geometrybase should be assigned when initializing the network by
        assigning the geometry to the "geometrybase" attribute of the network.

        Notes
        -----
        Based on an implementation inside the COMPAS framework.
        For more info see [1]_.

        References
        ----------
        .. [1] Van Mele, Tom et al. *COMPAS: A framework for computational research in architecture and structures*.
               See: https://github.com/compas-dev/compas/blob/09153de6718fb3d49a4650b89d2fe91ea4a9fd4a/src/compas/datastructures/network/duality.py#L20
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
        # TODO: implement search from leaf nodes first - ?
        u = sorted(self.nodes_iter(data=True), key=lambda n: (n[1]["y"], n[1]["x"]))[0][0]

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

    def CreateMesh(self, mode=-1, ngons=False):
        """
        Constructs a mesh from this network by finding cycles and using them as
        mesh faces.

        Parameters
        ----------
        mode : int
            Determines how the neighbors of each node are sorted when finding
            cycles for the network.
            -1 equals to using the world XY plane (default)
             0 equals to using a plane normal to the origin nodes closest
               point on the geometrybase
             1 equals to using a plane normal to the average of the origin
               and neighbor nodes' closest points on the geometrybase
             2 equals to using an average plane between a plane fit to the
               origin and its neighbor nodes and a plane normal to the origin
               nodes closest point on the geometrybase
            Defaults to -1

        ngons : bool
            If True, n-gon faces (more than 4 edges) are allowed, otherwise
            their cycles are treated as invalid and will be ignored.
            Defaults to False.

        Warning
        -------
        Modes other than -1 (default) are only possible if this network has an
        underlying geometrybase in form of a Mesh or NurbsSurface. The
        geometrybase should be assigned when initializing the network by
        assigning the geometry to the "geometrybase" attribute of the network.
        """

        # get cycles dict of this network
        cycles = self.FindCycles(mode=mode)

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
        for ckey in cycles.keys():
            cycle = cycles[ckey]
            if len(cycle) > 4 and not ngons:
                continue
            elif len(cycle) < 3:
                continue
            else:
                mesh_cycle = [node_to_vertex[n] for n in cycle]
                Mesh.Faces.AddFace(*mesh_cycle)

        # unify the normals of the mesh
        Mesh.UnifyNormals()

        return Mesh
