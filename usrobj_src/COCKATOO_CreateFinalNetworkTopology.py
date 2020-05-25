"""
Create the final network topology by using the previosly created and embedded
mapping network to sample the courses with the stitch width. Subsequently, all
final 'weft' and 'warp' edges will be created.
    Inputs:
        Toggle: Set to true to activate the component. {item, boolean}
        KnitNetwork: A KnitNetwork with a previosly created, embedded mapping
                     network. {item, KnitNetwork}
    Output:
        KnitNetwork: The KnitNetwork representing the final knit topology with
                     stitches, increases, decreases and short rows.
                     {item, KnitNetwork}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200525
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