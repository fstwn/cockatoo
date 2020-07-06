"""
Remeshes the input mesh using the new QuadRemesh functionality until all the
naked points are identical to the supplied points.
TODO: Update docstring, update inputs to item + runcount strategy instead of
using tree branches
    Inputs:
        Geometry: The original input mesh or brep to quad-remesh.
                  {tree, mesh/brep}
        FixedPts: The points where the quadmesh should connect (i.e. naked
                  vertices).
                  {list, point}
        InitialTargetQuadCount: The number of quads to try to achieve in the
                                final remeshed object.
                                {tree, integer}
        AdaptiveQuadCount: Respect the original Target Quad Count value as much
                           as possible. True returns more quads than
                           TargetQuadCount depending on amount of high-curvature
                           areas.
                           {item, bool}
        AdaptiveSize: Larger values results in for quad sizes that adjust to
                      match input curvature. Smaller values results in more
                      uniform quad sizes at the risk of less feature
                      preservation. Range [0 - 100]
                      {item, float}
        DetectHardEdges: When enabled the hard edges in models will be retained.
                         {item, boolean}
        GuideCurves: GuideCurves for the remeshing process.
                     {list, curve}
        GuideCurveInfluence: This value is ignored if Guide Curves are not
                             supplied.
                             [0] = Approximate
                             [1] = Interpolate Edge Ring 
                             [2] = Interpolate Edge Loop
                             {item, int}
        SymmetryAxis: Symmetry axis to use for symmetric remeshing.
                      [0] = No Symmetry
                      [1] = X
                      [2] = Y
                      [4] = Z 
                      {item, int}
        PreserveMeshArrayEdgesMode: Mesh array's created from Breps will have
                                    their brep face edge boundaries retained.
                                    Smart - Small or insignificant input faces
                                    are ignored.
                                    Strict - All input faces are factored in
                                    remeshed result.
                                    [0] = Off
                                    [1] = On(Smart)
                                    [2] = On(Strict)
                                    {item, int}
        MaxMeshingIterations: The maximum number of attempts to find a quadmesh
                              connecting to the supplied FixedPts. 0 turns off
                              the feature and only returns the first result.
                              {item, int}
        AdjustQuadMesh: If True, the component will try to move the naked
                        vertices of the quadmesh to the locations of the
                        supplied FixedPts. This will only be executed for meshes
                        where NakedPts = FixedPts!
                        {item, bool}
        RelaxQuadMesh: If True, an internal Kangaroo 2 solver will relax the
                       quadmesh and keep naked vertices fixed.
                       {item, bool}
        RelaxationEdgeLengthFactor: The target edgelength factor for the
                                    relaxation process.
                                    {item, float}
        RelaxationIterations: Number of iterations for the relaxation of the
                              mesh.
                              {item, int}
        RelaxationTolerance: Tolerance for the relaxation process.
                             Defaults to [0.01] units.
                             {item, float}
        Parallel: Toggle parallel execution on and off.
                  {item, bool}
    Output:
        QuadMesh: The remeshed result.
                  {item/list, mesh}
    Remarks:
        Author: Max Eschenbach
        License: MIT License
        Version: 200705
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division
import clr
import math
import os

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import ghpythonlib.treehelpers as th
import ghpythonlib.components as ghcomp
import Grasshopper, GhPython
import System
import Rhino

# KANGAROO 2 IMPORT
if "KangarooSolver" in str(clr.References):
    import KangarooSolver as ks
else:
    try:
        rhino_version = Rhino.RhinoApp.ExeVersion
        if os.name == "nt":
            if rhino_version == 6:
                k2ap = ("C:/Program Files/Rhino 6/Plug-ins/Grasshopper/"
                        "Components/KangarooSolver.dll")
                clr.AddReferenceToFileAndPath(os.path.normpath(k2ap))
            elif rhino_version == 7:
                k2ap = ("C:/Program Files/Rhino 7/Plug-ins/Grasshopper/"
                        "Components/KangarooSolver.dll")
                if not os.path.exists(k2ap):
                    k2ap = ("C:/Program Files/Rhino 7 WIP/Plug-ins/Grasshopper/"
                            "Components/KangarooSolver.dll")
                clr.AddReferenceToFileAndPath(os.path.normpath(k2ap))
        elif os.name == "posix":
            k2ap = (r"/Applications/Rhinoceros.app/Contents/Frameworks/"
                      "RhCore.framework/Versions/A/Resources/ManagedPlugIns/"
                      "GrasshopperPlugin.rhp/Components/KangarooSolver.dll")
            clr.AddReferenceToFileAndPath(os.path.normpath(k2ap))
        import KangarooSolver as ks
    except (IOError, ImportError):
        try:
            clr.AddReferenceToFile("KangarooSolver.dll")
            import KangarooSolver as ks
        except (IOError, ImportError):
            raise RuntimeError("KangarooSolver.dll was not found! "
                               "please add the folder to your module "
                               "search paths manually!")

# ADDITIONAL RHINO IMPORTS
from System.Collections.Generic import List
import scriptcontext as sc

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "QuadReMeshExtendedParallel"
ghenv.Component.NickName = "QRMExP"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "02 Meshing & Remeshing"

class QuadReMeshExtendedParallel(component):
    
    MINOR_ADJUSTMENT = 4
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
        
        if len(list(mesh.Vertices)) < 1:
            return ([], [], [], [])
        
        cIds = []
        cPts = []
        nIds = []
        nPts = []
        if p3d == True:
            for i, (vertex, status) in enumerate(zip(list(mesh.Vertices), 
                                            mesh.GetNakedEdgePointStatus())):
                if status == True:
                    nIds.append(i)
                    nPts.append(Rhino.Geometry.Point3d(vertex))
                else:
                    cIds.append(i)
                    cPts.append(Rhino.Geometry.Point3d(vertex))
        else:
            for i, (vertex, status) in enumerate(zip(list(mesh.Vertices), 
                                            mesh.GetNakedEdgePointStatus())):
                if status == True:
                    nIds.append(i)
                    nPts.append(vertex)
                else:
                    cIds.append(i)
                    cPts.append(vertex)
        return (nIds, nPts, cIds, cPts)
    
    def adjustRemeshParameters(self, ReParams, numNaked, numFixed, history, tqc_min, tqc_max, gc_off):
        # make list for logging messages
        Logging = []
        
        # compute and update TQC minima and maxima
        mins = sorted([h[2] for h in history if h[2] != None])
        maxs = sorted([h[3] for h in history if h[3] != None])
        
        # if last result is below numfixed
        if numNaked < numFixed:
            if tqc_min == None:
                tqc_min = history[-1][0]
            else:
                if history[-1][0] > mins[-1]:
                    tqc_min = history[-1][0]
                else:
                    tqc_min = mins[-1]
        # if last result is above numfixed
        elif numNaked > numFixed:
            if tqc_max == None:
                tqc_max = history[-1][0]
            else:
                if history[-1][0] < maxs[0]:
                    tqc_max = history[-1][0]
                else:
                    tqc_max = maxs[0]
        
        # detect overshoots and undershoots as possible new min or max values
        if len(history) >= 2:
            # if last diff is positive and last-last diff is negative
            if (history[-1][1] > numFixed and history[-2][1] < numFixed):
                Logging.append("OVERSHOOT DETECTED")
                Logging.append(" ")
                if maxs != [] and history[-1][0] < maxs[0]:
                    tqc_max = history[-1][0]
            # if last diff is negative and las-last diff is positive
            elif (history[-1][1] < numFixed and history[-2][1] > numFixed):
                Logging.append("UNDERSHOOT DETECTED")
                Logging.append(" ")
                if mins != [] and history[-1][0] > mins[-1]:
                    tqc_min = history[-1][0]
        
        # compute difference between num of naked vertices and num of fixed pts
        diff = numNaked - numFixed
        
        # set current targetquadcpount to last targetquadcount
        tqc = ReParams.TargetQuadCount
        
        # eyeball something like a QPN value (quads per naked vertex)
        # silly approach but works quite well ;-)
        qpn = int(math.ceil(ReParams.TargetQuadCount / numNaked))
        
        # compute adjustment of remesh parameters
        adjustment = abs(diff) * qpn
        
        # if min and max has already been found
        if tqc_min and tqc_max:
            if abs(tqc_max - tqc_min) < 2:
                if gc_off == False:
                    gc_off = True
                    Logging.append("TURNING OFF GUIDECURVES...")
                    tqc_min = None
                    tqc_max = None
                elif gc_off == True:
                    gc_off = False
                    tqc_min = None
                    tqc_max = None
                    Logging.append("TURNING ON GUIDECURVES...")
            else:
                tqc = int(math.ceil(abs(tqc_min + tqc_max) / 2))
                adjustment = tqc - ReParams.TargetQuadCount
        else:
            # do something to decrease the number of naked vertices
            if diff > 0:
                tqc -= adjustment
            # do something to increase the number of naked vertices
            elif diff < 0:
                tqc += adjustment
        
        """
        # CODE FOR OLD ADJUSTMENTS
        
        if abs(diff) > 4 and abs(diff) <= 8:
            adjustment = int(qpn - (qpn % 2)) * abs(diff)
        elif abs(diff) > 1 and abs(diff) <= 4:
            adjustment = self.MINOR_ADJUSTMENT
        elif abs(diff) <= 1:
            adjustment = self.MICRO_ADJUSTMENT
        else:
            adjustment = abs(diff) * self.TQC_NVX_EQUIVALENT
        """
        
        # write everything to the log
        Logging.append("Quads/NakedPt:       " + str(qpn))
        Logging.append("Last TQC:            " + str(history[-1][0]))
        Logging.append("Last numNakedPts:    " + str(numNaked))
        Logging.append("Target numNakedPts:  " + str(numFixed))
        Logging.append(" ")
        Logging.append("numNaked Difference: " + str(diff))
        Logging.append("Adjustment Value:    " + str(adjustment))
        Logging.append("Next TQC:            " + str(tqc))
        Logging.append("TQC MIN:             " + str(tqc_min))
        Logging.append("TQC MAX:             " + str(tqc_max))
        
        # write new tqc to reparams
        ReParams.TargetQuadCount = tqc
        
        # return the whole salad
        return ReParams, Logging, tqc_min, tqc_max, gc_off
    
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
        
        # find out where the first point of SortedFixedPts appears
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
    
    def createRelaxationGoals(self, QuadMesh, EdgeLengthFactor):
        """
        creates a goals list for relaxation of the mesh
        """
        
        if QuadMesh == None:
            QuadMesh = Rhino.Geometry.Mesh()
        
        # get edges and naked vertices from the mesh
        edges = [QuadMesh.TopologyEdges.EdgeLine(i) for i in range(
                                            QuadMesh.TopologyEdges.Count)]
        nakedPts = self.getNakedVertices(QuadMesh, p3d=True)[1]
        
        # make goals list
        goals = []
        
        # make show goal for mesh
        wrappedMesh = Grasshopper.Kernel.Types.GH_ObjectWrapper()
        wrappedMesh.CastFrom(QuadMesh)
        g = ks.Goals.Locator(wrappedMesh)
        goals.append(g)
        
        # make edge goals and append to goals list
        for l in edges:
            tel = l.Length * EdgeLengthFactor
            g = ks.Goals.Spring(l.From, l.To, tel, 1.00)
            goals.append(g)
        
        # make anchors and append to goals list
        for pt in nakedPts:
            g = ks.Goals.Anchor(pt, 1000000)
            goals.append(g)
        
        return goals
    
    def remeshRoutine(self, dataPackage):
        
        Logging = []
        
        # unpack the dataPackage
        Geometry, \
        Branch, \
        FixedPts, \
        TargetQuadCount, \
        AdaptiveQuadCount, \
        AdaptiveSize, \
        DetectHardEdges,\
        GuideCurves, \
        GuideCurveInfluence, \
        SymmetryAxis, \
        PreserveMeshArrayEdgesMode, \
        MaxMeshingIterations, \
        AdjustQuadMesh, \
        RelaxQuadMesh = dataPackage
        
        # check data
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
            # return nothing if the check fails
            return None
        else:
            # unpack the result of the check
            Geometry, \
            FixedPts, \
            TargetQuadCount, \
            AdaptiveQuadCount, \
            AdaptiveSize, \
            DetectHardEdges,\
            GuideCurveInfluence, \
            SymmetryAxis, \
            PreserveMeshArrayEdgesMode = result
        
        # create QuadRemeshing Parameters based on input values
        ReParams = self.createRemeshParameters(TargetQuadCount,
                                               AdaptiveQuadCount,
                                               AdaptiveSize,
                                               DetectHardEdges,
                                               GuideCurveInfluence,
                                               SymmetryAxis,
                                               PreserveMeshArrayEdgesMode)
        
        # If MaxMeshingIterations is 0 return the first result
        if MaxMeshingIterations <= 0:
            Logging.append("-------------------------------------")
            QuadMesh = self.createRemeshedResult(Geometry,
                                                 ReParams,
                                                 GuideCurves)
            
            if not QuadMesh:
                Logging.append("QUADREMESH RETURNED NO RESULT!")
                if GuideCurves:
                    Logging.append("TRYING WITHOUT GUIDECURVES...")
                    Logging.append(" ")
                    QuadMesh = self.createRemeshedResult(Geometry,
                                                         ReParams,
                                                         None)
                if not QuadMesh:
                    Logging.append("TRYING WITH DOUBLE ITQC...")
                    ReParams.TargetQuadCount = ReParams.TargetQuadCount * 2
                    QuadMesh = self.createRemeshedResult(Geometry,
                                                              ReParams,
                                                              None)
                if not QuadMesh:
                    Logging.append("QUADREMESH RETURNED NO RESULT!")
                    Logging.append("SKIPPING...")
                    return [None]
            
            # get naked ids, vertices etc.
            NakedIDs, NakedPts, cIds, cPts = self.getNakedVertices(
                                                                QuadMesh,
                                                                p3d=True)
            
            # write status message to the log
            Logging.append("RETURNING FIRST RESULT FOR THIS MESH.")
            Logging.append(" ")
        
        # if MaxMeshingIterations is > 0 try to get a refined result
        else:
            numFixed = len(FixedPts)
            numNaked = None
            history = []
            iteration = 1
            solution = False
            tqc_min = None
            tqc_max = None
            gc_off = False
            
            while solution == False and iteration <= MaxMeshingIterations:
                # write status message to the log
                Logging.append("-------------------------------------")
                Logging.append("ITERATION " + str(iteration))
                Logging.append(" ")
                
                # listen for escape key and abort if pressed
                sc.escape_test()
                
                # create a quadremeshed result
                if gc_off == True:
                    currentResult = self.createRemeshedResult(Geometry,
                                                          ReParams,
                                                          None)
                elif gc_off == False:
                    currentResult = self.createRemeshedResult(Geometry,
                                                          ReParams,
                                                          GuideCurves)
                
                if not currentResult:
                    Logging.append("QUADREMESH RETURNED NO RESULT!")
                    if GuideCurves:
                        Logging.append("TRYING WITHOUT GUIDECURVES...")
                        currentResult = self.createRemeshedResult(Geometry,
                                                                  ReParams,
                                                                  None)
                    if not currentResult:
                        Logging.append("TRYING WITH DOUBLE ITQC...")
                        ReParams.TargetQuadCount = ReParams.TargetQuadCount * 2
                        currentResult = self.createRemeshedResult(Geometry,
                                                                  ReParams,
                                                                  None)
                    if not currentResult:
                        break
                
                # get naked ids, vertices, etc. of current result
                NakedIDs, NakedPts, cIds, cPts = self.getNakedVertices(
                                                                currentResult,
                                                                p3d=True)
                
                # if the number of naked points is identical to fixed points,
                # treat this as the solution
                numNaked = len(NakedPts)
                
                history.append((ReParams.TargetQuadCount, numNaked, tqc_min, tqc_max))
                
                # if numnaked equals numfixed, we have a solution
                if numNaked == numFixed:
                    # write status message to the log
                    Logging.append("TargetQuadCount: " + str(ReParams.TargetQuadCount))
                    Logging.append("NakedPts:        " + str(numNaked))
                    Logging.append("Difference:      " + str(numNaked-numFixed))
                    Logging.append(" ")
                    Logging.append("SOLUTION ACCEPTED - RETURNING RESULT.")
                    
                    iteration += 1
                    solution = True
                    break
                
                # adjust the remeshing parameters for the next iteration
                else:
                    ReParams, logs, tqc_min, tqc_max, gc_off = self.adjustRemeshParameters(ReParams,
                                                           numNaked,
                                                           numFixed,
                                                           history,
                                                           tqc_min,
                                                           tqc_max,
                                                           gc_off)
                    Logging.extend(logs)
                    iteration += 1
            
            if not currentResult:
                Logging.append("NO SOLUTION FOR THIS MESH.")
                Logging.append("SKIPPING...")
                rmlevel = Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning
                self.AddRuntimeMessage(rmlevel,
                    "Mesh at Branch " + str(Branch) + " did not return any solution.")
                return (None, None, None, None, Logging)
            
            # set RuntimeMessages
            if numNaked == numFixed:
                rmlevel = Grasshopper.Kernel.GH_RuntimeMessageLevel.Remark
                self.AddRuntimeMessage(rmlevel,
                    "Mesh at Branch " + str(Branch) + " was returned with " +
                    "the target number of naked vertices after " +
                    str(iteration) + " iterations." )
            else:
                rmlevel = Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning
                diff = numNaked-numFixed
                if diff > 0:
                    msgdiff = "+" + str(diff)
                else:
                    msgdiff = str(diff)
                self.AddRuntimeMessage(rmlevel,
                    "Mesh at Branch " + str(Branch) + " was returned with " +
                    msgdiff + " naked vertices compared to FixedPts after " + 
                    str(iteration-1) + " iterations!" )
            
            QuadMesh = currentResult
        
        # if AdjustQuadMesh is True call the respective function
        if AdjustQuadMesh and solution == True:
            AdjustedQuadMesh = self.adjustNakedPts(QuadMesh, FixedPts)
        else:
            AdjustedQuadMesh = None
        
        # return the outputs
        return (QuadMesh, AdjustedQuadMesh, NakedPts, NakedIDs, Logging)
    
    def RunScript(self, Geometry, FixedPts, InitialTargetQuadCount, AdaptiveQuadCount, AdaptiveSize, DetectHardEdges, GuideCurves, GuideCurveInfluence, SymmetryAxis, PreserveMeshArrayEdgesMode, MaxMeshingIterations, AdjustQuadMesh, RelaxQuadMesh, RelaxationEdgeLengthFactor, RelaxationIterations, RelaxationTolerance, Parallel):
        
        # define outputs so that they are never empty
        QuadMesh = []
        AdjustedQuadMesh = []
        RelaxedQuadMesh = []
        NakedPts = []
        NakedIDs = []
        Logging = []
        
        # CHECK TREE INPUTS ----------------------------------------------------
        
        # if no geometry is supplied, do nothing
        if not Geometry.DataCount:
            return (QuadMesh,
                    AdjustedQuadMesh,
                    RelaxedQuadMesh,
                    NakedPts,
                    NakedIDs,
                    Logging)
        
        # unpack input datatrees
        arrData = []
        for i, branch in enumerate(Geometry.Branches):
            # step through branches of geometry input and collect other inputs
            if len(branch) > 1:
                rmw = Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning
                self.AddRuntimeMessage(rmw,
                    "Please make sure that the 'Geometry' input has one Mesh" +
                    "per branch in a DataTree!")
            SingleGeometry = branch[0]
            
            # collect fixedpts input
            if FixedPts.DataCount:
                try:
                    if len(Geometry.Branches) > 1 and len(FixedPts.Branches) > 1:
                        fpts_branch = FixedPts.Branch(Geometry.Path(i))
                    else:
                        fpts_branch = FixedPts.Branch(FixedPts.Paths[0])
                except:
                    rmw = Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning
                    self.AddRuntimeMessage(rmw,
                        "Please make sure that the 'FixedPts' input has the " +
                        "same DataTree-structure as the 'Geometry' input " +
                        "(one or multiple fixedpts per branch in a DataTree)!")
            else:
                fpts_branch = None
            
            # collect initial target quad count input
            if InitialTargetQuadCount.DataCount:
                tqc_branch = InitialTargetQuadCount.Branch(Geometry.Path(i))
                if len(tqc_branch) > 1:
                    rmw = Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning
                    self.AddRuntimeMessage(rmw,
                        "Please make sure that the 'TargetQuadCount' input " +
                        "has the same DataTree-structure as the 'Geometry' " +
                        "input (one int value per branch in a DataTree)!")
                if InitialTargetQuadCount.DataCount == 1:
                    tqc_branch = InitialTargetQuadCount.Branch(
                                                InitialTargetQuadCount.Paths[0])
            
            # collect guidecurves input
            if GuideCurves.DataCount:
                try:
                    if len(Geometry.Branches) > 1 and len(GuideCurves.Branches) > 1:
                        gc_branch = list(GuideCurves.Branch(Geometry.Path(i)))
                    else:
                        gc_branch = list(GuideCurves.Branch(GuideCurves.Paths[0]))
                except:
                    rmw = Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning
                    self.AddRuntimeMessage(rmw,
                      "Please make sure that the 'GuideCurves' input has " +
                      "the same DataTree-structure as the 'Geometry' input " +
                      "(one or multiple guidecurves per branch in a DataTree)!")
                if not gc_branch:
                    rmw = Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning
                    self.AddRuntimeMessage(rmw,
                      "Please make sure that the 'GuideCurves' input has " +
                      "the same DataTree-structure as the 'Geometry' input " +
                      "(one or multiple guidecurves per branch in a DataTree)!")
            else:
                gc_branch = None
            
            # COMPILE DATAPACKAGE FOR PARALLEL EXECUTION -----------------------
            
            dataPackage = (SingleGeometry, \
                           Geometry.Path(i), \
                           fpts_branch, \
                           tqc_branch[0], \
                           AdaptiveQuadCount, \
                           AdaptiveSize, \
                           DetectHardEdges, \
                           gc_branch, \
                           GuideCurveInfluence, \
                           SymmetryAxis, \
                           PreserveMeshArrayEdgesMode, \
                           MaxMeshingIterations, \
                           AdjustQuadMesh, \
                           RelaxQuadMesh)
            
            arrData.append(dataPackage)
        
        if not arrData:
            return None
        
        # TRIGGER REMESHING AND COLLECT RESULTS --------------------------------
        
        if Parallel:
            results = list(GhPython.ScriptHelpers.Parallel.Run(
                                                           self.remeshRoutine,
                                                           arrData,
                                                           False))
        else:
            results = [self.remeshRoutine(d) for d in arrData]
        
        for i, result in enumerate(results):
            if result == None:
                result = [None, None, None, None, None]
            QuadMesh.append([result[0]])
            if AdjustQuadMesh:
                AdjustedQuadMesh.append([result[1]])
            NakedPts.append(result[2])
            NakedIDs.append(result[3])
            Logging.append(result[4])
        
        # RELAXTAION -----------------------------------------------------------
        
        if RelaxQuadMesh and RelaxationIterations and RelaxationIterations != 0:
            if not RelaxationTolerance:
                RelaxationTolerance = 0.01
            
            if not RelaxationEdgeLengthFactor:
                RelaxationEdgeLengthFactor = 0.00
            
            # create all relaxation goals
            if AdjustQuadMesh:
                allgoals = [g for goals in (self.createRelaxationGoals(qm[0], RelaxationEdgeLengthFactor) for qm in AdjustedQuadMesh) for g in goals]
            else:
                allgoals = [g for goals in (self.createRelaxationGoals(qm[0], RelaxationEdgeLengthFactor) for qm in QuadMesh) for g in goals]
            
            #create physical system and dotnet list of goals
            ps = ks.PhysicalSystem()
            goalsList = List[ks.IGoal]()
            
            # assign particle indices automatically
            for g in allgoals:
                ps.AssignPIndex(g, RelaxationTolerance)
                goalsList.Add(g)
            
            # solve k2 system
            for i in range(int(RelaxationIterations)):
                ps.Step(goalsList, False, 1000)
            
            # Get meshes
            RelaxedQuadMesh = []
            for o in ps.GetOutput(goalsList):
                if type(o) is not Rhino.Geometry.Point3d and o is not None and type(o) is not Rhino.Geometry.Line:
                    if str(o) == "Invalid Mesh":
                        RelaxedQuadMesh.append(None)
                        continue
                    RelaxedQuadMesh.append(o)
        
        # PREPARE RESULTS FOR OUTPUT -------------------------------------------
        
        QuadMesh = th.list_to_tree(QuadMesh, [0])
        AdjustedQuadMesh = th.list_to_tree(AdjustedQuadMesh, [0])
        RelaxedQuadMesh = th.list_to_tree(RelaxedQuadMesh, [0])
        NakedPts = th.list_to_tree(NakedPts, [0])
        NakedIDs = th.list_to_tree(NakedIDs, [0])
        Logging = th.list_to_tree(Logging, [0])
        
        # RETURN RESULTS -------------------------------------------------------
        return (QuadMesh,
                AdjustedQuadMesh,
                RelaxedQuadMesh,
                NakedPts,
                NakedIDs,
                Logging)
