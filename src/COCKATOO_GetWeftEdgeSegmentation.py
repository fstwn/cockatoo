"""
Get the segmentation for loop generation and assign segment attributes
to 'weft' edges and vertices.
TODO: Update docstring!
    Inputs:
        Toggle: Set to true to activate {item, boolean}
        KnitNetwork: An initialized KnitNetwork. {item, KnitNetwork}
    Output:
        KnitNetwork: The KnitNetwork with 'weft' connections created. {item, polyline}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200325
"""

# GPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# CUSTOM MODULE IMPORTS
import Cockatoo
from mbe.component import addRuntimeWarning

ghenv.Component.Name = "GetWeftEdgeSegmentation"
ghenv.Component.NickName ="GWES"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "6 KnitNetwork"

class GetWeftEdgeSegmentation(component):
    
    def RunScript(self, Toggle, KN):
        
        if Toggle and KN:
            # copy the input network to not mess with previous components
            KN = Cockatoo.KnitNetwork(KN)
            
            # GET SEGMENTATION -------------------------------------------------
            
            KN.GetWeftEdgeSegmentation()
            
            # CHECK THE RESULTS ------------------------------------------------
            
            for edge in KN.edges(data=True):
                s = edge[2]["segment"]
                w = edge[2]["weft"]
                if w and not s:
                    vStr = "'weft' edge {} has no segment value!"
                    vStr = vStr.format((edge[0], edge[1]))
                    addRuntimeWarning(self, vStr)
            
            for node in KN.nodes(data=True):
                e = node[1]["end"]
                s = node[1]["segment"]
                if not s:
                    if not e:
                        vStr = "node {} has no segment value!"
                        vStr = vStr.format(node[0])
                        addRuntimeWarning(self, vStr)
        elif not Toggle and KN:
            return KN
        else:
            return Grasshopper.DataTree[object]()
        
        # return outputs if you have them; here I try it for you:
        return KN