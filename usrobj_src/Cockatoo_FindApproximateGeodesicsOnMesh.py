"""
Finds approximate geodesics on a mesh by relaxing a polyline between two
destinations points on the mesh using the Kangaroo2 solver.
---
Based on an approach by Anders Holden Deleuran
https://discourse.mcneel.com/t/geodesic-lines-on-a-mesh/58790/4
    Inputs:
        Run: Activate the component, if False the input will pass through.
             {item, bool}
        Destinations: Lines which define the start and end point of the
                      geodesic.
                      {list, line}
        Mesh: The mesh to find geodesics on.
              {item, mesh}
        ProjectDestinations: Will find the closest points on the mesh for the
                             input destinations before approximating the
                             geodesics.
                             {item, bool}
        Resolution: The resolution for discretizing the geodesic
                    polyline.
                    {item, float/integer)
        Mode: The mode for discretizing the geodesic polyline.
              [0] = Relative. the polyline will have ne number of segments
              specified by the Resolution parameter.
              [1] = Absolute. The segments of the geodesic will have the length
              specified by the Resolution Parameter.
              {item, integer}
        Threshold: The threshold for relaxing the geodesic polyline.
                   Defaults to 1e-14.
                   {item, float}
        MaxIterations: The maximum number of iterations for the relaxation.
                       Defaults to 1000.
                       {item, integer}
        LineStrength: The strength of the internal k2 LineLength goal.
                      Defaults to 10.
                      {item, integer}
        OnMeshStrength: The strength of the internal k2 OnMesh goal.
                        Defaults to 100.
                        {item, integer}
    Outputs:
        Geodesics: The found approximate geodesics on the mesh.
                   {list, polyline}
    Remarks:
        Author: Max Eschenbach, based on an approach by Anders Holden Deleuran
        License: Apache License 2.0
        Version: 200603
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division
import clr
import math
from os import path

# .NET IMPORTS
from System.Collections.Generic import List

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# CUSTOM RHINO IMPORTS
import scriptcontext as sc

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

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "FindApproximateGeodesicsOnMesh"
ghenv.Component.NickName ="FAGOM"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "9 Utilities"

class ConstructGeodesicsOnMesh(component):
    
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
    
    def discretize_destination_lines(self, line, mode, resolution):
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
    
    def RunScript(self, Run, Destinations, Mesh, ProjectDestinations, Resolution, Mode, Threshold, MaxIterations, LineStrength, OnMeshStrength):
        
        # initialize abort marker
        _abort = False
        
        # abort if there's no mesh to begin with
        if not Mesh:
            rml = Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, "Need a mesh for approximation " + 
                                        "of geodesics!")
            _abort = True
        
        # abort if there are no destinations specified
        if not Destinations:
            rml = Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, "Need destinations for approximation " + 
                                        "of geodesics!")
            _abort = True
        
        # abort if one of the above is the case
        if _abort:
            return None
        
        # define mode for resolution - 0 = Relative, 1 = Absolute
        if not Mode:
            Mode = 0
        elif Mode < 0:
            Mode = 0
        elif Mode > 1:
            Mode = 1
        
        # define resolution
        if not Resolution:
            Resolution = 100
        
        # set default Threshold
        if not Threshold:
            Threshold = 1e-14
        
        # set default for maximum iterations
        if not MaxIterations:
            MaxIterations = 1000
        
        # set default strength for line length goal
        if not LineStrength:
            LineStrength = 10
        
        # set default strength for onmesh goal
        if not OnMeshStrength:
            OnMeshStrength = 100
        
        # set tolerance to models tolerance
        Tolerance = Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance
        
        # handle projection case
        if ProjectDestinations:
            for i, d in enumerate(Destinations):
                sCP = Mesh.ClosestPoint(d.From)
                eCP = Mesh.ClosestPoint(d.To)
                Destinations[i] = Rhino.Geometry.Line(sCP, eCP)
        
        # discretize the destination lines
        Polylines = [self.discretize_destination_lines(d,
                                                    Mode,
                                                    Resolution)
                                                    for d in Destinations]
        
        if Run:
            Geodesics, Iterations = self.relax_polylines_on_mesh(Polylines,
                                                              Mesh,
                                                              LineStrength,
                                                              OnMeshStrength,
                                                              Threshold,
                                                              MaxIterations,
                                                              Tolerance)
            if Iterations < MaxIterations:
                self.Message = "Converged after {} iterations".format(
                                                                Iterations)
            else:
                self.Message = "Stopped after {} iterations".format(
                                                                MaxIterations)
        else:
            Geodesics = Polylines
            self.Message = "Deactivated"
        
        # return outputs if you have them; here I try it for you:
        return Geodesics
