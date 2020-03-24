"""
Load a model from an *.obj file and create a Mesh out of it.
    Inputs:
        FP: The File Path of the obj file {item, str}
    Outputs:
        M: The freshly created Rhino mesh {item, mesh}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200324
"""
from __future__ import division

from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

from mbe.io import loadOBJ, escapeFilePath

ghenv.Component.Name = "LoadOBJAsMesh"
ghenv.Component.NickName ="LOAM"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "9 Utilities"

class LoadOBJ(component):
    
    def RunScript(self, FP):
        # define output so it's never empty
        Model = None
        
        Model = loadOBJ(escapeFilePath(FP))
        
        # return outputs if you have them; here I try it for you:
        return Model
