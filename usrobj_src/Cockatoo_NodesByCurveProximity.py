"""
Select KnitNetwork Nodes by proximity by selecting all nodes that are closer
than the specified Tolerance to the given SamplePoints.
    Inputs:
        KnitNetwork: The KnitNetwork to select nodes from.
                     {item, KnitNetworkBase}
        SampleCurves: Curve for proximity search.
                      {list, point3d}
        Tolerance: All nodes closer to the sample curves than this value will
                   be selected by the component.
                   Defaults to [0.01] units.
                   {item, float}
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
        License: MIT License
        Version: 200705
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
ghenv.Component.Name = "NodesByCurveProximity"
ghenv.Component.NickName ="NBCP"
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

class NodesByCurveProximity(component):
    
    def __init__(self):
        super(NodesByCurveProximity, self).__init__()
        
        self.drawing_nodes = []
        self.skip_invalid = False
    
    def is_point_within_tolerance_to_crv(self, data_tuple):
        node, sample_crvs, tol = data_tuple
        for j, samplecrv in enumerate(sample_crvs):
            if samplecrv == None:
                continue
            curve_cp = samplecrv.ClosestPoint(node[1]["geo"], tol)
            if curve_cp[0]:
                return True
        return False
    
    def RunScript(self, KnitNetwork, SampleCurves, Tolerance=0.01):
        
        # set defaults and catch None values
        if Tolerance == None:
            Tolerance = 0.01
        
        # initialize outputs
        NodeIndices = Grasshopper.DataTree[object]()
        Nodes = Grasshopper.DataTree[object]()
        NodePoints = Grasshopper.DataTree[object]()
        
        # filter nodes according to input
        if KnitNetwork and SampleCurves:
            
            # get all the nodes of the network
            network_nodes = KnitNetwork.nodes(data=True)
            
            data_list = []
            for i, node in enumerate(network_nodes):
                data_tuple = (node, SampleCurves, Tolerance)
                data_list.append(data_tuple)
            
            results = GhPython.ScriptHelpers.Parallel.Run(
                                self.is_point_within_tolerance_to_crv,
                                data_list,
                                False)
            
            Nodes = [network_nodes[i] for i, val in enumerate(results) if val]
            NodeIndices = [n[0] for n in Nodes]
            NodePoints = [n[1]["geo"] for n in Nodes]
        
        # catch missing inputs
        if not KnitNetwork:
            errMsg = "No KnitNetwork input!"
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, errMsg)
        if not SampleCurves:
            errMsg = "No SampleCurves input!"
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, errMsg)
        
        # return results
        return NodeIndices, Nodes, NodePoints
