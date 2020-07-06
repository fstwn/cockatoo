"""
Attempts to visualise the time flow on KnitContours by rendering them as
gradient coloured curves. Will work with any type of curve, actually.
    Inputs:
        KnitContours: Some KnitContours to visualise (works with any curve). 
                      {list, curve/polyline}
        Thickness: The thickness of the rendered curves.
                   Defaults to 3.
                   {item, int}
    Remarks:
        Author: Max Eschenbach
        License: MIT License
        Version: 200705
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

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "RenderKnitContours"
ghenv.Component.NickName ="RKC"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "08 Visualisation"

# LOCAL MODULE IMPORTS
try:
    from cockatoo.utilities import map_values_as_colors
except ImportError:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

class RenderKnitContours(component):
    
    def __init__(self):
        super(RenderKnitContours, self).__init__()
        
        self.drawing_curves = []
    
    def get_ClippingBox(self):
        return Rhino.Geometry.BoundingBox()
    
    def DrawViewportWires(self, args):
        try:
            # get the display from the arguments
            display = args.Display
            
            for curve in self.drawing_curves:
                display.DrawCurve(curve[0], curve[1], curve[2])
            
        except Exception, e:
            System.Windows.Forms.MessageBox.Show(str(e),
                                                 "Error while drawing preview!")
    
    def RunScript(self, KnitContours, Thickness):
        
        # VISUALISATION OF CONTOURS USING CUSTOM DISPLAY -----------------------
        
        # set default thickness
        if Thickness == None:
            Thickness = 3
        
        if KnitContours:
            
            drawing_curves = []
            
            # make customdisplay
            for i, pl in enumerate(KnitContours):
                if pl.IsPolyline() and pl.Degree == 1:
                    polypts = []
                    for j, cpt in enumerate(pl.Points):
                        polypts.append(Rhino.Geometry.Point3d(cpt.X, 
                                                              cpt.Y,
                                                              cpt.Z))
                    pl = Rhino.Geometry.Polyline(polypts)
                    segs = [Rhino.Geometry.LineCurve(s) \
                            for s in pl.GetSegments()]
                    numseg = len(segs)
                    ccols = map_values_as_colors(range(numseg),
                                                 0,
                                                 numseg,
                                                 0.0,
                                                 0.35)
                    for j, seg in enumerate(segs):
                        drawing_curves.append((seg, ccols[j], Thickness))
                else:
                    abstol = Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance
                    angletol = Rhino.RhinoDoc.ActiveDoc.ModelAngleToleranceRadians
                    minlen = abstol
                    maxlen = 100
                    # make polylinecurve (!)
                    pl = pl.ToPolyline(abstol, angletol, minlen, maxlen)
                    # make polyline
                    pl = pl.ToPolyline()
                    segs = [Rhino.Geometry.LineCurve(s) \
                            for s in pl.GetSegments()]
                    numseg = len(segs)
                    ccols = map_values_as_colors(range(numseg),
                                                 0,
                                                 numseg,
                                                 0.0,
                                                 0.35)
                    for j, seg in enumerate(segs):
                        drawing_curves.append((seg, ccols[j], Thickness))
            
            # set attributes for drawing routine
            self.drawing_curves = drawing_curves
            
        elif not KnitContours:
            self.drawing_curves = []
            rml = self.RuntimeMessageLevel.Warning
            rMsg = "No KnitContours input!"
            self.AddRuntimeMessage(rml, rMsg)
        else:
            self.drawing_curves = []
