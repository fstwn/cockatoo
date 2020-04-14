"""
Utility functions for writing GHPython scripts
Author: Max Eschenbach
License: Apache License 2.0
Version: 200414
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import absolute_import
from __future__ import division
from collections import deque

# RHINO IMPORTS
import Rhino
import scriptcontext

from .helpers import escapeFilePath, removeTrailingNewlines

def loadOBJ(filepath):
    """Reads from an *.obj file and returns a Rhino mesh"""
    # create a new, empty Rhino mesh
    model = Rhino.Geometry.Mesh()
    # read from the file in text mode
    with open(filepath, "rt") as f:
        while True:
            scriptcontext.escape_test()

            # read a line and split it into parts
            line = f.readline()
            if not line:
                break

            # split the line into parts
            parts = str.split(line, " ")
            token = parts[0]
            data = parts[1:]

            # catch empty line as delimiter
            if not parts or parts == [""]:
                continue

            # catch vertices
            elif token == "v":
                # add vertex
                vx, vy, vz = [float(c) for c in data]
                vertex = Rhino.Geometry.Point3f(vx, vy, vz)
                model.Vertices.Add(vertex)

            # catch faces
            elif token == "f":
                # add face
                if len(data) == 3:
                    # implementation detail: Rhino vertex indices are 0-based
                    va, vb, vc = [int(i)-1 for i in data]
                    model.Faces.AddFace(va, vb, vc)
                elif len(data) == 4:
                    # implementation detail: Rhino vertex indices are 0-based
                    va, vb, vc, vd = [int(i)-1 for i in data]
                    model.Faces.AddFace(va, vb, vc, vd)
    return model

def saveOBJ(mesh, filepath):
    """Saves a Rhino mesh as an *.obj file."""
    # run some checks on the input
    if not mesh or type(mesh) is not Rhino.Geometry.Mesh:
        raise ValueError("Supplied mesh is not a valid Rhino mesh!")
    if not filepath or type(filepath) is not str:
        raise ValueError("Supplied filepath is not a valid filepath!")

    # remove trailing newlines from the filepath and check for file extension
    filepath = escapeFilePath(removeTrailingNewlines(filepath))
    if not filepath.lower().endswith(".obj"):
        filepath = filepath + ".obj"

    # extract vertex coordinates from the mesh and build strings
    mv = list(mesh.Vertices.ToPoint3dArray())
    vertices = ["v {} {} {}\n".format(v.X, v.Y, v.Z) for v in mv]

    # extract faces from the mesh and build obj strings
    fids = deque(mesh.Faces.ToIntArray(False))
    temp = deque()
    faces = deque()
    while len(fids) > 0:
        scriptcontext.escape_test()
        # if face is complete, check if it is a triangle, append and reset temp
        if temp and len(temp) == 4:
            if temp[-2] == temp[-1]:
                temp.pop()
            faces.append(("f" + (" {}" * len(temp)) + "\n").format(*temp))
            temp.clear()
        else:
            # standard procedure - just add index to temp
            temp.append(fids.popleft() + 1)
    else:
        # handle trailing face at the end
        if len(temp) > 0:
            faces.append(("f" + (" {}" * len(temp)) + "\n").format(*temp))
            temp.clear()

    # open the file and write all the collected data to it
    with open(filepath, "wt") as f:
        # write the header to the file
        f.write("# Rhino Grasshopper OBJ exporter by Max Eschenbach\n")
        f.write("\n")
        f.write("# Mesh Vertices\n")
        f.writelines(vertices)
        f.write("\n")
        f.write("# Mesh Faces\n")
        f.writelines(faces)
