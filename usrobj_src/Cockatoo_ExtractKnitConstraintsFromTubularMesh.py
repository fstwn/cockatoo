"""
Extracts the necessary constraints to create KnitContours for a tubular with
two closed boundaries based  on specified parameters. The constraints consist of
a start, end as well as a  left and right boundary. Preview shows the start
course in red, the end course in green and the left/right boundaries in orange.
To extract the constraints, the boundary of the mesh is broken apart at kinks
which exceed the specified break angle. The 'Start' and 'End' parameters define
indices for the resulting list of polylines.
TODO: Update Docstring!
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
        License: MIT License
        Version: 200705
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division
import clr

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# .NET IMPORTS
from System.Collections.Generic import List

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "ExtractKnitConstraintsFromTubularMesh"
ghenv.Component.NickName ="EKCFTM"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "04 Constraints"

# KANGAROO 2 IMPORT
k2import = False
try:
    clr.AddReferenceToFile("KangarooSolver.dll")
    k2import = True
except IOError:
    pass
if not k2import:
    try:
        clr.AddReferenceToFileAndPath(path.normpath(r"C:\Program Files\Rhino 7\Plug-ins\Grasshopper\Components\KangarooSolver.dll"))
        k2import = True
    except IOError:
        pass
if not k2import:
    try:
        clr.AddReferenceToFileAndPath(path.normpath(r"C:\Program Files\Rhino 7 WIP\Plug-ins\Grasshopper\Components\KangarooSolver.dll"))
        k2import = True
    except IOError:
        pass
if not k2import:
    try:
        clr.AddReferenceToFileAndPath(path.normpath(r"C:\Program Files\Rhino 6\Plug-ins\Grasshopper\Components\KangarooSolver.dll"))
    except IOError:
        raise RuntimeError("KangarooSolver.dll was not found! please add the " + \
                           "folder to your module search paths manually!")
import KangarooSolver as ks

# LOCAL MODULE IMPORTS
try:
    from cockatoo import KnitConstraint
    from cockatoo.utilities import break_polyline
except ImportError as e:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

class ExtractKnitConstraintsFromTubularMesh(component):
    
    def __init__(self):
        super(ExtractKnitConstraintsFromTubularMesh, self).__init__()
        self.SC = None
        self.EC = None
        self.SB = None
    
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
                sbcol = System.Drawing.Color.SkyBlue
                # add start and end to customdisplay
                display.DrawCurve(self.SC, scol, 3)
                display.DrawCurve(self.EC, ecol, 3)
                display.DrawCurve(self.SB, sbcol, 3)
            
        except Exception, e:
            System.Windows.Forms.MessageBox.Show(str(e),
                                                 "Error while drawing preview!")
    
    def relax_polylines_on_mesh(self, polylines, mesh, kLineLength, kOnMesh, thres, iMax, tol):
        """Relax a bunch of polylines on a mesh as an approach to finding
        approximate geodesics on meshes.
        Based on an approach by Anders Holden Deleuran."""
        
        if iMax == 0:
            return polylines, 0
        else:
            # create the list of goals
            goals = []
            for i, pl in enumerate(polylines):
                # make show goal
                ghc = Grasshopper.Kernel.Types.GH_Curve(pl.ToPolylineCurve())
                gow = Grasshopper.Kernel.Types.GH_ObjectWrapper(ghc)
                goals.append(ks.Goals.Locator(gow))
                # make anchor goals
                plpts = pl.ToArray()
                goals.extend([ks.Goals.Anchor(a, 100000) for a in [plpts[0],
                                                                   plpts[-1]]])
                # make spring goals (line length)
                segs = pl.GetSegments()
                if len(segs) <= 10:
                    rml = Grasshopper.Kernel.GH_RuntimeMessageLevel.Remark
                    self.AddRuntimeMessage(rml, "Segment count is quite low! " +
                            "You might want to incerease this to find useful " +
                            "geodesics on the mesh.")
                for j, seg in enumerate(segs):
                    goals.append(ks.Goals.Spring(seg.From,
                                                 seg.To,
                                                 0.00,
                                                 kLineLength))
                # make onmesh goal with all points
                anchorList = List[Rhino.Geometry.Point3d]()
                [anchorList.Add(pt) for pt in plpts]
                goals.append(ks.Goals.OnMesh(anchorList, mesh, kOnMesh))
            
            # create physical system and dotnet list for goals
            ps = ks.PhysicalSystem()
            goalsList = List[ks.IGoal]()
            
            # assign particle indices automagically
            for g in goals:
                ps.AssignPIndex(g, tol)
                goalsList.Add(g)
            
            # solve the k2 physical system
            iterations = 0
            for i in range(iMax):
                ps.Step(goalsList, True, 1000)
                vs = ps.GetvSum()
                iterations += 1
                if vs <= thres:
                    break
            
            # get relaxed polylines from output
            geodesics = []
            for o in ps.GetOutput(goalsList):
                if type(o) is Rhino.Geometry.Polyline:
                    geodesics.append(o)
                    
            return geodesics, iterations
    
    def discretize_destination_line(self, line, mode, resolution):
        """Discretizes a destination line into a polyline with
        equally sized segments."""
        
        if mode == 0:
            division = round(resolution)
            if division == 0:
                division = 1
        elif mode == 1:
            division = math.ceil(line.Length / resolution)
            if division == 0:
                division = 1
        
        line = line.ToNurbsCurve()
        divT = list(line.DivideByCount(division, True))
        dPts = [line.PointAt(t) for t in divT]
        pl = Rhino.Geometry.Polyline(dPts)
        
        return pl
    
    def RunScript(self, Mesh, SeamA, SeamB, Flip):
        
        # define defaults and sanitize input
        if SeamA == None:
            SeamA = 0.5
        elif SeamA > 1:
            SeamA = 1.0
        elif SeamA < 0:
            SeamA = 0.0
        
        if SeamB == None:
            SeamB = 0.5
        elif SeamB > 1:
            SeamB = 1.0
        elif SeamB < 0:
            SeamB = 0.0
        
        if Flip == None:
            Flip = False
        
        # define empty tree placeholder output
        NullTree = Grasshopper.DataTree[object]()
        
        # catch missing inputs
        if not Mesh or SeamA == None or SeamB == None:
            if not Mesh:
                rml = self.RuntimeMessageLevel.Warning
                self.AddRuntimeMessage(rml, "No Mesh input!")
            return NullTree
        
        # get naked edges of the mesh boundary
        mesh_boundaries = list(Mesh.GetNakedEdges())
        if len(mesh_boundaries) > 2:
            errMsg = "Meshes with more than two closed " + \
                     "boundaries are not supported yet!"
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, errMsg)
            return Grasshopper.DataTree[object]()
        
        mesh_boundary_curves = [pl.ToPolylineCurve() for pl in mesh_boundaries]
        
        # set start and end courses
        if Flip:
            StartCourse = mesh_boundary_curves[1]
            EndCourse = mesh_boundary_curves[0]
        else:
            StartCourse = mesh_boundary_curves[0]
            EndCourse = mesh_boundary_curves[1]
        
        # reparam domains
        StartCourse.Domain = Rhino.Geometry.Interval(0, 1)
        EndCourse.Domain = Rhino.Geometry.Interval(0, 1)
        
        # set seam
        StartCourse.ChangeClosedCurveSeam(SeamA)
        EndCourse.ChangeClosedCurveSeam(SeamB)
        
        # create destination line (seam of the knit, if you will)
        dest_a = StartCourse.PointAtStart
        dest_b = EndCourse.PointAtStart
        dest_line = Rhino.Geometry.Line(dest_a, dest_b)
        dest_line = self.discretize_destination_line(dest_line,
                                                     0,
                                                     100)
        
        tol = Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance
        seam_line = self.relax_polylines_on_mesh(
                                            [dest_line],
                                            Mesh,
                                            10,
                                            100,
                                            1e-14,
                                            1000,
                                            tol)[0][0].ToPolylineCurve()
        
        LeftBoundary = seam_line
        RightBoundary = seam_line.Duplicate()
        
        # set left and right for preview drawing
        self.SC = StartCourse
        self.EC = EndCourse
        self.SB = LeftBoundary
        
        KC = KnitConstraint(StartCourse,
                            EndCourse,
                            [LeftBoundary],
                            [RightBoundary])
        
        # return outputs if you have them; here I try it for you:
        return KC
