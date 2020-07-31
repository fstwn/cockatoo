"""
Creates a graph suitable for visualisation using Gephi from a KnitNetwork.
    Inputs:
        Toggle: {item, boolean}
        KnitNetwork: An initialized KnitNetwork. {item, KnitNetwork}
    Output:
        GephiGraph: A graph prepared for visualisation using Gephi.
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
ghenv.Component.Name = "MakeGephiGraph"
ghenv.Component.NickName ="MGG"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "08 Visualisation"

# LOCAL MODULE IMPORTS
try:
    import cockatoo
except ImportError:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

class MakeGephiGraph(component):
    
    def RunScript(self, Toggle, KN):
        
        if Toggle and KN:
            GephiGraph = KN.prepare_for_gephi()
        else:
            GephiGraph = Grasshopper.DataTree[object]()
        
        # return outputs if you have them; here I try it for you:
        return GephiGraph