"""
Attempts to relax a mesh into a plane to make it planar. The best fit plane
is used for reference and updated at every iteration
    Inputs:
        Run: If set to true, the relaxation process will run, if False it will
             Pause. {item, boolean}
        Reset: Will reset the relaxation if set to true. Connect a button here,
               ideally. {item, boolean}
        Threshold: Stop when average movement is less than this
                   (default is 1e-3). {item, float}
        Mesh: The mesh to attempt planarization for. {item, mesh}
        GlobalPlaneStrength: Strength of the movement towards the global plane
                             {list, point}
        LocalPlaneStrength: Strength of the movement towards the local planes.
                            {item, float}
        EdgeLengthStrength: Strength with which edgelengths are preserved.
                            {item, float}
    Output:
        Iterations: The current number of iterations. {item, integer}
        RelaxedMesh: The relaxed mesh for every iteration {list, points}
        GlobalFitPlane: The best fit plane of the mesh {item, plane}
        LocalFitPlanes: All the local planes used in the planarization attempt.
                        {list, plane}
        AveragePlaneDeviation: Average deviation between the vertices of the
                               mesh and the globally fit plane. {item, float}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200525
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division
import clr
import math

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# CUSTOM RHINO IMPORTS
from ghpythonlib import treehelpers as th
from scriptcontext import escape_test
from scriptcontext import sticky as st

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "RelaxMeshIntoPlane"
ghenv.Component.NickName ="RMIP"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "9 Utilities"

class RelaxMeshIntoPlane(component):
    
    def updateComponent(self):
        """Updates this component in a safe way."""
        # define callback action
        def callBack(e):
            self.ExpireSolution(False)
        # get ghDoc
        ghDoc = self.OnPingDocument()
        # schedule new solution
        ghDoc.ScheduleSolution(1, 
                   Grasshopper.Kernel.GH_Document.GH_ScheduleDelegate(callBack))
    
    def TweenPlanes(self, P1, P2, t):
        """Tweens between two planes using quaternion rotation."""
        Q = Rhino.Geometry.Quaternion.Rotation(P1, P2)
        
        # prepare out parameters
        qAngle = clr.Reference[System.Double]()
        qAxis = clr.Reference[Rhino.Geometry.Vector3d]()
        
        # get the rotation of the quaternion
        Q.GetRotation(qAngle, qAxis)
        
        axis = Rhino.Geometry.Vector3d(qAxis.X, qAxis.Y, qAxis.Z)
        angle = float(qAngle) - 2 * math.pi if float(qAngle) > math.pi else float(qAngle)
        
        OutputPlane = P1.Clone()
        OutputPlane.Rotate(t * angle, axis, OutputPlane.Origin)
        Translation = Rhino.Geometry.Vector3d(P2.Origin - P1.Origin)
        OutputPlane.Translate(Translation * t)
        
        return OutputPlane
    
    def _compute_local_plane_indices(self, TopologyVertexList, vIndex, Depth):
        """
        Computes the vertex indices for local plane interpolation up to
        a given depth.
        """
        
        if Depth < 1:
            return None
        vertices = list(TopologyVertexList)
        next = [vIndex]
        ci = []
        for i in range(Depth):
            for vi in next[:]:
                this = list(TopologyVertexList.ConnectedTopologyVertices(vi))
                ci.extend(this)
                next = this
        ci.append(vIndex)
        return ci
    
    def ComputeLocalPlanes(self, Mesh, Depth=1):
        vertices = list(Mesh.Vertices.ToPoint3dArray())
        LocalPlanes = []
        for i, vertex in enumerate(vertices):
            # get indices for vertices included in local plane
            lpi = self._compute_local_plane_indices(Mesh.TopologyVertices,
                                                   i,
                                                   Depth)
            # get thee points from the vertexlist
            lpts = [vertices[x] for x in lpi]
            
            # fit plane to set of points
            suc, lfp = Rhino.Geometry.Plane.FitPlaneToPoints(lpts)
            if suc != Rhino.Geometry.PlaneFitResult.Success:
                rml = self.RuntimeMessageLevel.Error
                self.AddRuntimeMessage(rml,
                              "Could not fit local plane through meshpoints...")
                return None
            
            # compute average vertex for plane translation
            avgVx = lpts[0]
            for j, v in enumerate(lpts[1:]):
                avgVx += v
            avgVx = avgVx / len(lpts)
            avgPCP = lfp.ClosestPoint(vertices[i])
            lfp.Origin = avgPCP
            
            # align local plane with mesh normal
            dp = lfp.Normal * Rhino.Geometry.Vector3d(Mesh.Normals[i])
            if dp < 0:
                lfp.Flip()
            
            # append to list of local planes
            LocalPlanes.append(lfp)
        return LocalPlanes
    
    def ComputeMoves(self, Mesh, vertices, GlobalFitPlane, GlobalPlaneStrength, LocalPlaneStrength, EdgeLengthStrength, lKey, eKey):
        """
        Compute the moves and collision counts for a given set of vertices.
        """
        
        # define lists for storage of moves and collisions
        totalMoves = []
        collisionCounts = []
        
        # fill moves and collision list with empty values
        for i, vertex in enumerate(vertices):
            totalMoves.append(Rhino.Geometry.Vector3d(0, 0, 0))
            collisionCounts.append(0.0)
        
        # loop through all vertices
        for i, vertex in enumerate(vertices):
            # get all the connected vertices
            ci = list(Mesh.TopologyVertices.ConnectedTopologyVertices(i))
            connectedpts = [vertices[idx] for idx in ci]
            
            # COMPUTE MOVE FOR GLOBAL PLANE FITTING ----------------------------
            gpd = GlobalFitPlane.DistanceTo(vertices[i])
            if abs(gpd) > 0:
                gplnmove = GlobalFitPlane.Normal
                gplnmove.Unitize()
                # implementation detail: vector has to be reversed to move point
                # in the direction of the plane
                gplnmove.Reverse()
                gplnmove = gplnmove * gpd * GlobalPlaneStrength
                totalMoves[i] += gplnmove
                collisionCounts[i] += 1.0
            
            # COMPUTE MOVE FOR LOCAL PLANE FITTING
            LocalFitPlane = st[lKey][i]
            lpd = LocalFitPlane.DistanceTo(vertices[i])
            if abs(lpd) > 0:
                lplnmove = LocalFitPlane.Normal
                lplnmove.Unitize()
                # implementation detail: vector has to be reversed to move point
                # in the direction of the plane
                lplnmove.Reverse()
                lplnmove = lplnmove * lpd * LocalPlaneStrength
                totalMoves[i] += lplnmove
                collisionCounts[i] += 1.0
            
            # COMPUTE MOVE FOR EDGELENGTH PRESERVATION -------------------------
            for j, cpt in enumerate(connectedpts):
                # distance to connected point
                cd = vertices[i].DistanceTo(cpt)
                od = st[eKey][i][j]
                
                # compute delta
                delta = od - cd
                if abs(delta) > 0:
                    # define moves, collisions and add them to lists
                    move = vertices[i] - cpt
                    move.Unitize()
                    move = move * delta * EdgeLengthStrength
                    totalMoves[i] += move
                    totalMoves[ci[j]] -= move
                    collisionCounts[i] += 1.0
                    collisionCounts[ci[j]] += 1.0
        
        return totalMoves, collisionCounts
    
    def ComputeQuaternionMoves(self, Mesh, vertices, GlobalFitPlane, GlobalPlaneStrength, LocalPlaneStrength, EdgeLengthStrength, lKey, eKey):
        """Computes the move susing quaternion rotation augmentation"""
        
        # define lists for storage of moves and collisions
        totalMoves = []
        collisionCounts = []
        
        # fill moves and collision list with empty values
        for i, vertex in enumerate(vertices):
            totalMoves.append(Rhino.Geometry.Vector3d(0, 0, 0))
            collisionCounts.append(0.0)
        
        # loop through all vertices
        for i, vertex in enumerate(vertices):
            # get all the connected vertices
            ci = list(Mesh.TopologyVertices.ConnectedTopologyVertices(i))
            connectedpts = [vertices[idx] for idx in ci]
            
            # COMPUTE MOVE FOR GLOBAL PLANE FITTING ----------------------------
            gpd = GlobalFitPlane.DistanceTo(vertices[i])
            gplnmove = GlobalFitPlane.Normal
            gplnmove.Unitize()
            # implementation detail: vector has to be reversed to move point
            # in the direction of the plane
            gplnmove.Reverse()
            gplnmove = gplnmove * gpd * GlobalPlaneStrength
            
            # COMPUTE MOVE FOR LOCAL PLANE FITTING -----------------------------
            LocalFitPlane = st[lKey][i]
            lpd = LocalFitPlane.DistanceTo(vertices[i])
            lplnmove = LocalFitPlane.Normal
            lplnmove.Unitize()
            # implmentation detail: vector has to be reversed to move point
            # in the direction of the plane
            lplnmove.Reverse()
            lplnmove = lplnmove * lpd * LocalPlaneStrength
            
            # COMPUTE TWEENED PLANE FROM GLOBAL AND LOCAL PLANE ----------------
            QuaternionPlane = self.TweenPlanes(GlobalFitPlane, st[lKey][i], 0.5)
            
            qpd = QuaternionPlane.DistanceTo(vertices[i])
            qplnmove = QuaternionPlane.Normal
            qplnmove.Unitize()
            qplnmove.Reverse()
            qplnmove = qplnmove * lpd * LocalPlaneStrength
            
            # ADD MOVE TO MOVESLIST FOR BOTH PLANE MOVES -----------------------
            totalMoves[i] += gplnmove + lplnmove + qplnmove
            collisionCounts[i] += 1.0
            
            # COMPUTE MOVE FOR EDGELENGTH PRESERVATION -------------------------
            for j, cpt in enumerate(connectedpts):
                # distance to connected point
                cd = vertices[i].DistanceTo(cpt)
                od = st[eKey][i][j]
                
                # compute delta
                delta = od - cd
                
                # define moves, collisions and add them to lists
                move = vertices[i] - cpt
                move.Unitize()
                move = move * delta * EdgeLengthStrength
                totalMoves[i] += move
                totalMoves[ci[j]] -= move
                collisionCounts[i] += 1.0
                collisionCounts[ci[j]] += 1.0
        
        return totalMoves, collisionCounts
    
    def RunScript(self, Run, Reset, Threshold, Mesh, LocalPlaneDepth, GlobalPlaneStrength, LocalPlaneStrength, EdgeLengthStrength):
        
        PLANEMODE = 0
        
        # DEFINE STICKY KEYS FOR STORAGE OF PERISTENT DATA BETWEEN ITERATIONS --
        ig = str(self.InstanceGuid)
        vKey = ig + "___VERTICES"
        eKey = ig + "___ORIGINALEDGELENGTHS"
        lKey = ig + "___LOCALVIEWPLANES"
        cKey = ig + "___CONVERGED"
        iKey = ig + "___ITERATIONS"
        
        # MESH INPUT CHECKING --------------------------------------------------
        if not Mesh:
            rml = Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, "Missing Mesh input...")
            return None
        elif Mesh.IsClosed:
            rml = Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, "Boundary is " +
                "closed! This operation only makes sense " + 
                "with open meshes....")
            return None
        
        # DEFAULT VALUES -------------------------------------------------------
        # set default value for threshold
        if not Threshold:
            Threshold = 1e-3
        
        # define global plane strength default
        if GlobalPlaneStrength == None:
            GlobalPlaneStrength = 0.25
        
        # define local plane strength default
        if LocalPlaneStrength == None:
            LocalPlaneStrength = 0.75
        
        # strength for edgelength preservation
        if EdgeLengthStrength == None:
            EdgeLengthStrength = 0.5
        
        # RESET HANDLING AND INITIALIZATION ------------------------------------
        if Reset or (not vKey in st or
                     not eKey in st or
                     not lKey in st or
                     not cKey in st or
                     not iKey in st) or st[iKey] == 0:
            self.Message = "Reset"
            st[vKey] = None
            st[eKey] = None
            st[lKey] = None
            st[cKey] = None
            st[iKey] = 0
            
            # initialize vertices
            st[vKey] = list(Mesh.Vertices.ToPoint3dArray())
            
            # initialize original edgelengths
            originaledgelengths = []
            for i, v in enumerate(st[vKey]):
                ci = list(Mesh.TopologyVertices.ConnectedTopologyVertices(i))
                cd = [v.DistanceTo(cv) for cv in [st[vKey][j] for j in ci]]
                originaledgelengths.append(cd)
            if originaledgelengths:
                st[eKey] = originaledgelengths
            
        # PAUSED CONDITION -----------------------------------------------------
        elif not Run and cKey in st and st[cKey] == False:
            ghenv.Component.Message = "Paused"
        # CONVERGED CONDITION
        elif cKey in st and st[cKey] == True:
            ghenv.Component.Message = "Converged"
        
        vertices = st[vKey]
        EdgeLengths = st[eKey]
        Iterations = st[iKey]
        
        # CREATE RELAXED MESH OUTPUT -------------------------------------------
        RelaxedMesh = Mesh.Duplicate()
        for i, vertex in enumerate(st[vKey]):
            RelaxedMesh.Vertices.SetVertex(i, vertex)
        
        # COMPUTE AVERAGE MESH NORMAL ------------------------------------------
        meshnormals = RelaxedMesh.Normals
        avgNormal = Rhino.Geometry.Vector3d(meshnormals[0])
        for i, normal in enumerate(meshnormals):
            if i == 0:
                continue
            avgNormal += Rhino.Geometry.Vector3d(normal)
        avgNormal = avgNormal / len(meshnormals)
        avgNormal.Unitize
        
        # COMPUTE AVERAGE MESH VERTEX ------------------------------------------
        avgMvx = vertices[0]
        for i, v in enumerate(vertices[1:]):
            avgMvx += v
        avgMvx = avgMvx / len(vertices)
        
        # BUILD GLOBAL PLANE FROM AVERAGE MESH NORMAL AND VERTEX ---------------
        GlobalFitPlane = Rhino.Geometry.Plane(avgMvx, avgNormal)
        
        # BUILD LOCALFITPLANES -------------------------------------------------
        if lKey in st and st[lKey] != None and st[iKey] > 0:
            LocalFitPlanes = st[lKey]
        elif lKey in st and st[lKey] == None:
            LocalFitPlanes = self.ComputeLocalPlanes(Mesh, LocalPlaneDepth)
            st[lKey] = LocalFitPlanes
        
        # RUN CONDITION --------------------------------------------------------
        if Run and not st[cKey]:
            # set message to component
            self.Message = "Running"
            
            LocalFitPlanes = self.ComputeLocalPlanes(RelaxedMesh,
                                                     LocalPlaneDepth)
            st[lKey] = LocalFitPlanes
            
            # COMPUTATION OF MOVES ---------------------------------------------
            if PLANEMODE == 0:
                totalMoves, collisionCounts = self.ComputeMoves(RelaxedMesh,
                                                                vertices,
                                                                GlobalFitPlane,
                                                                GlobalPlaneStrength,
                                                                LocalPlaneStrength,
                                                                EdgeLengthStrength,
                                                                lKey,
                                                                eKey)
            elif PLANEMODE == 1:
                totalMoves, collisionCounts = self.ComputeQuaternionMoves(RelaxedMesh,
                                                                vertices,
                                                                GlobalFitPlane,
                                                                GlobalPlaneStrength,
                                                                LocalPlaneStrength,
                                                                EdgeLengthStrength,
                                                                lKey,
                                                                eKey)
            
            # EXECTUTION OF MOVES ----------------------------------------------
            for i, c in enumerate(vertices):
                if collisionCounts[i] != 0.0:
                    st[vKey][i] += totalMoves[i] / collisionCounts[i]
                    RelaxedMesh.Vertices.SetVertex(i, st[vKey][i])
            
            # PARTICLE VELOCITY ------------------------------------------------
            totalvelocity = 0
            for i, v in enumerate(totalMoves):
                totalvelocity += v.Length
            if totalvelocity <= Threshold:
                st[cKey] = True
            else:
                st[cKey] = False
            
            # set iteration counter in sticky
            st[iKey] += 1
            
            # update the component
            self.updateComponent()
        
        # DEFINE OUTPUTS -------------------------------------------------------
        
        # LocalFitPlanes
        LocalFitPlanes = th.list_to_tree(st[lKey])
        
        # AveragePlaneDeviation
        AveragePlaneDeviation = 0
        for i, vertex in enumerate(st[vKey]):
            AveragePlaneDeviation += abs(GlobalFitPlane.DistanceTo(vertex))
        AveragePlaneDeviation = AveragePlaneDeviation / len(st[vKey])
        
        # return outputs if you have them; here I try it for you:
        return (Iterations,
                RelaxedMesh,
                GlobalFitPlane,
                LocalFitPlanes,
                AveragePlaneDeviation)