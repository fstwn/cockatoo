"""Extracts constraint from a mesh to derive a knitting pattern.
TODO: Update docstring, multiple start and end indices?, edge case for touching s and e
    Inputs:
        Mesh:{item, mesh}
        BreakAngle: {item, float}
        StartIndex: {item, integer}
        EndIndex: {item, integer}
    Output:
        StartCourse: {item, polyline}
        EndCourse: {item, polyline}
        LeftBoundary: {item, polyline}
        RightBoundary: {item, polyline}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200325
"""

# PYTHON LIBRARY IMPORTS
from __future__ import division
from collections import deque
import math

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# CUSTOM RHINO IMPORTS
import scriptcontext
from ghpythonlib import treehelpers as th

# CUSTOM MODULE IMPORTS
import mbe.geometry
reload(mbe.geometry)
from mbe.geometry import BreakPolyline
from mbe.helpers import mapValuesAsColors
import mbe.component as ct

ghenv.Component.Name = "ExtractKnitConstraintsFromMesh"
ghenv.Component.NickName ="EKCFM"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "4 Constraint Extraction"

class ExtractKnitConstraintsFromMesh(component):
    
    def RunScript(self, Mesh, BreakAngle, Start, End, VizConstraints):
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
            ct.addRuntimeWarning(self, "Start index cannot be the same as " +
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
        
        # define maximum distance for boundary direction flipping as 1mm
        md = Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Millimeters,
                                       Rhino.RhinoDoc.ActiveDoc.ModelUnitSystem)
        md = md * 1
        
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
        
        if VizConstraints:
            viz = ct.customDisplay(self, True)
            # diplay colors for start and end in custom display
            scol = System.Drawing.Color.Red
            ecol = System.Drawing.Color.Green
            # add start and end to customdisplay
            viz.AddCurve(StartCourse, scol, 3)
            viz.AddCurve(EndCourse, ecol, 3)
        else:
            viz = ct.customDisplay(self, False)
        
        # Left and right boundaries again so we don't have to do it yet again
        LeftBoundary = BreakPolyline(LeftBoundary.ToPolyline(), BreakAngle)
        RightBoundary = BreakPolyline(RightBoundary.ToPolyline(), BreakAngle)
        
        KnitConstraints = Grasshopper.DataTree[object]()
        KnitConstraints.Add(StartCourse, Grasshopper.Kernel.Data.GH_Path(0))
        KnitConstraints.Add(EndCourse, Grasshopper.Kernel.Data.GH_Path(1))
        KnitConstraints.AddRange(LeftBoundary, Grasshopper.Kernel.Data.GH_Path(2))
        KnitConstraints.AddRange(RightBoundary, Grasshopper.Kernel.Data.GH_Path(3))
        
        # return outputs if you have them; here I try it for you:
        return KnitConstraints
