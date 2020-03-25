"""Constructs contours for deriving a knitting pattern from a mesh.
TODO: Update docstring
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
import clr

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# CUSTOM RHINO IMPORTS
clr.AddReferenceToFile("KangarooSolver.dll")
import KangarooSolver as ks
from System.Collections.Generic import List

# CUSTOM MODULE IMPORTS
from mbe.geometry import BreakPolyline
from mbe.helpers import mapValuesAsColors
from mbe.component import customDisplay

ghenv.Component.Name = "KnitContoursOnMesh"
ghenv.Component.NickName ="KCOM"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "5 Contouring"

class KnitContoursOnMesh(component):
    
    def RelaxContoursOnMesh(self, polylines, mesh, kLineLength, kEqualize, kOnMesh, thres, iMax, tol):
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
                                                 kLineLength))
                    
                    if nextsegs:
                        goals.append(ks.Goals.Spring(seg.From,
                                                     nextsegs[j].From,
                                                     0.00,
                                                     kLineLength))
                        
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
    
    def CreateContours(self, KMCList, DensitySE, DensityLR, SamplingMode):
        
        # unpack the kmclist
        StartCourse, EndCourse, LeftBoundary, RightBoundary = KMCList
        
        StartCourse = [c.ToPolylineCurve() for c in StartCourse]
        EndCourse = [c.ToPolylineCurve() for c in EndCourse]
        LeftBoundary = [c.ToPolylineCurve() for c in LeftBoundary]
        RightBoundary = [c.ToPolylineCurve() for c in RightBoundary]
        
        # GET SEGMENTATION RATIOS ----------------------------------------------
        
        stLen, sRat = self.GetSegmentRatios(StartCourse)
        etLen, eRat = self.GetSegmentRatios(EndCourse)
        ltLen, lbRat = self.GetSegmentRatios(LeftBoundary)
        rtLen, rbRat = self.GetSegmentRatios(RightBoundary)
        
        # SET SAMPLING DENSITY -------------------------------------------------
        
        if SamplingMode == 0:
            DensityLR = int(DensityLR)
            DensitySE = int(DensitySE)
        elif SamplingMode == 1:
            DensityLR = int(round(max([ltLen, rtLen])/DensityLR))
            DensitySE = int(round(max([stLen, etLen])/DensitySE))
        
        # COMPUTE DIVISIONS FOR LEFT AND RIGHT BOUNDARY SEGMENTS ---------------
        
        # get left boundary divisions
        lbDiv = [int(round(rat*int(DensityLR))) for rat in lbRat]
        lbSum = sum(lbDiv)
        if 0 in lbDiv:
            for i, val in enumerate(lbDiv):
                if val == 0:
                    lbDiv[i] += 1
                if val == max(lbDiv):
                    lbDiv[i] -= 1
        if lbSum != DensityLR:
            dlt = int(DensityLR - lbSum)
            for i, val in enumerate(lbDiv):
                if val == max(lbDiv):
                    lbDiv[i] += dlt
                    break
        
        # get right boundary divisions
        rbDiv = [int(round(rat*int(DensityLR))) for rat in rbRat]
        rbSum = sum(rbDiv)
        if 0 in rbDiv:
            for i, val in enumerate(rbDiv):
                if val == 0:
                    rbDiv[i] += 1
                if val == max(rbDiv):
                    rbDiv[i] -= 1
        if rbSum != DensityLR:
            dlt = int(DensityLR - rbSum)
            for i, val in enumerate(rbDiv):
                if val == max(rbDiv):
                    rbDiv[i] += dlt
                    break
        
        # raise errors if input is wrong
        if not sum(lbDiv) == sum(rbDiv) == DensityLR:
            if SamplingMode == 0:
                raise ValueError("Sampling density for left and right is too " +
                                 "low for number of left or right segments! " +
                                 "Try increasing the density.")
            elif SamplingMode == 1:
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
        sDiv = [int(round(rat*int(DensitySE))) for rat in sRat]
        sSum = sum(sDiv)
        if 0 in sDiv:
            for i, val in enumerate(sDiv):
                if val == 0:
                    sDiv[i] += 1
                if val == max(sDiv):
                    sDiv[i] -= 1
        if sSum != DensitySE:
            dlt = int(DensitySE - sSum)
            for i, val in enumerate(sDiv):
                if val == max(sDiv):
                    sDiv[i] += dlt
                    break
        
        # get end boundary divisions
        eDiv = [int(round(rat*int(DensitySE))) for rat in eRat]
        eSum = sum(eDiv)
        if 0 in eDiv:
            for i, val in enumerate(eDiv):
                if val == 0:
                    eDiv[i] += 1
                if val == max(eDiv):
                    eDiv[i] -= 1
        if eSum != DensitySE:
            dlt = int(DensityLR - eSum)
            for i, val in enumerate(eDiv):
                if val == max(eDiv):
                    eDiv[i] += dlt
                    break
        
        # raise errors if input is wrong
        if not sum(sDiv) == sum(eDiv) == DensitySE:
            if SamplingMode == 0:
                raise ValueError("Sampling density for start and end is too " +
                                 "low for number of start or end segments! " +
                                 "Try increasing the density.")
            elif SamplingMode == 1:
                raise ValueError("Sampling distance for start and end is too " +
                                 "high for number of start or end segments! " +
                                 "Try decreasing the distance.")
        
        # divide all start boundary segments with their matching segment count
        spt = []
        for i, segment in enumerate(StartCourse):
            segment.Domain = Rhino.Geometry.Interval(0, 1)
            segT = segment.DivideByCount(sDiv[i], True)
            segPt = [segment.PointAt(t) for t in segT]
            [spt.append(p) for p in segPt if p not in spt]
        spt = spt[1:-1]
        
        # divide all right boundary segments with their matching segment count
        ept = []
        for i, segment in enumerate(EndCourse):
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
            dt = d.DivideByCount(DensityLR, True)
            dpts = [d.PointAt(t) for t in dt]
            destinations[i] = Rhino.Geometry.PolylineCurve(dpts)
        
        # CREATE FINAL LIST OF CONTOURS ----------------------------------------
        
        Contours = [Rhino.Geometry.PolylineCurve(lpt)]
        Contours.extend(destinations)
        Contours.append(Rhino.Geometry.PolylineCurve(rpt))
        for i, c in enumerate(Contours):
            Contours[i] = c.TryGetPolyline()[1]
        
        return Contours
    
    def RunScript(self, Run, Mesh, KnitConstraints, SamplingDensitySE, SamplingDensityLR, SamplingMode, MaxIterations, Tolerance, Threshold, VizContours):
        
        # INITIALIZATION -------------------------------------------------------
        
        # sanitize samplingmode input
        if SamplingMode < 0:
            SamplingMode = 0
        elif SamplingMode > 1:
            SamplingMode = 1
        
        # set default for maximum iterations
        if MaxIterations == None:
            MaxIterations = 100
        
        # set default tolerance
        if Tolerance == None:
            Tolerance = 1e-6
        
        # set default Threshold
        if not Threshold:
            Threshold = 1e-14
        
        LineStrength = 200
        EqualizeStrength = 100
        OnMeshStrength = 10000
        NullTree = Grasshopper.DataTree[object]()
        
        # DEACTIVATED CONDITION ------------------------------------------------
        
        if not Run or MaxIterations == 0 or not Mesh or not KnitConstraints:
            self.Message = "Deactivated"
            return NullTree
        
        # UNPACK CONSTRAINTS ---------------------------------------------------
        
        StartCourse = list(KnitConstraints.Branch(0))
        EndCourse = list(KnitConstraints.Branch(1))
        LeftBoundary = list(KnitConstraints.Branch(2))
        RightBoundary = list(KnitConstraints.Branch(3))
        
        KMCList = [StartCourse, EndCourse, LeftBoundary, RightBoundary]
        
        # SAMPLE INPUT AND CREATE CONTOURS -------------------------------------
        
        Contours = self.CreateContours(KMCList,
                                       SamplingDensitySE,
                                       SamplingDensityLR,
                                       SamplingMode)
        
        # RELAX CONTOUR CURVES ON THE MESH -------------------------------------
        
        Contours, Iterations = self.RelaxContoursOnMesh(Contours,
                                                        Mesh,
                                                        LineStrength,
                                                        EqualizeStrength,
                                                        OnMeshStrength,
                                                        Threshold,
                                                        MaxIterations, 
                                                        Tolerance)
        Contours.reverse()
        
        # VISUALISATION OF CONTOURS USING CUSTOM DISPLAY -----------------------
        
        if VizContours:
            # make customdisplay
            viz = customDisplay(self, True)
            for i, pl in enumerate(Contours):
                segs = [Rhino.Geometry.LineCurve(s) for s in pl.GetSegments()]
                numseg = len(segs)
                ccols = mapValuesAsColors(range(numseg), 0, numseg, 0.0, 0.35)
                for j, seg in enumerate(segs):
                    viz.AddCurve(seg, ccols[j], 3)
        else:
            viz = customDisplay(self, False)
        
        
        # SET COMPONENT MESSAGE ------------------------------------------------
        
        if Iterations < MaxIterations:
            self.Message = "Converged after {} iterations".format(Iterations)
        else:
            self.Message = "Stopped after {} iterations".format(Iterations)
        
        # RETURN OUTPUTS -------------------------------------------------------
        
        return Contours
