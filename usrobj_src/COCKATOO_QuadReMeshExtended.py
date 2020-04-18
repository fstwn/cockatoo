"""
Remeshes the input mesh using the new QuadRemesh functionality until all the naked points are identical to the supplied points.
    Inputs:
        Geometry: The original input mesh or brep to quad-remesh. {item, mesh/brep}
        FixedPts: The points where the quadmesh should connect. {list, point}
        TargetQuadCount: The number of quads to try to achieve in the final remeshed object. {item, integer}
        AdaptiveQuadCount: Respect the original Target Quad Count value as much as possible. True returns more quads than TargetQuadCount depending on amount of high-curvature areas {item, boolean}
        AdaptiveSize: Larger values results in for quad sizes that adjust to match input curvature. Smaller values results in more uniform quad sizes at the risk of less feature preservation. Range [0 - 100] {item, float}
        DetectHardEdges: When enabled the hard edges in models will be retained. {item, boolean}
        GuideCurves: GuideCurves for the remeshing process {list, curve}
        GuideCurveInfluence: 0 = Approximate 1 = Interpolate Edge Ring 2 = Interpolate Edge Loop This value is ignored if Guide Curves are not supplied {item, number}
        SymmetryAxis: Symmetry axis to use for symmetric remeshing. [0 = No Symmetry, 1 = X, 2 = Y, 4 = Z] {item, integer}
        PreserveMeshArrayEdgesMode: 0=off, 1=On(Smart), 2=On(Strict) : Mesh array's created from Breps will have their brep face edge boundaries retained. Smart - Small or insignificant input faces are ignored. Strict - All input faces are factored in remeshed result. {item, integer}
        Iterations: The maximum number of attempts to find a quadmesh connecting to the supplied vertices. 0 turns off the feature and only returns the first result {item, integer}
    Output:
        QuadMesh: The remeshed result {item/list, Mesh}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200324
"""

from __future__ import division
import math
#import clr
#clr.AddReferenceToFile("KangarooSolver.dll")
#import KangarooSolver as ks
from ghpythonlib.componentbase import executingcomponent as component
import ghpythonlib.components as ghcomp
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs
import System.Threading
import scriptcontext as sc

ghenv.Component.Name = "QuadReMeshExtended"
ghenv.Component.NickName = "QRMEx"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "3 Remeshing"

