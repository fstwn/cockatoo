"""
Create the final network topology by using the previosly created and embedded
mapping network to sample the courses with the stitch width. Subsequently, all
final 'weft' and 'warp' edges will be created.
---
[WARNING] The implementation used is research-level code and not optimized. This
can lead to substantial computation time, depending on size of the mesh, stitch
parameters and hardware of the machine!
    Inputs:
        Toggle: Set to true to activate the component.
                {item, boolean}
        KnitNetwork: A KnitNetwork with a previosly created, embedded mapping
                     network.
                     {item, KnitNetwork}
        IncludeEnds: If True, 'end' nodes between adjacent segments in a source
                     chain will be included in the first pass of connecting
                     'warp' edges.
                     Defaults to True.
                     {item, bool}
        Precise: If True, the more precise but slower DistanceTo() function will
                 be used instead of DistanceToSquared().
                 Defaults to False.
                 {item, boolean}
    Output:
        KnitNetwork: The KnitNetwork representing the final knit topology with
                     stitches, increases, decreases and short rows.
                     {item, KnitNetwork}
    Remarks:
        Author: Max Eschenbach
        License: MIT License
        Version: 200705
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
ghenv.Component.Name = "CreateFinalNetworkTopology"
ghenv.Component.NickName ="CFNT"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "06 KnitNetwork"

# LOCAL MODULE IMPORTS
try:
    import cockatoo
except ImportError:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

class CreateFinalNetworkTopology(component):
    
    def RunScript(self, Toggle, KN, StitchWidth, IncludeEnds=True, Precise=False):
        
        if Toggle and KN and StitchWidth:
            KN = cockatoo.KnitNetwork(KN)
            
            # SAMPLING OF SEGMENT CONTOURS -------------------------------------
            
            KN.sample_segment_contours(StitchWidth)
            
            # CREATION OF FINAL WEFT CONNECTIONS -------------------------------
            
            KN.create_final_weft_connections()
            
            # CREATION OF WARP CONNECTIONS -------------------------------------
            
            KN.create_final_warp_connections(max_connections=4,
                                             include_end_nodes=IncludeEnds,
                                             precise=Precise,
                                             verbose=False)
        else:
            if not KN:
                rml = self.RuntimeMessageLevel.Warning
                self.AddRuntimeMessage(rml, "No KnitNetwork input!")
            if not StitchWidth:
                rml = self.RuntimeMessageLevel.Warning
                self.AddRuntimeMessage(rml, "No StitchWidth input!")
            KN = Grasshopper.DataTree[object]()
        
        # return outputs if you have them; here I try it for you:
        return KN