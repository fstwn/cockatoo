"""
Constructs contours for deriving a knitting pattern from a surface.
---
[NOTE] When dealing with surfaces, KnitContours are essentially just isocurves.
So this is a single-node solution for generating an array of equally distributed
isocurves on a surface.
    Inputs:
        Surface: The surface to create the contours on.
                 {item, surface}
        Density: The density (i.e. number) of contour curves.
                 {item, int}
        FlipUV: Flip the U and V parameter space of the surface for isocurve
                extraction.
                Defaults to False.
                {item, bool}
        FlipDir: Flip the curve direction of the contours.
                 Defualts to False.
                 {item, bool}
    Output:
        KnitContours: The KnitContour curves on the surface for initializing a
                      KnitNetwork and deriving a knitting pattern.
                      {item, curve}
    Remarks:
        Author: Max Eschenbach
        License: MIT License
        Version: 200724
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
ghenv.Component.Name = "KnitContoursOnSurface"
ghenv.Component.NickName ="KCOS"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "05 Contouring"

class KnitContoursOnSurface(component):
    
    def RunScript(self, Surface, Density, FlipUV, FlipDir):
        
        if Surface and Density is not None:
            
            # verify density input
            if Density <= 0:
                rml = self.RuntimeMessageLevel.Error
                rMsg = "Density can not be zero or negative!"
                self.AddRuntimeMessage(rml, rMsg)
                return Grasshopper.DataTree[object]()
            
            # reparamterize the surface
            dom = Rhino.Geometry.Interval(0, 1)
            Surface.SetDomain(0, dom)
            Surface.SetDomain(1, dom)
            
            # extract surface isocurves
            contours = []
            for i in range(Density+1):
                # extract isocurves based on parameter input
                if FlipUV:
                    param = 1
                else:
                    param = 0
                
                iso = Surface.IsoCurve(param, i/Density)
                
                if i == 0 and not iso.IsValid:
                    isoval = 0.001
                    while not iso.IsValid:
                        iso = Surface.IsoCurve(param, isoval)
                        isoval += 0.001
                        
                elif i == Density and not iso.IsValid:
                    isoval = 0.999
                    while not iso.IsValid:
                        iso = Surface.IsoCurve(param, isoval)
                        isoval -= 0.001
                
                # append to list of contours
                contours.append(iso)
            
            # also reverse the curve order if uv was flipped
            if FlipUV:
                contours.reverse()
            
            # flip direction of curves based on input param
            if FlipDir:
                [c.Reverse() for c in contours]
        
        else:
            if not Surface:
                rml = self.RuntimeMessageLevel.Warning
                rMsg = "No Surface input!"
                self.AddRuntimeMessage(rml, rMsg)
            if Density == None:
                rml = self.RuntimeMessageLevel.Warning
                rMsg = "No Density input!"
                self.AddRuntimeMessage(rml, rMsg)
            
            return Grasshopper.DataTree[object]()
        
        return contours
