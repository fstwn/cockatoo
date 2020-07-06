"""
Set a specific color to nodes selected by indices in the network.
    Inputs:
        KnitNetwork: The KnitNetwork to edit nodes from.
                     {item, KnitNetworkBase}
        NodeIndex: Indices of the Nodes to assign color to.
                   {list, int}
        Color: New color for the specified nodes. This can also be None to reset
               the color of the nodes.
               {item, System.Drawing.Color}
    Outputs:
        KnitNetwork: The network with the new color information.
                     {tree, KnitNetworkBase}
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
ghenv.Component.Name = "SetNodeColor"
ghenv.Component.NickName ="SNC"
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

class SetNodeColor(component):
    
    def __init__(self):
        super(SetNodeColor, self).__init__()
        
        self.drawing_nodes = []
        self.skip_invalid = False
    
    def RunScript(self, KnitNetwork, NodeIndex, Color):
        
        # initialize output so it's never empty
        KN = Grasshopper.DataTree[object]()
        
        # filter nodes according to input
        if KnitNetwork and NodeIndex:
            
            # make copy of the input to avoid messing up the data struture
            if isinstance(KnitNetwork, cockatoo.KnitNetwork):
                KN = cockatoo.KnitNetwork(KnitNetwork)
            elif isinstance(KnitNetwork, cockatoo.KnitMappingNetwork):
                KN = cockatoo.KnitMappingNetwork(KnitNetwork)
            elif isinstance(KnitNetwork, cockatoo.KnitDiNetwork):
                KN = cockatoo.KnitDiNetwork(KnitNetwork)
            
            for i in NodeIndex:
                if KN.has_node(i):
                    if Color != None:
                        KN.node[i]["color"] = (Color.R,
                                               Color.G,
                                               Color.B)
                    else:
                        KN.node[i]["color"] = None
            
            return KN
        
        # catch missing inputs
        if not KnitNetwork:
            errMsg = "No KnitNetwork input!"
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, errMsg)
        if not NodeIndex:
            errMsg = "No NodeIndex input!"
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, errMsg)
