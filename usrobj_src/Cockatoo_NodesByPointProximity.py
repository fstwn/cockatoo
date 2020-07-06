"""
Select KnitNetwork Nodes by proximity by selecting all nodes that are closer
than the specified Tolerance to the given SamplePoints.
    Inputs:
        KnitNetwork: The KnitNetwork to select nodes from.
                     {item, KnitNetworkBase}
        SamplePoint: Point to sample for proximity search.
                     {list, point3d}
        Tolerance: All nodes closer to the samplepoints than this value will
                   be selected by the component.
                   Defaults to [0.01] units.
                   {item, float}
        Precise: If True, the more precise but slower DistanceTo() function will
                 be used instead of DistanceToSquared().
                 Defaults to False.
                 {item, bool}
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
from collections import OrderedDict

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "NodesByPointProximity"
ghenv.Component.NickName ="NBPP"
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

class NodesByPointProximity(component):
    
    def __init__(self):
        super(NodesByPointProximity, self).__init__()
        
        self.drawing_nodes = []
        self.skip_invalid = False
    
    def compare_points(self, data_tuple):
        node, samplepoints, tol = data_tuple
        for j, samplept in enumerate(samplepoints):
            if samplept == None:
                continue
            if not node[1]["geo"] == samplept:
                dist = samplept.DistanceTo(node[1]["geo"])
                if dist < tol:
                    return True
                continue
            return True
        return False
    
    def compare_points_squared(self, data_tuple):
        node, samplepoints, tol = data_tuple
        for j, samplept in enumerate(samplepoints):
            if samplept == None:
                continue
            if not node[1]["geo"] == samplept:
                dist = samplept.DistanceToSquared(node[1]["geo"])
                if dist < tol ** 2:
                    return True
                continue
            return True
        return False
    
    def RunScript(self, KnitNetwork, SamplePoints, Tolerance=0.01, Precise=False):
        
        # set defaults and catch None values
        if Tolerance == None:
            Tolerance = 0.01
        if Precise == None:
            Precise = False
        
        # initialize outputs
        NodeIndices = Grasshopper.DataTree[object]()
        Nodes = Grasshopper.DataTree[object]()
        NodePoints = Grasshopper.DataTree[object]()
        
        # filter nodes according to input
        if KnitNetwork and SamplePoints:
            
            # get all the nodes of the network
            network_nodes = KnitNetwork.nodes(data=True)
            
            # initialize list of data for parallel computation
            data_list = []
            
            for i, node in enumerate(network_nodes):
                data_tuple = (node, SamplePoints, Tolerance)
                data_list.append(data_tuple)
            
            # on precise option
            if Precise:
                results = list(GhPython.ScriptHelpers.Parallel.Run(
                                                self.compare_points,
                                                data_list,
                                                False))
            # standard case
            else:
                results = list(GhPython.ScriptHelpers.Parallel.Run(
                                                self.compare_points_squared,
                                                data_list,
                                                False))
            
            # collect results
            Nodes = [network_nodes[i] for i, val in enumerate(results) if val]
            NodeIndices = [n[0] for n in Nodes]
            NodePoints = [n[1]["geo"] for n in Nodes]
            
        # catch missing inputs
        if not KnitNetwork:
            errMsg = "No KnitNetwork input!"
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, errMsg)
        if not SamplePoints:
            errMsg = "No SamplePoints input!"
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, errMsg)
        
        # return results
        return NodeIndices, Nodes, NodePoints
