"""
Saves a mesh as an *.obj file on trigger.
    Inputs:
        Save: The File Path of the obj file {item, boolean}
        M: The mesh(es) to save to an *.obj file {list, mesh}
        FP: The filepath to save the file. {item, str}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200414
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# LOCAL MODULE IMPORTS
from mbe.io import saveOBJ

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "SaveMeshAsOBJ"
ghenv.Component.NickName ="SMAO"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "9 Utilities"

class SaveMeshAsOBJ(component):
    
    def RunScript(self, Save, Mesh, FilePath):
        if Save:
            for m in Mesh:
                if type(m) is Rhino.Geometry.Mesh:
                    saveOBJ(m, FilePath)
        
        # return outputs if you have them; here I try it for you:
        return 
