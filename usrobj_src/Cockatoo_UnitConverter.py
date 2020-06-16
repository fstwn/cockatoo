"""
Converts units specified in millimeters or with a signed string into document units.
    Inputs:
        Value: Signed value. Can end with mm, dm, cm, m. For example 10mm is 10 millimeters. {item, number}
    Outputs:
        ModelUnits: The input number converted to current model units of the Rhino document {item, number}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200615
"""

# PYTHON MODULE IMPORTS
from __future__ import division

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# COMPONENT PROPERTIES
ghenv.Component.Name = "UnitConverter"
ghenv.Component.NickName = "UC"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "10 Utilities"

class UnitConverter(component):
    
    def splitString(self, strToSplit): 
        alpha = "" 
        num = "" 
        special = "" 
        for i in range(len(strToSplit)):
            if (strToSplit[i].isdigit()) or strToSplit[i] == ".": 
                num = num + strToSplit[i] 
            elif((strToSplit[i] >= 'A' and strToSplit[i] <= 'Z') or
                 (strToSplit[i] >= 'a' and strToSplit[i] <= 'z')): 
                alpha += strToSplit[i] 
            else: 
                special += strToSplit[i] 
        
        return alpha, num, special
    
    def RunScript(self, Value):
        # get current Rhino unit system and absolute tolerance setting
        musys = Rhino.RhinoDoc.ActiveDoc.ModelUnitSystem
        abstol = Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance
        
        # set component info message
        self.Message = ("UnitSystem: " + str(musys) + "\n"
                                   "Tolerance: " + str(abstol))
        
        if Value:
            if Value.startswith("1E") \
            or Value.startswith("1e") \
            or Value.startswith("1.0e") \
            or Value.startswith("1.0E"):
                Value = "{:.500f}".format(float(Value))
                Value = Value.rstrip("0")
            
            alpha, num, special = self.splitString(Value)
            if alpha == "" or alpha == "mm":
                insys = Rhino.UnitSystem.Millimeters
            elif alpha == "cm":
                insys = Rhino.UnitSystem.Centimeters
            elif alpha == "dm":
                insys = Rhino.UnitSystem.Decimeters
            elif alpha == "m":
                insys = Rhino.UnitSystem.Meters
            elif alpha == '"' or alpha == "in":
                insys = Rhino.UnitSystem.Inches
            try:
                ModelUnits = float(num) * Rhino.RhinoMath.UnitScale(insys, musys)
            except:
                rml = self.RuntimeMessageLevel.Error
                self.AddRuntimeMessage(rml, "Could not parse signed value.")
                return None
        else:
            ModelUnits = None
        
        # return outputs if you have them; here I try it for you:
        return ModelUnits