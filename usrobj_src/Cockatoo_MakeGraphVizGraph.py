"""
Creates a graph suitable for visualisation using GraphViz from a KnitNetwork.
    Inputs:
        Toggle: {item, boolean}
        KnitNetwork: An initialized KnitNetwork. {item, KnitNetwork}
    Output:
        GraphVizGraph: A graph prepared for visualisation using GraphViz.
                       {item, polyline}
    Remarks:
        Author: Max Eschenbach
        License: MIT License
        Version: 200731
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division

# GPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "MakeGraphVizGraph"
ghenv.Component.NickName ="MGVG"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "08 Visualisation"

# LOCAL MODULE IMPORTS
try:
    import cockatoo
    import networkx as nx
except ImportError:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

class MakeRenderGraph(component):
    
    def RunScript(self, Toggle, KN):
        
        if Toggle and KN:
            GraphVizGraph = KN.prepare_for_graphviz()
        else:
            GraphVizGraph = Grasshopper.DataTree[object]()
        
        # return outputs if you have them; here I try it for you:
        return GraphVizGraph