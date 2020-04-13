"""
Create the final network topology by sampling the previously generated courses
with the stitch width and creating all final 'weft' and 'warp' edges using a
previously generated mapping network.
TODO: Update docstring!
    Inputs:
        Toggle: Set to true to activate {item, boolean}
        KnitNetwork: An initialized KnitNetwork. {item, KnitNetwork}
    Output:
        MappingNetwork: The KnitNetwork with 'weft' connections created. {item, polyline}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200413
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
import Cockatoo

ghenv.Component.Name = "CreateFinalNetworkTopology"
ghenv.Component.NickName ="CFNT"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "6 KnitNetwork"

class CreateFinalNetworkTopology(component):
    
    def RunScript(self, Toggle, KN, StitchWidth, IncludeEnds=True):
        
        if Toggle and KN and StitchWidth:
            KN = Cockatoo.KnitNetwork(KN)
            
            # SAMPLING OF SEGMENT CONTOURS -------------------------------------
            
            KN.SampleSegmentContours(StitchWidth)
            
            # CREATION OF FINAL WEFT CONNECTIONS -------------------------------
            
            KN.CreateFinalWeftConnections()
            
            # CREATION OF WARP CONNECTIONS -------------------------------------
            
            KN.CreateFinalWarpConnections(max_connections=4,
                                          include_end_nodes=IncludeEnds,
                                          precise=False,
                                          verbose=False)
            
        else:
            KN = Grasshopper.DataTree[object]()
        
        # return outputs if you have them; here I try it for you:
        return KN