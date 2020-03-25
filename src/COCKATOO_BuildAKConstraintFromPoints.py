"""
Build an autoknit constraint (AKConstraint) from a list of points
and a time value.
    Inputs:
        P: The points to build the constraint with. {list, points}
        V: The value to build the constraint with. {item, float}
    Outputs:
        AKConstraint: The constraint as AKConstraint. {list, AKConstraint}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200124
"""
# Python module imports
from __future__ import division

# Rhino imports
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext

# Library imports
from Cockatoo import Autoknit as cak

ghenv.Component.Name = "BuildAKConstraintFromPoints"
ghenv.Component.NickName ="BAKCFP"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "8 Autoknit Pipeline"

class BuildAKConstraintFromPoints(component):
    
    def RunScript(self, P, V):
        # define outputs so they're never empty
        AKConstraint = None
        
        AKConstraint = cak.AKConstraint(-1, P, V, 0)
        
        
        # return outputs if you have them; here I try it for you:
        return (AKConstraint)