"""
Get the segmentation for loop generation and assign segment attributes
to 'weft' edges and vertices.
TODO: Update docstring!
    Inputs:
        Toggle: Set to true to activate {item, boolean}
        KnitMeshNetwork: An initialized KnitMeshNetwork. {item, KnitMeshNetwork}
    Output:
        KnitMeshNetwork: The KnitMeshNetwork with 'weft' connections created. {item, polyline}
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
from mbe.component import addRuntimeWarning

ghenv.Component.Name = "GetWeftEdgeSegmentation"
ghenv.Component.NickName ="GWES"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "6 KnitMeshNetwork"

class GetWeftEdgeSegmentation(component):
    
    def RunScript(self, Toggle, KMN):
        
        if Toggle and KMN:
            # copy the input network to not mess with previous components
            KMN = cockatoo.KnitMeshNetwork(KMN)
            
            # GET SEGMENTATION -------------------------------------------------
            
            KMN.GetWeftEdgeSegmentation()
            
            # CHECK THE RESULTS ------------------------------------------------
            
            for edge in KMN.edges(data=True):
                s = edge[2]["segment"]
                w = edge[2]["weft"]
                if w and not s:
                    vStr = "'weft' edge {} has no segment value!"
                    vStr = vStr.format((edge[0], edge[1]))
                    addRuntimeWarning(self, vStr)
            
            for node in KMN.nodes(data=True):
                e = node[1]["end"]
                s = node[1]["segment"]
                if not s:
                    if not e:
                        vStr = "node {} has no segment value!"
                        vStr = vStr.format(node[0])
                        addRuntimeWarning(self, vStr)
        elif not Toggle and KMN:
            KMN = KMN = cockatoo.KnitMeshNetwork(KMN)
        else:
            KMN = Grasshopper.DataTree[object]()
        
        # return outputs if you have them; here I try it for you:
        return KMN