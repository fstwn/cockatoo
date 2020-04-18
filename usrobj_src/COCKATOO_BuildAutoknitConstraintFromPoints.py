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
from Cockatoo import Autoknit as cak

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "BuildAutoknitConstraintFromPoints"
ghenv.Component.NickName ="BACFP"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "8 Autoknit Pipeline"

class BuildAutoknitConstraintFromPoints(component):
    
    def RunScript(self, P, V):
        # define outputs so they're never empty
        AKConstraint = None
        
        AKConstraint = cak.Constraint(-1, P, V, 0)
        
        
        # return outputs if you have them; here I try it for you:
        return (AKConstraint)