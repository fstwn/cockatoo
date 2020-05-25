"""
Attempts to visualise the time flow on KnitContours by rendering them as
gradient coloured curves. Will work with any type of curve, actually.
    Inputs:
        Toggle: If True, curves will be rendered to the viewport. 
                {item, boolean}
        KnitContours: Some KnitContours to visualise (works with any curve). 
                      {list, curve/polyline}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200525
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
                if pl.IsPolyline() and pl.Degree == 1:
                    polypts = []
                    for j, cpt in enumerate(pl.Points):
                        polypts.append(Rhino.Geometry.Point3d(cpt.X, 
                                                              cpt.Y,
                                                              cpt.Z))
                    pl = Rhino.Geometry.Polyline(polypts)
                    segs = [Rhino.Geometry.LineCurve(s) for s in pl.GetSegments()]
                    numseg = len(segs)
                    ccols = mapValuesAsColors(range(numseg), 0, numseg, 0.0, 0.35)
                    for j, seg in enumerate(segs):
                        viz.AddCurve(seg, ccols[j], 3)
                else:
                    abstol = Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance
                    angletol = Rhino.RhinoDoc.ActiveDoc.ModelAngleToleranceRadians
                    minlen = abstol
                    maxlen = 100
                    # make polylinecurve (!)
                    pl = pl.ToPolyline(abstol, angletol, minlen, maxlen)
                    # make polyline
                    pl = pl.ToPolyline()
                    segs = [Rhino.Geometry.LineCurve(s) for s in pl.GetSegments()]
                    numseg = len(segs)
                    ccols = mapValuesAsColors(range(numseg), 0, numseg, 0.0, 0.35)
                    for j, seg in enumerate(segs):
                        viz.AddCurve(seg, ccols[j], 3)
        elif Toggle and not KnitContours:
            viz = customDisplay(self, False)
            rml = self.RuntimeMessageLevel.Warning
            rMsg = "No KnitContours input!"
            self.AddRuntimeMessage(rml, rMsg)
        else:
            viz = customDisplay(self, False)
        
