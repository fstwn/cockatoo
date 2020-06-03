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
        Version: 200603
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# ADDITIONAL RHINO IMPORTS
from scriptcontext import sticky as st

# LOCAL MODULE IMPORTS
try:
    from cockatoo.utilities import map_values_as_colors
except ImportError:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "RenderKnitContours"
ghenv.Component.NickName ="RKC"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "7 Visualisation"

class RenderKnitContours(component):
    
    def custom_display(self, toggle):
        """
        Make a custom display which is unique to the component and lives in the
        sticky dictionary.
    
        Notes
        -----
        Original code by Anders Holden Deleuran.
        For more info see [1]_.
    
        References
        ----------
        .. [1] customDisplayInSticky.py - gist by Anders Holden Deleuran
               See: https://gist.github.com/AndersDeleuran/09f8af66c29e96bd35440fa8276b0b5a
        """
    
        # Make unique name and custom display
        displayKey = str(self.InstanceGuid) + "___CUSTOMDISPLAY"
        if displayKey not in st:
            st[displayKey] = Rhino.Display.CustomDisplay(True)
    
        # Clear display each time component runs
        st[displayKey].Clear()
    
        # Return the display or get rid of it
        if toggle:
            return st[displayKey]
        else:
            st[displayKey].Dispose()
            del st[displayKey]
            return None
    
    def RunScript(self, Toggle, KnitContours):
        
        # VISUALISATION OF CONTOURS USING CUSTOM DISPLAY -----------------------
        
        if Toggle and KnitContours:
            # make customdisplay
            viz = self.custom_display(True)
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
                    ccols = map_values_as_colors(range(numseg), 0, numseg, 0.0, 0.35)
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
                    ccols = map_values_as_colors(range(numseg), 0, numseg, 0.0, 0.35)
                    for j, seg in enumerate(segs):
                        viz.AddCurve(seg, ccols[j], 3)
        elif Toggle and not KnitContours:
            viz = self.custom_display(False)
            rml = self.RuntimeMessageLevel.Warning
            rMsg = "No KnitContours input!"
            self.AddRuntimeMessage(rml, rMsg)
        else:
            viz = self.custom_display(False)
        
