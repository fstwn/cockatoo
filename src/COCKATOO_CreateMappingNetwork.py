"""
Creates a mapping network from segmented weft edges.
TODO: Update docstring!
    Inputs:
        Toggle: Set to true to activate {item, boolean}
        KnitNetwork: An initialized KnitNetwork. {item, KnitNetwork}
    Output:
        MappingNetwork: The KnitNetwork with 'weft' connections created. {item, polyline}
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

ghenv.Component.Name = "CreateMappingNetwork"
ghenv.Component.NickName ="CMN"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "6 KnitNetwork"

class CreateMappingNetwork(component):
    
    def RunScript(self, Toggle, KN):
        
        if Toggle and KN:
            MappingNetwork = KN.CreateMappingNetwork()
        else:
            MappingNetwork = Grasshopper.DataTree[object]()
        
        # return outputs if you have them; here I try it for you:
        return MappingNetwork