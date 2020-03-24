"""
Get the segmentation for loop generation and assign segment attributes
to 'weft' edges and vertices.
TODO: Update docstring!
    Inputs:
        Toggle: {item, boolean}
        KnitMeshNetwork: An initialized KnitMeshNetwork. {item, KnitMeshNetwork}
    Output:
        RenderGraph: The KnitMeshNetwork with 'weft' connections created. {item, polyline}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200324
"""

# PYTHON LIBRARY IMPORTS
from __future__ import division

# GPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# CUSTOM MODULE IMPORTS
import cockatoo

ghenv.Component.Name = "MakeRenderGraph"
ghenv.Component.NickName ="MRG"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "7 Visualisation"

class MakeRenderGraph(component):
    
    def RunScript(self, Toggle, KMN):
        
        if Toggle and KMN:
            RenderGraph = cockatoo.KnitMeshNetwork(KMN).ToRenderGraph()
        else:
            RenderGraph = Grasshopper.DataTree[object]()
        
        # return outputs if you have them; here I try it for you:
        return RenderGraph