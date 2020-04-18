"""Visualises KnitContours
TODO: Update docstring, implement curve behaviour
    Inputs:
        Toggle: {item, boolean}
        KnitContours:{item, curve/polyline}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200418
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
from mbe.helpers import mapValuesAsColors
from mbe.component import customDisplay

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "RenderKnitContours"
ghenv.Component.NickName ="RKC"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "7 Visualisation"

class RenderKnitContours(component):
    
    def RunScript(self, Toggle, KnitContours):
        
        # VISUALISATION OF CONTOURS USING CUSTOM DISPLAY -----------------------
        
        if Toggle and KnitContours:
            # make customdisplay
            viz = customDisplay(self, True)
            for i, pl in enumerate(KnitContours):
                segs = [Rhino.Geometry.LineCurve(s) for s in pl.GetSegments()]
                numseg = len(segs)
                ccols = mapValuesAsColors(range(numseg), 0, numseg, 0.0, 0.35)
                for j, seg in enumerate(segs):
                    viz.AddCurve(seg, ccols[j], 3)
        else:
            viz = customDisplay(self, False)
        
