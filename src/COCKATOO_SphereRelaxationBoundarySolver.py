"""Relaxes a bunch of points using sphere relaxation.
    Inputs:
        Run: If set to true, the relaxation process will run, if False it will Pause. {item, boolean}
        Reset: Will reset the relaxation if set to true. Connect a button here ideally. {item, boolean}
        Threshold: Stop when average movement is less than this (default is 1e-3). {item, float}
        Boundary: The boundary to keep the points in. {item, mesh}
        Points: The center points for the circle relaxation. {list, point}
        Distance: The distance the points should respect {item, float}
        BoundaryStrength: The momentum used for collisions with the boundary (ideally between 0.0 and 1.0). Default is 0.5 {item, float}
    Output:
        Iterations: The current number of iterations. {item, integer}
        RelaxedPoints: The relaxed points for every iteration {list, points}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200324
"""

# PYTHON MODULES IMPORTS
from __future__ import division

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# CUSTOM RHINO IMPORTS
import scriptcontext as sc

ghenv.Component.Name = "SphereRelaxationBoundarySolver"
ghenv.Component.NickName ="SRBS"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "9 Utilities"

class SphereRelaxationBoundarySolver(component):
    
    def RunScript(self, Run, Reset, Threshold, Boundary, Points, Distance, BoundaryStrength):
        
        def updateComponent():
            """Updates this component."""
            
            # Define callback action
            def callBack(e):
                self.ExpireSolution(False)
                
            # Get grasshopper document
            ghDoc = self.OnPingDocument()
            
            # Schedule this component to expire
            ghDoc.ScheduleSolution(1, Grasshopper.Kernel.GH_Document.GH_ScheduleDelegate(callBack))
        
        # define sticky keys for persistent data storage
        iguid = str(self.InstanceGuid)
        ckey = iguid + "__Centers"
        rkey = iguid + "__Converged"
        ikey = iguid + "__Iterations"
        
        # define reset condition
        if Reset or not ckey in sc.sticky or not rkey in sc.sticky or not ikey in sc.sticky:
            ghenv.Component.Message = "Reset"
            sc.sticky[ckey] = Points[:]
            sc.sticky[rkey] = False
            sc.sticky[ikey] = 0
        
        # set default value for threshold
        if not Threshold:
            Threshold = 1e-3
        
        # define boundary strength default
        if not BoundaryStrength:
            BoundaryStrength = 0.5
        
        # run condition
        if Run and not sc.sticky[rkey]:
            ghenv.Component.Message = "Running"
            # define lists for storage of moves and collisions
            totalMoves = []
            collisionCounts = []
            
            # get current centerpoints from sticky
            centers = sc.sticky[ckey]
            
            if Boundary and type(Boundary) is Rhino.Geometry.Mesh:
                Boundary.UnifyNormals()
                Boundary.Normals.ComputeNormals()
            
            # fill moves and collision list with empty values
            for i, c in enumerate(centers):
                totalMoves.append(Rhino.Geometry.Vector3d(0, 0, 0))
                collisionCounts.append(0.0)
            
            # loop through pairs of centerpoints
            for i in range(len(centers)):
                j = i+1
                # test for boundary containment
                if Boundary:
                    if not Boundary.IsClosed:
                        bclsd = False
                        rml = Grasshopper.Kernel.GH_RuntimeMessageLevel.Warning
                        self.AddRuntimeMessage(rml, "Boundary is not " +
                            "closed! This operation only makes sense " + 
                            "with closed boundaries. Ignoring Boundary...")
                    else:
                        bclsd = True
                    ipi = Boundary.IsPointInside(centers[i],
                        Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance, False)
                    if type(Boundary) is Rhino.Geometry.Mesh and bclsd:
                        bcp = Boundary.ClosestMeshPoint(centers[i], Distance * 0.5)
                        if bcp:
                            normal = Boundary.NormalAt(bcp.FaceIndex, *bcp.T)
                            bcp = bcp.Point
                    if bcp and bclsd:
                        bd = centers[i].DistanceTo(bcp)
                        bmove = normal
                        bmove.Unitize()
                        bmove = bmove * 0.5 * ((Distance * BoundaryStrength) - bd)
                        bmove.Reverse()
                        totalMoves[i] += bmove
                        collisionCounts[i] += 1.0
                
                while j < len(centers):
                    sc.escape_test()
                    d = centers[i].DistanceTo(centers[j])
                    
                    # only proceed if distance is smaller than the set limit
                    if d > Distance:
                        j += 1
                        continue
                    
                    # define moves, collisions and add them to lists
                    move = centers[i] - centers[j]
                    move.Unitize()
                    move = move * 0.5 * (Distance - d)
                    totalMoves[i] += move
                    totalMoves[j] -= move
                    collisionCounts[i] += 1.0
                    collisionCounts[j] += 1.0
                    # increment counter
                    j += 1
            
            # execute alle the moves
            for i, c in enumerate(centers):
                if collisionCounts[i] != 0.0:
                    centers[i] += totalMoves[i] / collisionCounts[i]
            
            # write the moved center points to the sticky
            sc.sticky[ckey] = centers
            
            # get velocity of all particles
            totalvelocity = 0
            for i, v in enumerate(totalMoves):
                totalvelocity += v.Length
            if totalvelocity <= Threshold:
                sc.sticky[rkey] = True
            
            # set iteration counter in sticky
            sc.sticky[ikey] += 1
            
            # update the component
            updateComponent()
        
        # set message if solver is converged
        elif sc.sticky[rkey]:
            ghenv.Component.Message = "Converged"
        # if solver is not running and not converged, set pause message
        else:
            ghenv.Component.Message = "Paused"
        
        # define the outputs
        Iterations = sc.sticky[ikey]
        
        if Iterations > 0:
            RelaxedPoints = sc.sticky[ckey]
        else:
            RelaxedPoints = Points
        
        # return outputs if you have them; here I try it for you:
        return (Iterations, RelaxedPoints)
