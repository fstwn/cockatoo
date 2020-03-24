"""
Load an Autoknit *.cons file and interpret the constraints in it.
    Inputs:
        FP: The File Path of the constraint file {item, str}
    Outputs:
        V: The vertices from the constraint file as tuples {list, tuple}
        P: The vertices from the constraint file as points {list, point}
        C: The constraints from the constraint file as tuples {list, tuple}
        AKC: The constraints from the constraint file as AKConstraint objects {list, AKSavedConstraint}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200324
"""

from __future__ import division
from string import join
import importlib

from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext

from mbe.helpers import escapeFilePath
from cockatoo.autoknit import AKFileIO, AKStoredConstraint

ghenv.Component.Name = "LoadAKConstraintFile"
ghenv.Component.NickName ="LAKCF"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "8 Autoknit Pipeline"

class LoadAKConstraintFile(component):
    
    def RunScript(self, FP):
        # define outputs so they're never empty
        V = []
        P = []
        C = []
        
        # if theres no filepath, don't even try ;-)
        if FP:
            filepath = escapeFilePath(FP)
        else:
            rml = self.RuntimeMessageLevel.Warning
            msg = "No File Path specified!"
            self.AddRuntimeMessage(rml, msg)
            return None
        
        # give some feedback to the user
        if len(filepath) > 100:
            end = join(str(filepath).split("\\\\")[-7:], "/")
            fn = ".../" + end
        else:
            fn = join(str(filepath).split("\\\\"), "/")
        rml = self.RuntimeMessageLevel.Remark
        msg = "Reading from file '{}'".format(fn)
        self.AddRuntimeMessage(rml, msg)
        
        # load the constraints
        result = AKFileIO.LoadConstraints(filepath)
        if result[0] == False:
            rml = self.RuntimeMessageLevel.Error
            msg = "Error Loading constraints! " + str(result[1])
            self.AddRuntimeMessage(rml, msg)
            return None
        else:
            R, V, C = result
            P = [Rhino.Geometry.Point3d(v[0], v[1], v[2]) for v in V]
        
        AKSC = [AKStoredConstraint(c[0], c[1], c[2]) for c in C]
        
        AKC = AKFileIO.InterpretStoredConstraints(V, AKSC)
        
        # return outputs if you have them; here I try it for you:
        return (V, P, C, AKC)