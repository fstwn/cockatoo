"""
Select KnitNetwork Nodes by index.
    Inputs:
        KnitNetwork: The KnitNetwork to select nodes from.
                     {item, KnitNetworkBase}
        NodeIndex: Indices of the Nodes to select
                   {list, int}
        SkipInvalid: If True, invalid indices (indices that have no node) will
                     be silently skipped. Otherwise, None will be inserted into
                     the output for invalid indices.
                     Defaults to False.
                     {item, bool}
    Outputs:
        Nodes: The found nodes as node-2-tuples consisting of (index, data).
               {list, nodes}
        NodePoints: The Point3d geometry of the selected nodes.
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
ghenv.Component.Name = "NodesByIndex"
ghenv.Component.NickName ="NBI"
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

class NodesByIndex(component):
    
    def __init__(self):
        super(NodesByIndex, self).__init__()
        
        self.drawing_nodes = []
    
    def RunScript(self, KnitNetwork, NodeIndex, SkipInvalid=True):
        
        # set defaults and catch None values
        if SkipInvalid == None:
            SkipInvalid = True
        
        # initialize output trees
        Nodes = Grasshopper.DataTree[object]()
        NodePoints = Grasshopper.DataTree[object]()
        
        # filter nodes
        if KnitNetwork and NodeIndex:
            
            # initialize output lists
            Nodes = []
            NodePoints = []
            
            # loop through given indices
            for i in NodeIndex:
                try:
                    selected_node = (i, KnitNetwork.node[i])
                    Nodes.append(selected_node)
                    NodePoints.append(selected_node[1]["geo"])
                except KeyError:
                    if SkipInvalid:
                        errMsg = "Node with index {} does not exist in " + \
                                 "network! It was skipped in the output!"
                        errMsg = errMsg.format(i)
                        rml = self.RuntimeMessageLevel.Remark
                        self.AddRuntimeMessage(rml, errMsg)
                    else:
                        errMsg = "Node with index {} does not exist in " + \
                                 "network! None was inserted into the output!"
                        errMsg = errMsg.format(i)
                        rml = self.RuntimeMessageLevel.Remark
                        self.AddRuntimeMessage(rml, errMsg)
                        Nodes.append(None)
                        NodePoints.append(None)
        if not KnitNetwork:
            errMsg = "No KnitNetwork input!"
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, errMsg)
        if not NodeIndex:
            errMsg = "No NodeIndex input!"
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, errMsg)
        
        return Nodes, NodePoints