"""
Used to create a manual KnitConstraint by supplying curves for start, end, left
boundary and right boundary. Together, these curves must form a closed loop!
    Inputs:
        StartCourse: The curve that defines the start of the knit.
                     {item, curve}
        EndCourse: The curve that defines the end of the knit.
                   {item, curve}
        LeftBoundary: The curve that defines the left boundary of the knit.
                      {item, curve}
        RightBoundary: Curve that defines the right boundary of the knit.
                       {item, curve}
    Output:
        KnitConstraint: The KnitConstraint resulting from the given inputs.
                        {item, KnitConstraint}
    Remarks:
        Author: Max Eschenbach
        License: MIT License
        Version: 200731
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "CreateManualKnitConstraint"
ghenv.Component.NickName ="CMKC"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "04 Constraints"

# LOCAL MODULE IMPORTS
try:
    from cockatoo import KnitConstraint
except ImportError as e:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

class CreateManualKnitConstraint(component):
    
    def __init__(self):
        super(CreateManualKnitConstraint, self).__init__()
        self.SC = None
        self.EC = None
        self.LB = []
        self.RB = []
    
    def get_ClippingBox(self):
        return Rhino.Geometry.BoundingBox()
    
    def DrawViewportWires(self, args):
        try:
            # get display from args
            display = args.Display
            
            if self.SC and self.EC:
                # diplay colors for start and end in custom display
                scol = System.Drawing.Color.Red
                ecol = System.Drawing.Color.Green
                bcol = System.Drawing.Color.SkyBlue
                # add start and end to customdisplay
                display.DrawCurve(self.SC, scol, 3)
                display.DrawCurve(self.EC, ecol, 3)
                [display.DrawCurve(c, bcol, 2) for c in self.LB]
                [display.DrawCurve(c, bcol, 2) for c in self.RB]
            
        except Exception, e:
            System.Windows.Forms.MessageBox.Show(str(e),
                                                 "Error while drawing preview!")
    
    def RunScript(self, StartCourse, EndCourse, LeftBoundary, RightBoundary):
        # define default break angle for mesh boundary
        
        NullTree = Grasshopper.DataTree[object]()
        
        input_complete = True
        if not StartCourse:
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, "No StartCourse input!")
            input_complete = False
        if not EndCourse:
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, "No EndCourse input!")
            input_complete = False
        if not LeftBoundary:
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, "No LeftBoundary input!")
            input_complete = False
        if not RightBoundary:
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, "No RightBoundary input!")
            input_complete = False
        
        if not input_complete:
            return NullTree
        else:
            # StartBoundary startpoint
            ssp = StartCourse.PointAtStart
            # EndBoundary startpoint
            esp = EndCourse.PointAtStart
            # LeftBoundary startpoint
            lsp = LeftBoundary.PointAtStart
            # RightBoundary startpoint
            rsp = RightBoundary.PointAtStart
            
            # define maximum distance for boundary direction flipping as 10 * abstol
            md = Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance
            md = md * 10
            
            # check for flipping of left and right boundaries
            lbsccp = StartCourse.ClosestPoint(lsp, md)
            rbsccp = StartCourse.ClosestPoint(rsp, md)
            if not lbsccp[0]:
                LeftBoundary.Reverse()
            if not rbsccp[0]:
                RightBoundary.Reverse()
            
            # check for flipping of start and end courses
            scrbcp = LeftBoundary.ClosestPoint(ssp, md)
            ecrbcp = LeftBoundary.ClosestPoint(esp, md)
            if not scrbcp[0]:
                StartCourse.Reverse()
            if not ecrbcp[0]:
                EndCourse.Reverse()
            
            # set left and right for preview drawing
            self.SC = StartCourse
            self.EC = EndCourse
            self.LB = [LeftBoundary]
            self.RB = [RightBoundary]
            
            KC = KnitConstraint(StartCourse, EndCourse, [LeftBoundary], [RightBoundary])
            
            return KC
