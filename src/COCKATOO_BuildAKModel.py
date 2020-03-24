"""
Load an Autoknit *.cons file and interpret the constraints in it.
    Inputs:
        M: The mesh to build the model with {item, mesh}
        C: The constraints to build the model with as AKConstraints {list, AKConstraint}
    Outputs:
        AKModel: The vertices from the constraint file as tuples {list, AKModel}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200324
"""

from __future__ import division
from string import join

from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext

from cockatoo import autoknit as cak

ghenv.Component.Name = "BuildAKModel"
ghenv.Component.NickName ="BAKM"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "8 Autoknit Pipeline"

class BuildAKModel(component):
    
    def RunScript(self, M, C):
        # define outputs so they're never empty
        AKModel = None
        
        if not M:
            return None
        if not C:
            C = None
        
        for i, c in enumerate(C):
            if type(c) is not cak.AKConstraint:
                raise ValueError("Supplied constraint {i} is not a valid " + \
                                 "AKConstraint!".format(i))
        
        # create model
        AKModel = cak.AKModel(M, C)
        
        # return outputs if you have them; here I try it for you:
        return (AKModel)