class QuadReMeshExtended(component):
    
    TQC_NVX_EQUIVALENT = 6
    MINOR_ADJUSTMENT = 2
    MICRO_ADJUSTMENT = 2
    
    def checkInputData(self, geo, fpts, tqc, aqc, aqs, dhe, gci, sa, pmaem):
        # check Geometry input
        if not geo or geo == None or geo == []:
            return None
        
        if not fpts or fpts == None or fpts == []:
            fpts = []
        
        # check TargetQuadCount input
        if ((not tqc) or 
            (tqc == None) or 
            (tqc == [])):
            return None
        
        # check AdaptiveQuadCount input
        if aqc == None or aqc == []:
            aqc = False
        
        # check AdaptiveSize input
        if not aqs or aqs == None or aqs == []:
            aqs = 0
        elif aqs > 100:
            aqs = 100
        
        # check DetectHardEdges input
        if dhe == None or dhe == []:
            dhe = False
        
        # check GuideCurveInfluence input
        if ((not gci) or
            (gci == None) or 
            (gci == [])):
            gci = 0
        elif gci > 2:
            gci = 2
       
       # check SymmetryAxis input
        if ((not sa) or 
            (sa == None) or 
            (sa == []) or 
            (sa == 0) or 
            (sa > 4)):
                sa = Rhino.Geometry.QuadRemeshSymmetryAxis.None
        elif sa == 1:
            sa = Rhino.Geometry.QuadRemeshSymmetryAxis.X
        elif sa == 2 or sa == 3:
            sa = Rhino.Geometry.QuadRemeshSymmetryAxis.Y
        elif sa == 4:
            sa = Rhino.Geometry.QuadRemeshSymmetryAxis.Z
        
        # check PreserveMeshArrayEdgesMode input
        if ((not pmaem) or 
            (pmaem == None) or
            (pmaem == []) or
            (pmaem < 0)):
                pmaem = 0
        elif pmaem > 2:
            pmaem = 2
        
        return (geo, fpts, tqc, aqc, aqs, dhe, gci, sa, pmaem)
    
    def createRemeshParameters(self, tqc, aqc, aqs, dhe, gci, sa, pmaem):
        # create quad remesh parameters instance
        qrp = Rhino.Geometry.QuadRemeshParameters()
        
        # fill instance with the parameters
        qrp.TargetQuadCount = tqc
        qrp.AdaptiveQuadCount = aqc
        qrp.AdaptiveSize = aqs
        qrp.DetectHardEdges = dhe
        qrp.GuideCurveInfluence = gci
        qrp.SymmetryAxis = sa
        qrp.PreserveMeshArrayEdgesMode = pmaem
        
        # return the quad remesh parameters
        return qrp
    
    def createRemeshedResult(self, Geometry, ReParams, GuideCurves):
        """Creates a remeshed QuadMesh from the inputs and returns it."""
        
        # if guidecurves are supplied, supply them to the remesh routine
        if GuideCurves and GuideCurves != None and GuideCurves != []:
            # if a mesh is supplied as geometry, remesh this mesh
            if type(Geometry) == Rhino.Geometry.Mesh:
                QuadMesh = Geometry.QuadRemesh(ReParams,
                                               GuideCurves)
            
            # if a brep is supplied, create a new quadmesh from this brep
            elif type(Geometry) == Rhino.Geometry.Brep:
                QuadMesh = Rhino.Geometry.Mesh.QuadRemeshBrep(Geometry,
                                                              ReParams,
                                                              GuideCurves)
        
        # if no guidecurves are supplied, don't add them to the routine
        else:
            # if a mesh is supplied as geometry, remesh this mesh
            if type(Geometry) == Rhino.Geometry.Mesh:
                QuadMesh = Geometry.QuadRemesh(ReParams)
                
            # if a brep is supplied, create a new quadmesh from this brep
            elif type(Geometry) == Rhino.Geometry.Brep:
                QuadMesh = Rhino.Geometry.Mesh.QuadRemeshBrep(Geometry,
                                                              ReParams)
        
        return QuadMesh
    
    def getNakedVertices(self, mesh, p3d=False):
        """Returns the naked vertices of a mesh"""
        
        if mesh == None:
            return None
        
        cIds = []
        cPts = []
        nIds = []
        nPts = []
        if p3d == True:
            for i, (vertex, status) in enumerate(zip(list(mesh.Vertices), mesh.GetNakedEdgePointStatus())):
                if status == True:
                    nIds.append(i)
                    nPts.append(Rhino.Geometry.Point3d(vertex))
                else:
                    cIds.append(i)
                    cPts.append(Rhino.Geometry.Point3d(vertex))
        else:
            for i, (vertex, status) in enumerate(zip(list(mesh.Vertices), mesh.GetNakedEdgePointStatus())):
                if status == True:
                    nIds.append(i)
                    nPts.append(vertex)
                else:
                    cIds.append(i)
                    cPts.append(vertex)
        return (nIds, nPts, cIds, cPts)
    
    def adjustRemeshParameters(self, ReParams, numNaked, numFixed, history):
        # list for logging messages
        Logging = []
        
        # compute difference
        diff = numNaked-numFixed
        
        # get current targetquadcount
        tqc = ReParams.TargetQuadCount
        
        # get equivalent value
        equiv = self.TQC_NVX_EQUIVALENT
        
        # get QPN value
        qpn = int(math.ceil(ReParams.TargetQuadCount / numNaked))
        Logging.append("Quads/NakedPt:   " + str(qpn))
        
        # compute adjustment of remesh parameters
        if abs(diff) <= 2:
            adjustment = self.MINOR_ADJUSTMENT
        else:
            adjustment = abs(diff)*equiv
        
        Logging.append("TargetQuadCount: " + str(tqc))
        Logging.append("NakedPts:        " + str(numNaked))
        Logging.append("Difference:      " + str(diff))
        Logging.append("Adjustment:      " + str(adjustment))
        
         # do something to decrease the number of naked vertices if there are too many
        if diff > 0:
            tqc -= adjustment
        # do something to increase the number of naked vertices
        elif diff < 0:
            tqc += adjustment
        
        ReParams.TargetQuadCount = tqc
        
        return ReParams, Logging
    
    def adjustNakedPts(self, QuadMesh, FixedPts):
        """
        Adjusts the naked vertices location of the remeshed result to match
        locations of the FixedPts input.
        Returns the adjusted Mesh.
        """
        
        if not QuadMesh:
            return None
        
        if not FixedPts:
            return None
        
        # pull naked points to fixed points and get distances
        NakedIDs, NakedPts, cIds, cPts = self.getNakedVertices(QuadMesh, p3d=True)
        pulledPts, distKeys = ghcomp.PullPoint(NakedPts, FixedPts)
        
        # sort everything after distance values
        distKeys, SortedFixedPts, SortedNakedPts, SortedNakedIDs = zip(*sorted(zip(distKeys, pulledPts, NakedPts[:], NakedIDs[:])))
        
        # find out where the first point of SortedFixedPts appears in the original list
        memberIndex = [i for i, pt in enumerate(FixedPts) if pt == SortedFixedPts[0]]
        ShiftedFixedPts = list(FixedPts[:])
        ShiftedFixedPts = ShiftedFixedPts[memberIndex[0]:] + ShiftedFixedPts[:memberIndex[0]]
        
        # create polyline from shifted fixedpts
        pl = Rhino.Geometry.Polyline(ShiftedFixedPts)
        
        # sort sorted NakedPts along crv
        crvPts, crvIds = ghcomp.SortAlongCurve(SortedNakedPts, pl)
        
        # get proper ids via the mapping
        crvNakedIDs = [SortedNakedIDs[id] for id in crvIds]
        
        # create a copy of the input mesh
        AdjustedMesh = Rhino.Geometry.Mesh()
        AdjustedMesh.CopyFrom(QuadMesh)
        
        MeshVertices = AdjustedMesh.Vertices
        for i, vertexId in enumerate(crvNakedIDs):
            p3f = Rhino.Geometry.Point3f(ShiftedFixedPts[i].X, 
                                         ShiftedFixedPts[i].Y,
                                         ShiftedFixedPts[i].Z)
            MeshVertices[vertexId] = p3f
        
        return AdjustedMesh
    
    def relaxMesh(self, QuadMesh, TargetEdgeLengths):
        """
        Relaxes the input Mesh using Kangaroo 2.
        """
        pass
    
    def RunScript(self, Geometry, FixedPts, TargetQuadCount, AdaptiveQuadCount, AdaptiveSize, DetectHardEdges, GuideCurves, GuideCurveInfluence, SymmetryAxis, PreserveMeshArrayEdgesMode, AdjustQuadMesh, RelaxQuadMesh, MaxMeshingIterations):
        
        # define outputs so that they are never empty
        QuadMesh = []
        AdjustedQuadMesh = []
        RelaxedQuadMesh = []
        NakedPts = []
        NakedIDs = []
        Logging = []
        
        # CHECK INPUTS ---------------------------------------------------------
        
        result = self.checkInputData(Geometry,
                                     FixedPts,
                                     TargetQuadCount,
                                     AdaptiveQuadCount,
                                     AdaptiveSize,
                                     DetectHardEdges,
                                     GuideCurveInfluence,
                                     SymmetryAxis,
                                     PreserveMeshArrayEdgesMode)
        if not result:
            # return if the check fails
            return None
        else:
            # unpack the result of the check
            Geometry,\
            FixedPts,\
            TargetQuadCount,\
            AdaptiveQuadCount,\
            AdaptiveSize, DetectHardEdges,\
            GuideCurveInfluence,\
            SymmetryAxis,\
            PreserveMeshArrayEdgesMode = result
        
        # CREATE PARAMETERS ----------------------------------------------------
        
        # create QuadRemeshing Parameters based on input values
        ReParams = self.createRemeshParameters(TargetQuadCount,
                                               AdaptiveQuadCount,
                                               AdaptiveSize,
                                               DetectHardEdges,
                                               GuideCurveInfluence,
                                               SymmetryAxis,
                                               PreserveMeshArrayEdgesMode)
        
        # TRIGGER REMESHING ----------------------------------------------------
        
        # If MaxMeshingIterations is 0 return the first result
        if MaxMeshingIterations <= 0:
            QuadMesh = self.createRemeshedResult(Geometry,
                                                 ReParams,
                                                 GuideCurves)
            NakedIDs, NakedPts, cIds, cPts = self.getNakedVertices(
                                                                currentResult,
                                                                p3d=True)
        
        # If MaxMeshingIterations is > 0 try to get a refined result
        else:
            numFixed = len(FixedPts)
            numNaked = None
            history = []
            iteration = 1
            solution = False
            
            while solution == False and iteration < MaxMeshingIterations:
                # write to the log
                Logging.append("-------------------------------------")
                Logging.append("ITERATION " + str(iteration))
                Logging.append(" ")
                
                # listen for escape key and abort if pressed
                sc.escape_test()
                
                # create a quadremeshed result
                currentResult = self.createRemeshedResult(Geometry,
                                                          ReParams,
                                                          GuideCurves)
                
                # get naked vertices of current result
                NakedIDs, NakedPts, cIds, cPts = self.getNakedVertices(
                                                                currentResult,
                                                                p3d=True)
                
                # if the number of naked points is identical to fixed points,
                # treat this as the solution
                numNaked = len(NakedPts)
                history.append((ReParams.TargetQuadCount, numNaked))
                if numNaked == numFixed:
                    solution = True
                    break
                
                # Adjust the remeshing parameters for the next iteration
                else:
                    ReParams, logs = self.adjustRemeshParameters(ReParams,
                                                           numNaked,
                                                           numFixed,
                                                           history)
                    Logging.extend(logs)
                    iteration += 1
            
            # set RuntimeMessages
            if numNaked == numFixed:
                rmlevel = Grasshopper.Kernel.GH_RuntimeMessageLevel.Remark
                self.AddRuntimeMessage(rmlevel, "Mesh was returned with the " +
                                       "target number of naked vertices after " +
                                       str(iteration) + " iterations." )
            else:
                rmlevel = Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning
                diff = numNaked-numFixed
                if diff > 0:
                    msgdiff = "+" + str(diff)
                else:
                    msgdiff = str(diff)
                self.AddRuntimeMessage(rmlevel, "Mesh was returned with " +
                                       msgdiff + " naked vertices compared " + 
                                       "to FixedPts after " + str(iteration) + 
                                       " iterations!" )
            
            QuadMesh = currentResult
        
        # ADJUSTMENT OF RESULT -------------------------------------------------
        
        if AdjustQuadMesh:
            AdjustedQuadMesh = self.adjustNakedPts(QuadMesh, FixedPts)
        
        # RETURN RESULTS -------------------------------------------------------
        return (QuadMesh, AdjustedQuadMesh, RelaxedQuadMesh, NakedPts, NakedIDs, Logging)
