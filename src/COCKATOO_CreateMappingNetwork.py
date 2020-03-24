"""
Creates a mapping network from segmented weft edges.
TODO: Update docstring!
    Inputs:
        Toggle: Set to true to activate {item, boolean}
        KnitMeshNetwork: An initialized KnitMeshNetwork. {item, KnitMeshNetwork}
    Output:
        MappingNetwork: The KnitMeshNetwork with 'weft' connections created. {item, polyline}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200324
"""

# GPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# CUSTOM MODULE IMPORTS
import cockatoo

ghenv.Component.Name = "CreateMappingNetwork"
ghenv.Component.NickName ="CMN"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "6 KnitMeshNetwork"

class CreateMappingNetwork(component):
    
    def RunScript(self, Toggle, KMN):
        
        if Toggle and KMN:
            MappingNetwork = KMN.CreateMappingNetwork()
        else:
            MappingNetwork = Grasshopper.DataTree[object]()
        
        # return outputs if you have them; here I try it for you:
        return MappingNetwork