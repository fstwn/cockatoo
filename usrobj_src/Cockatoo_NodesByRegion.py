"""
Select KnitNetwork Nodes by testing for containment within a specified region
curve.
    Inputs:
        KnitNetwork: The KnitNetwork to select nodes from.
                     {item, KnitNetworkBase}
        RegionCurves: Curve for proximity search.
                      {list, point3d}
        UseReference: If True, will use the normal plane at each node of the 
                      networks reference geometry to determine the region 
                      inclusion of the node. Otherwise, will use the
                      RegionPlane. If no reference geometry is set for the
                      network, will also fall back to the RegionPlane.
                      Defaults to False.
                      {item, bool}
        RegionPlane: Plane for region containment query. The UseReference
                     parameter will overwrite this plane if True!
                     Defaults to World XY Plane.
                     {item, plane}
    Outputs:
        NodeIndices: The indices (identifiers) of the found nodes within the
                     network.
                     {list, int}
        Nodes: The found nodes as node-2-tuples consisting of (index, data).
               {list, nodes}
        NodePoints: The Point3d geometry of the selected nodes within the
                    network.
                    {list, point3d}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200615
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "NodesByRegion"
ghenv.Component.NickName ="NBR"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "07 KnitNetwork Editing"

# LOCAL MODULE IMPORTS
try:
    import cockatoo
except ImportError:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

class NodesByRegion(component):
    
    def __init__(self):
        super(NodesByRegion, self).__init__()
        
        self.region_plane = None
    
    def is_point_in_region(self, data_tuple):
        node, region_crvs, nrm = data_tuple
        for j, region in enumerate(region_crvs):
            if nrm:
                plane = Rhino.Geometry.Plane(node[1]["geo"], nrm[node[0]])
            else:
                plane = self.region_plane
            tol = Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance
            pc = region.Contains(node[1]["geo"], plane, tol)
            if not (pc == Rhino.Geometry.PointContainment.Inside \
                    or pc == Rhino.Geometry.PointContainment.Coincident):
                    continue
            return True
        return False
    
    def RunScript(self, KnitNetwork, RegionCurves, UseReference, RegionPlane):
        
        # set defaults
        if UseReference == None:
            UseReference = False
        if RegionPlane != None:
            self.region_plane = RegionPlane
        else:
            self.region_plane = Rhino.Geometry.Plane.WorldXY
        
        # initialize outputs
        NodeIndices = Grasshopper.DataTree[object]()
        Nodes = Grasshopper.DataTree[object]()
        NodePoints = Grasshopper.DataTree[object]()
        
        # filter nodes according to input
        if KnitNetwork and RegionCurves:
            
            # get all the nodes of the network
            network_nodes = KnitNetwork.nodes(data=True)
            
            if UseReference:
                try:
                    reference_geometry = KnitNetwork.graph["reference_geometry"]
                except KeyError:
                    reference_geometry = None
                
                if not reference_geometry:
                    cbp = None
                    nrm = None
                    errMsg = "KnitNetwork has no reference geometry " + \
                             "attached! Fallback to RegionPlane."
                    rml = self.RuntimeMessageLevel.Warning
                    self.AddRuntimeMessage(rml, errMsg)
                elif isinstance(reference_geometry, Rhino.Geometry.Mesh):
                    cbp = {network_nodes[k][0]: reference_geometry.ClosestMeshPoint(
                           network_nodes[k][1]["geo"], 0) for k in range(len(network_nodes))}
                    nrm = {k: reference_geometry.NormalAt(cbp[k]) \
                           for k in cbp.keys()}
                elif isinstance(reference_geometry, Rhino.Geometry.NurbsSurface):
                    cbp = {network_nodes[k][0]: reference_geometry.ClosestPoint(
                           network_nodes[k][1]["geo"], 0) for k in network_nodes}
                    nrm = {k: reference_geometry.NormalAt(cbp[k][0], cbp[k][1]) \
                           for k in cbp.keys()}
            else:
                cbp = None
                nrm = None
            
            # prepare for parallel execution
            data_list = []
            for i, node in enumerate(network_nodes):
                data_tuple = (node, RegionCurves, nrm)
                data_list.append(data_tuple)
            
            # run parallel and collect results
            results = GhPython.ScriptHelpers.Parallel.Run(
                                        self.is_point_in_region,
                                        data_list,
                                        False)
            
            # route results to outputs
            Nodes = [network_nodes[i] for i, val in enumerate(results) if val]
            NodeIndices = [n[0] for n in Nodes]
            NodePoints = [n[1]["geo"] for n in Nodes]
        
        # catch missing inputs
        if not KnitNetwork:
            errMsg = "No KnitNetwork input!"
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, errMsg)
        if not RegionCurves:
            errMsg = "No RegionCurves input!"
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, errMsg)
        
        # return results
        return NodeIndices, Nodes, NodePoints
