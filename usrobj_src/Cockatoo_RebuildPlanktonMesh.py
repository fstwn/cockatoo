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
        License: MIT License
        Version: 200705
"""

# PYTHON LIBRARY IMPORTS
import clr
import os

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# COMPONENT SETTINGS
ghenv.Component.Name = "RebuildPlanktonMesh"
ghenv.Component.NickName = "RPM"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "02 Meshing & Remeshing"


# PLANKTON IMPORT
if "Plankton," in str(clr.References):
    import Plankton
else:
    try:
        if os.name == "nt":
            plankton_path = (os.path.expandvars("%userprofile%") + 
                             "/AppData/Roaming/"
                             "Grasshopper/Libraries/Plankton.dll")
            clr.AddReferenceToFileAndPath(os.path.normpath(plankton_path))
        elif os.name == "posix":
            plankton_path = ("/Library/Application Support/McNeel/Rhinoceros/"
                             "6.0/Plug-ins/Grasshopper (b45a29b1-4343-4035-"
                             "989e-044e8580d9cf)/Libraries/Plankton.dll")
            clr.AddReferenceToFileAndPath(os.path.normpath(plankton_path))
        import Plankton
    except (IOError, ImportError):
        raise RuntimeError("Plankton could not be imported! Please install it.")
if "PlanktonGh," in str(clr.References):
    import PlanktonGh
else:
    try:
        if os.name == "nt":
            planktongh_path = (os.path.expandvars("%userprofile%") + 
                               "/AppData/Roaming/"
                               "Grasshopper/Libraries/PlanktonGh.dll")
            clr.AddReferenceToFileAndPath(os.path.normpath(planktongh_path))
        elif os.name == "posix":
            planktongh_path = ("/Library/Application Support/McNeel/Rhinoceros/"
                               "6.0/Plug-ins/Grasshopper (b45a29b1-4343-4035-"
                               "989e-044e8580d9cf)/Libraries/PlanktonGh.dll")
            clr.AddReferenceToFileAndPath(os.path.normpath(planktongh_path))
        import PlanktonGh
    except (IOError, ImportError):
        raise RuntimeError("PlanktonGh could not be imported!"
                           "Please install it.")

class RebuildPlanktonMesh(component):
    
    def rebuild_mesh(self, Mesh, RebuildNormals, CullUnusedVertices, CullDegenerateFaces, CombineIdentical):
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
                    inputMesh = self.rebuild_mesh(inputMesh,
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
