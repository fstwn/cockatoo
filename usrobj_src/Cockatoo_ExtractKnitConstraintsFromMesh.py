"""
Extracts the necessary constraints to create KnitContours for a mesh based on
specified parameters. The constraints consist of a start, end as well as a left
and right boundary. Preview shows the start course in red and the end course in
green.
To extract the constraints, the boundary of the mesh is broken apart at kinks
which exceed the specified break angle. The 'Start' and 'End' parameters define
indices for the resulting list of polylines.
    Inputs:
        Mesh: The mesh that should be knit for constraint extraction.
              {item, mesh}
        BreakAngle: Angle at which to break apart mesh boundary.
                    {item, float}
        StartIndex: Index for the start course.
                    {item, integer}
        EndIndex: Index for the end course.
                  {item, integer}
    Output:
        KnitConstraints: The knitconstraints for this mesh for contour
                         generation.
                         {item, KnitConstraint}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200602
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
try:
    from Cockatoo import KnitConstraint
    from Cockatoo.Utilities import BreakPolyline
except ImportError:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "ExtractKnitConstraintsFromMesh"
ghenv.Component.NickName ="EKCFM"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "4 Constraint Extraction"

class ExtractKnitConstraintsFromMesh(component):
    
    def __init__(self):
        super(ExtractKnitConstraintsFromMesh, self).__init__()
        self.SC = None
        self.EC = None
        self.LB = []
        self.RB = []
    
    def DrawViewportWires(self, args):
        try:
            # get display from args
            display = args.Display
            
            if self.SC and self.EC:
                # diplay colors for start and end in custom display
                scol = System.Drawing.Color.Red
                ecol = System.Drawing.Color.Green
                # add start and end to customdisplay
                display.DrawCurve(self.SC, scol, 3)
                display.DrawCurve(self.EC, ecol, 3)
            
        except Exception, e:
            System.Windows.Forms.MessageBox.Show(str(e),
                                                 "Error while drawing preview!")
    
    def RunScript(self, Mesh, BreakAngle, Start, End):
        # define default break angle for mesh boundary
        if BreakAngle == None:
            BreakAngle = 1.0
        
        NullTree = Grasshopper.DataTree[object]()
        
        if not Mesh:
            return NullTree
        
        # get naked edges of the mesh boundary
        meshBoundary = list(Mesh.GetNakedEdges())
        if len(meshBoundary) > 1:
            raise NotImplementedError("Meshes with multiple closed boundaries"+
                                      " are not supported yet!")
            return Grasshopper.DataTree[object]()
        
        # break the boundary polyline based on angles
        boundarysegments = BreakPolyline(meshBoundary[0], BreakAngle)
        
        # sanitize start and end inputs
        if Start > len(boundarysegments)-1:
            Start = len(boundarysegments)-1
        if End > len(boundarysegments)-1:
            End = len(boundarysegments)-1
        
        # extract left and right boundaries by indices
        if Start == End:
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, "Start index cannot be the same as " +
                                       "end index! Aborting...")
            return NullTree
        elif Start > End:
            Right = boundarysegments[End+1:Start]
            Left = boundarysegments[0:End] + boundarysegments[Start+1:]
        elif End > Start:
            Right = boundarysegments[Start+1:End]
            Left = boundarysegments[0:Start] + boundarysegments[End+1:]
        
        # extract start and end course polyline by index
        StartCourse = boundarysegments[Start]
        EndCourse = boundarysegments[End]
        
        # join the boundary curves
        if len(Left) > 0:
            LeftBoundary = list(Rhino.Geometry.Curve.JoinCurves(Left))[0]
        else:
            print StartCourse.PointAtEnd == EndCourse.PointAtStart
            raise NotImplementedError("Touching start and end courses are " +
                                      "not supported yet!")
        if len(Right) > 0:
            RightBoundary = list(Rhino.Geometry.Curve.JoinCurves(Right))[0]
        else:
            print StartCourse.PointAtStart == EndCourse.PointAtEnd
            raise NotImplementedError("Touching start and end courses are " +
                                      "not supported yet!")
        
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
        
        # Break apart left and right boundaries again so we don't have to do
        # it yet again in the next step
        LeftBoundary = BreakPolyline(LeftBoundary.ToPolyline(), BreakAngle)
        RightBoundary = BreakPolyline(RightBoundary.ToPolyline(), BreakAngle)
        
        # set left and right for preview drawing
        self.SC = StartCourse
        self.EC = EndCourse
        self.LB = LeftBoundary
        self.RB = RightBoundary
        
        KC = KnitConstraint(StartCourse, EndCourse, LeftBoundary, RightBoundary)
        
        KnitConstraints = Grasshopper.DataTree[object]()
        KnitConstraints.Add(StartCourse, Grasshopper.Kernel.Data.GH_Path(0))
        KnitConstraints.Add(EndCourse, Grasshopper.Kernel.Data.GH_Path(1))
        KnitConstraints.AddRange(LeftBoundary, Grasshopper.Kernel.Data.GH_Path(2))
        KnitConstraints.AddRange(RightBoundary, Grasshopper.Kernel.Data.GH_Path(3))
        
        # return outputs if you have them; here I try it for you:
        return KC
