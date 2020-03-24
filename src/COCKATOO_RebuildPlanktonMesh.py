"""
Rebuilds the input mesh based on a variety of parameters using Plankton.
TODO: Update docstring
    Inputs:
        RebuildNormals: {item, boolean}
        CullUnusedVertices: {item, boolean}
        CullDegenerateFaces: {item, boolean}
        CombineIdentical: {item, boolean}
        MendMeshHoles: {item, boolean}
    Output:
        PMesh: The result as Plankton Mesh {tree, mesh}
        GHMesh: The result as Grasshopper Mesh {tree, mesh}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200324
"""

# PYTHON LIBRARY IMPORTS
import clr

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# CUSTOM MODULE IMPORTS
clr.AddReferenceToFile("Plankton.dll")
clr.AddReferenceToFile("PlanktonGh.dll")
import Plankton
import PlanktonGh

ghenv.Component.Name = "RebuildPlanktonMesh"
ghenv.Component.NickName = "RPM"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "3 Remeshing"

class RebuildPlanktonMesh(component):
    
    def RebuildMesh(self, Mesh, RebuildNormals, CullUnusedVertices, CullDegenerateFaces, CombineIdentical):
        """
        Rebuilds a mesh based on certain input parameters.
        """
        
        # rebuild normals if requested
        if Mesh and RebuildNormals:
            res = Mesh.Normals.ComputeNormals()
        
        # cull unused vertices from input mesh
        if Mesh and CullUnusedVertices:
            res = Mesh.Vertices.CullUnused()
        
        # cull duplicate faces
        if Mesh and CullDegenerateFaces:
            res = Mesh.Faces.ExtractDuplicateFaces()
            res = Mesh.Faces.CullDegenerateFaces()
        
        # combine identical vertices
        if Mesh and CombineIdentical:
            res = Mesh.Vertices.CombineIdentical(False, True)
        
        return Mesh
    
    def RunScript(self, Mesh, RebuildNormals, CullUnusedVertices, CullDegenerateFaces, CombineIdentical, MendMeshHoles):
        
        PMesh = Grasshopper.DataTree[object]()
        GHMesh = Grasshopper.DataTree[object]()
        
        if Mesh and Mesh.DataCount and list(Mesh.AllData()) != [None]:
            for i, branch in enumerate(list(Mesh.Branches)):
                for j, item in enumerate(list(branch)):
                    inputMesh = item
                    
                    if str(type(inputMesh)) == "<type 'PlanktonMesh'>":
                        inputMesh = PlanktonGh.RhinoSupport.ToRhinoMesh(inputMesh)
            
                    # get mesh vertexlist from mesh
                    MVL = inputMesh.Vertices
                    
                    # rebuild the mesh according to the input parameters
                    inputMesh = self.RebuildMesh(inputMesh,
                                                 RebuildNormals,
                                                 CullUnusedVertices,
                                                 CullDegenerateFaces,
                                                 CombineIdentical)
                    
                    # get vertices as points
                    V = [MVL[x] for x in range(MVL.Count)]
                    
                    # Create PlanktonMesh
                    newPMesh = Plankton.PlanktonMesh()
                    # create plankton points
                    pxyz = [Plankton.PlanktonXYZ(v.X, v.Y, v.Z) for v in V]
                    # add pxyz objects to pmesh vertexlist
                    newPMesh.Vertices.AddVertices(pxyz)
                    
                    # make ghtype and objectwrapper for outputting to gh
                    newPMesh = PlanktonGh.RhinoSupport.ToPlanktonMesh(inputMesh)
                    newGHMesh = PlanktonGh.RhinoSupport.ToRhinoMesh(newPMesh)
                    newPMesh = PlanktonGh.GH_PlanktonMesh(newPMesh)
                    newPMesh = Grasshopper.Kernel.Types.GH_ObjectWrapper(newPMesh)
                    
                    PMesh.Add(newPMesh, Mesh.Paths[i])
                    GHMesh.Add(newGHMesh, Mesh.Paths[i])
        
        # return outputs if you have them; here I try it for you:
        return (PMesh, GHMesh)
