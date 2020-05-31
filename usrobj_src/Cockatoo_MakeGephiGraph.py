"""
Get the segmentation for loop generation and assign segment attributes
to 'weft' edges and vertices.
TODO: Update docstring!
    Inputs:
        Toggle: {item, boolean}
        KnitNetwork: An initialized KnitNetwork. {item, KnitNetwork}
    Output:
        RenderGraph: The KnitNetwork with 'weft' connections created. {item, polyline}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200531
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division

# GPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# LOCAL MODULE IMPORTS
import Cockatoo

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "MakeGephiGraph"
ghenv.Component.NickName ="MGG"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "7 Visualisation"

class MakeGephiGraph(component):
    
    def RunScript(self, Toggle, KN):
        
        if Toggle and KN:
            GephiGraph = KN.MakeGephiGraph()
        else:
            GephiGraph = Grasshopper.DataTree[object]()
        
        # return outputs if you have them; here I try it for you:
        return GephiGraph