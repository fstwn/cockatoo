"""
Constructs contours for deriving a knitting pattern from a mesh. Use the
GeodesicStrength and TweenStrength inputs to control the shape and distribution
of the contour curves on the mesh.
---
Based on an approach for geodesics by Anders Holden Deleuran
https://discourse.mcneel.com/t/geodesic-lines-on-a-mesh/58790/4
    Inputs:
        Run: Set to True to activate the component. Connect a boolean toggle
             ideally.
             {item, bool}
        Mesh: The mesh to create the contours on.
              {item, mesh}
        KnitConstraints: The Cockatoo KnitConstraints defining the direction and
                         limits of the contours.
                         {item, float}
        ContourDensity: The density (i.e. amount) of the contour curves.
                        {item, int/float}
        ContourMode: How to interpret the ContourDensity input.
                     [0] = Relative - ContourDensity sets the total number of
                           contour curves.
                     [1] = Absolute - ContourDensity sets the target distance
                         between the contour curves.
                     {item, integer}
        ContourDivisionDensity: The resolution (i.e. division count) of the
                                contour curves.
                                {item, int/float}
        ContourDivisionMode: How to interpret the ContourDivisionDensity input.
                             [0] = Relative - ContourDivisionDensity sets the
                                 total num of divisions for the contour curves.
                             [1] = Absolute - ContourDivisionDensity sets the
                                 target segment length of the contour curves.
                             {item, int/float}
        GeodesicStrength: Strength of the internal Kangaroo2 goal minimizing the
                          length of the contour curves. Defaults to 1000.
                          {item, int}
        TweenStrength: Strength of the internal Kangaroo2 goal controlling the
                       distribution of the contours. Defaults to 2000.
                       {item, int}
        MaxIterations: The maximum number of iterations for the internal
                       Kangaroo2 solver.
                       {item, int}
        Tolerance: The tolerance of the internal Kangaroo2 solver.
                   Defaults to 1e-6.
                   {item, int}
        Threshold: The threshold for the internal Kangaroo2 solver.
                   Defaults to 1e-14.
                   {item, int}
    Output:
        KnitContours: The KnitContour curves on the mesh for initializing a
                      KnitNetwork and deriving a knitting pattern.
                      {item, polyline}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200531
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division
import clr
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
ghenv.Component.Name = "KnitContoursOnMesh"
ghenv.Component.NickName ="KCOM"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "5 Contouring"

class KnitContoursOnMesh(component):
    
    def RelaxContoursOnMesh(self, polylines, mesh, kLineLengthA, kLineLengthB, kEqualize, kOnMesh, thres, iMax, tol):
        """
        Relax a bunch of contour lines on a mesh.
        Based on an approach by Anders Holden Deleuran.
        """
        
        EQMODE = 0
        
        if iMax == 0:
            return polylines, 0
        else:
            # create the list of goals
            goals = []
            if EQMODE == 0:
                eqLines = List[Rhino.Geometry.Curve]()
            elif EQMODE == 1:
                eqLines = [List[Rhino.Geometry.Curve]() \
                           for x in range(len(polylines))]
            for i, pl in enumerate(polylines):
                # make show goal
                ghc = Grasshopper.Kernel.Types.GH_Curve(pl.ToPolylineCurve())
                gow = Grasshopper.Kernel.Types.GH_ObjectWrapper(ghc)
                goals.append(ks.Goals.Locator(gow))
                
                # make anchor goals
                plpts = pl.ToArray()
                if i == 0 or i == (len(polylines) - 1):
                    goals.extend([ks.Goals.Anchor(pt, 10000000) for pt in plpts])
                else:
                    goals.extend([ks.Goals.Anchor(a, 10000000) for a in [plpts[0],
                                                                   plpts[-1]]])
                
                # make spring goals (line length)
                segs = pl.GetSegments()
                
                # get next segments
                y = i + 1
                if y <= len(polylines) - 1:
                    nextsegs = polylines[y].GetSegments()
                else:
                    nextsegs = None
                
                for j, seg in enumerate(segs):
                    goals.append(ks.Goals.Spring(seg.From,
                                                 seg.To,
                                                 0.00,
                                                 kLineLengthA))
                    
                    if nextsegs:
                        goals.append(ks.Goals.Spring(seg.From,
                                                     nextsegs[j].From,
                                                     0.00,
                                                     kLineLengthB))
                        if kEqualize:
                            # create the equal length line
                            eqln = Rhino.Geometry.LineCurve(seg.From,
                                                            nextsegs[j].From)
                            if EQMODE == 0:
                                eqLines.Add(eqln)
                            elif EQMODE == 1:
                                eqLines[0].Add(eqln)
                
                # make onmesh goal with all points
                anchorList = List[Rhino.Geometry.Point3d]()
                [anchorList.Add(pt) for pt in plpts]
                goals.append(ks.Goals.OnMesh(anchorList, mesh, kOnMesh))
            
            # create equallength goal
            if kEqualize:
                if EQMODE == 0:
                    goals.append(ks.Goals.EqualLength(eqLines, kEqualize))
                elif EQMODE == 1:
                    for eqLine in eqLines:
                        goals.append(ks.Goals.EqualLength(eqLine, kEqualize))
            
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
                ps.Step(goalsList, True, 1000.0)
                vs = ps.GetvSum()
                iterations += 1
                if vs <= thres:
                    break
            
            # get relaxed polylines from output
            contours = []
            for o in ps.GetOutput(goalsList):
                if type(o) is Rhino.Geometry.Polyline:
                    contours.append(o)
                    
            return contours, iterations
    
    def GetSegmentRatios(self, segments):
        """
        Get the length ratios for the given segment relative to their overall
        length.
        """
        
        overall_length = sum([seg.GetLength() for seg in segments])
        
        seg_ratios = [(seg.GetLength() / overall_length) for seg in segments]
        
        return overall_length, seg_ratios
    
    def CreateContours(self, KMCList, ContourDensity, ContourDivisionDensity, ContourMode, ContourDivisionMode):
        
        # unpack the kmclist
        StartCourse, EndCourse, LeftBoundary, RightBoundary = KMCList
        
        # GET SEGMENTATION RATIOS ----------------------------------------------
        
        stLen, sRat = self.GetSegmentRatios([StartCourse])
        etLen, eRat = self.GetSegmentRatios([EndCourse])
        ltLen, lbRat = self.GetSegmentRatios(LeftBoundary)
        rtLen, rbRat = self.GetSegmentRatios(RightBoundary)
        
        # SET SAMPLING DENSITY -------------------------------------------------
        
        if ContourMode == 0:
            ContourDensity = int(ContourDensity)
        elif ContourMode == 1:
            ContourDensity = int(round(max([stLen, etLen])/ContourDensity))
        
        if ContourDivisionMode == 0:
            ContourDivisionDensity = int(ContourDivisionDensity)
        elif ContourDivisionMode == 1:
            ContourDivisionDensity = int(round(max([ltLen, rtLen])/ContourDivisionDensity))
        
        # COMPUTE DIVISIONS FOR LEFT AND RIGHT BOUNDARY SEGMENTS ---------------
        
        # get left boundary divisions
        lbDiv = [int(round(rat*int(ContourDivisionDensity))) for rat in lbRat]
        lbSum = sum(lbDiv)
        if 0 in lbDiv:
            for i, val in enumerate(lbDiv):
                if val == 0:
                    lbDiv[i] += 1
                if val == max(lbDiv):
                    lbDiv[i] -= 1
        if lbSum != ContourDivisionDensity:
            dlt = int(ContourDivisionDensity - lbSum)
            for i, val in enumerate(lbDiv):
                if val == max(lbDiv):
                    lbDiv[i] += dlt
                    break
        
        # get right boundary divisions
        rbDiv = [int(round(rat*int(ContourDivisionDensity))) for rat in rbRat]
        rbSum = sum(rbDiv)
        if 0 in rbDiv:
            for i, val in enumerate(rbDiv):
                if val == 0:
                    rbDiv[i] += 1
                if val == max(rbDiv):
                    rbDiv[i] -= 1
        if rbSum != ContourDivisionDensity:
            dlt = int(ContourDivisionDensity - rbSum)
            for i, val in enumerate(rbDiv):
                if val == max(rbDiv):
                    rbDiv[i] += dlt
                    break
        
        # raise errors if input is wrong
        if not sum(lbDiv) == sum(rbDiv) == ContourDivisionDensity:
            if ContourDivisionMode == 0:
                raise ValueError("Sampling density for left and right is too " +
                                 "low for number of left or right segments! " +
                                 "Try increasing the density.")
            elif ContourDivisionMode == 1:
                raise ValueError("Sampling distance for left and right is " +
                                 "too high for number of left or right " +
                                 "segments! Try decreasing the distance.")
        
        # divide all left boundary segments with their matching segment count
        lpt = []
        for i, segment in enumerate(LeftBoundary):
            segment.Domain = Rhino.Geometry.Interval(0, 1)
            segT = segment.DivideByCount(lbDiv[i], True)
            segPt = [segment.PointAt(t) for t in segT]
            [lpt.append(p) for p in segPt if p not in lpt]
        
        # divide all right boundary segments with their matching segment count
        rpt = []
        for i, segment in enumerate(RightBoundary):
            segment.Domain = Rhino.Geometry.Interval(0, 1)
            segT = segment.DivideByCount(rbDiv[i], True)
            segPt = [segment.PointAt(t) for t in segT]
            [rpt.append(p) for p in segPt if p not in rpt]
        
        # GET SEGMENTATION RATIOS FOR START AND END BOUNDARY -------------------
        
        # get start boundary divisions
        sDiv = [int(round(rat*int(ContourDensity))) for rat in sRat]
        sSum = sum(sDiv)
        if 0 in sDiv:
            for i, val in enumerate(sDiv):
                if val == 0:
                    sDiv[i] += 1
                if val == max(sDiv):
                    sDiv[i] -= 1
        if sSum != ContourDensity:
            dlt = int(ContourDensity - sSum)
            for i, val in enumerate(sDiv):
                if val == max(sDiv):
                    sDiv[i] += dlt
                    break
        
        # get end boundary divisions
        eDiv = [int(round(rat*int(ContourDensity))) for rat in eRat]
        eSum = sum(eDiv)
        if 0 in eDiv:
            for i, val in enumerate(eDiv):
                if val == 0:
                    eDiv[i] += 1
                if val == max(eDiv):
                    eDiv[i] -= 1
        if eSum != ContourDensity:
            dlt = int(ContourDivisionDensity - eSum)
            for i, val in enumerate(eDiv):
                if val == max(eDiv):
                    eDiv[i] += dlt
                    break
        
        # raise errors if input is wrong
        if not sum(sDiv) == sum(eDiv) == ContourDensity:
            if ContourMode == 0:
                raise ValueError("Sampling density for start and end is too " +
                                 "low for number of start or end segments! " +
                                 "Try increasing the density.")
            elif ContourMode == 1:
                raise ValueError("Sampling distance for start and end is too " +
                                 "high for number of start or end segments! " +
                                 "Try decreasing the distance.")
        
        # divide all start boundary segments with their matching segment count
        spt = []
        for i, segment in enumerate([StartCourse]):
            segment.Domain = Rhino.Geometry.Interval(0, 1)
            segT = segment.DivideByCount(sDiv[i], True)
            segPt = [segment.PointAt(t) for t in segT]
            [spt.append(p) for p in segPt if p not in spt]
        spt = spt[1:-1]
        
        # divide all right boundary segments with their matching segment count
        ept = []
        for i, segment in enumerate([EndCourse]):
            segment.Domain = Rhino.Geometry.Interval(0, 1)
            segT = segment.DivideByCount(eDiv[i], True)
            segPt = [segment.PointAt(t) for t in segT]
            [ept.append(p) for p in segPt if p not in ept]
        ept = ept[1:-1]
        
        # CREATE DESTIONATION LINES AND SAMPLE THEM ----------------------------
        
        # build destination lines
        destinations = []
        for i, pt in enumerate(spt):
            ln = Rhino.Geometry.LineCurve(pt, ept[i])
            destinations.append(ln)
        
        # sample destination lines
        for i, d in enumerate(destinations):
            d.Domain = Rhino.Geometry.Interval(0, 1)
            dt = d.DivideByCount(ContourDivisionDensity, True)
            dpts = [d.PointAt(t) for t in dt]
            destinations[i] = Rhino.Geometry.PolylineCurve(dpts)
        
        # CREATE FINAL LIST OF CONTOURS ----------------------------------------
        
        Contours = [Rhino.Geometry.PolylineCurve(lpt)]
        Contours.extend(destinations)
        Contours.append(Rhino.Geometry.PolylineCurve(rpt))
        for i, c in enumerate(Contours):
            Contours[i] = c.TryGetPolyline()[1]
        
        return Contours
    
    def RunScript(self, Run, Mesh, KnitConstraint, ContourDensity, ContourMode, ContourDivisionDensity, ContourDivisionMode, GeodesicStrength, TweenStrength, MaxIterations, Tolerance, Threshold):
        
        # INITIALIZATION -------------------------------------------------------
        
        # sanitize ContourMode input
        if ContourMode == None:
            ContourMode = 0
        elif ContourMode < 0:
            ContourMode = 0
        elif ContourMode > 1:
            ContourMode = 1
        
        # sanitize ContourDivisionMode input
        if ContourDivisionMode == None:
            ContourDivisionMode = 0
        elif ContourDivisionMode < 0:
            ContourDivisionMode = 0
        elif ContourDivisionMode > 1:
            ContourDivisionMode = 1
        
        # set default for maximum iterations
        if MaxIterations == None:
            MaxIterations = 100
        
        # set default tolerance
        if Tolerance == None:
            Tolerance = 1e-6
        
        # set default Threshold
        if not Threshold:
            Threshold = 1e-14
        
        if GeodesicStrength == None:
            GeodesicStrength = 1000
        if TweenStrength == None:
            TweenStrength = 2000
        
        EqualizeStrength = 0
        OnMeshStrength = 100000
        
        NullTree = Grasshopper.DataTree[object]()
        
        # DEACTIVATED CONDITION ------------------------------------------------
        
        if not Run or MaxIterations == 0 or not Mesh or not KnitConstraint:
            self.Message = "Deactivated"
            return NullTree
        
        # UNPACK CONSTRAINTS ---------------------------------------------------
        
        StartCourse = KnitConstraint.StartCourse
        EndCourse = KnitConstraint.EndCourse
        LeftBoundary = KnitConstraint.LeftBoundary
        RightBoundary = KnitConstraint.RightBoundary
        
        KMCList = [StartCourse, EndCourse, LeftBoundary, RightBoundary]
        
        # SAMPLE INPUT AND CREATE CONTOURS -------------------------------------
        
        Contours = self.CreateContours(KMCList,
                                       ContourDensity,
                                       ContourDivisionDensity,
                                       ContourMode,
                                       ContourDivisionMode)
        
        # RELAX CONTOUR CURVES ON THE MESH -------------------------------------
        
        Contours, Iterations = self.RelaxContoursOnMesh(Contours,
                                                        Mesh,
                                                        GeodesicStrength,
                                                        TweenStrength,
                                                        EqualizeStrength,
                                                        OnMeshStrength,
                                                        Threshold,
                                                        MaxIterations, 
                                                        Tolerance)
        
        # SET COMPONENT MESSAGE ------------------------------------------------
        
        if Iterations < MaxIterations:
            self.Message = "Converged after {} iterations".format(Iterations)
        else:
            self.Message = "Stopped after {} iterations".format(Iterations)
        
        # RETURN OUTPUTS -------------------------------------------------------
        
        return Contours
