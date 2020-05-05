"""
Static functions for loading and writing autoknit constraints from and to
*.cons files aswell as reading and writing *.obj files.
Author: Max Eschenbach
Version: 200414
"""

# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from collections import deque
import itertools
from os import path

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from Cockatoo.Environment import IsRhinoInside
from Cockatoo.Autoknit import Structs
from Cockatoo.Autoknit.Constraint import Constraint

# RHINO IMPORTS ----------------------------------------------------------------
if IsRhinoInside():
    import rhinoinside
    rhinoinside.load()
    from Rhino.Geometry import Mesh as RhinoMesh
    from Rhino.Geometry import Point3f as RhinoPoint3f
else:
    from Rhino.Geometry import Mesh as RhinoMesh
    from Rhino.Geometry import Point3f as RhinoPoint3f

# ALL DICTIONARY ---------------------------------------------------------------
__all__ = [
    "LoadConstraints",
    "SaveConstraints",
    "InterpretStoredConstraints",
    "LoadObj",
    "SaveObj"
]

# READ AND WRITE FUNCTIONS (PRIVATE) -------------------------------------------

# SCALARS ----------------------------------------------------------------------

def _read_scalar(instream, name):
    """Reads a scalar from the stream and returns it as an integer."""
    try:
        s = instream.read(Structs.STRUCT_SCALAR.size)
        scalar = Structs.STRUCT_SCALAR.unpack(s)[0]
        return scalar
    except Exception, e:
        raise RuntimeError("Failed to read scalar " + \
                           "{} // {}".format(name, str(e)))

def _write_scalar(outstream, scalar, name):
    """Writes a scalar to the output stream."""
    try:
        s = Structs.STRUCT_SCALAR.pack(scalar)
        outstream.write(s)
        return True
    except Exception, e:
        raise RuntimeError("Failed to write scalar " + \
                           "{} // {}".format(name, e))

# VECTORS ----------------------------------------------------------------------

def _read_vector(instream, structure, name):
    """Reads a vector from the instream and returns it as a tuple."""
    try:
        v = instream.read(structure.size)
        vector = structure.unpack(v)
        return vector
    except Exception, e:
        raise RuntimeError("Failed to read vector " + \
                           "{} // {}".format(name, str(e)))

def _write_vector(outstream, vector, structure, name):
    """Writes a vector to the output stream."""
    try:
        v = structure.pack(*vector)
        outstream.write(v)
        return True
    except Exception, e:
        raise RuntimeError("Failed to write vector " + \
                           "{} // {}".format(name, e))

# VECTOR SEQUENCES -------------------------------------------------------------

def _read_vector_sequence(instream, structure, name):
    """Reads a sequence of vectors from the stream using the given structure."""
    try:
        count = _read_scalar(instream, name + " count")
        vectors = [_read_vector(instream,
                                structure,
                                name + " {}".format(i)) for i in range(count)]
        return vectors
    except Exception, e:
        raise RuntimeError("Failed to read vector sequence " + \
                           "{} // {}".format(name, str(e)))

def _write_vector_sequence(outstream, sequence, structure, name):
    """Writes a sequence of vectors to the stream using the given structure."""
    try:
        count = len(sequence)
        _write_scalar(outstream, count, name + " count")
        for i, v in enumerate(sequence):
            _write_vector(outstream, v, structure, name + " {}".format(str(i)))
        return True
    except Exception, e:
        raise RuntimeError("Failed to write vector sequence " + \
                           "{} // {}".format(name, str(e)))

# LOADING AND SAVING OF CONSTRAINTS (PUBLIC) -----------------------------------

def LoadConstraints(filepath):
    """Loads autoknit constraints from a binary *.cons file."""
    with open(filepath, "rb") as f:
        try:
            vertices = _read_vector_sequence(f, Structs.STRUCT_VERTEX,
                                             "vertices")
            constraints = _read_vector_sequence(f, Structs.STRUCT_STOREDCONSTRAINT,
                                                "constraints")
            return True, vertices, constraints
        except Exception, e:
            print(e)
            return False, e

def SaveConstraints(filepath, vertices, constraints):
    """Saves constraints to a binary *.cons file compatible with autoknit."""
    try:
        with open(filepath, "wb") as f:
            vertices = list(itertools.chain.from_iterable(vertices))
            _write_vector_sequence(f, vertices, Structs.STRUCT_VERTEX, "vertices")

            constraints = [c.Storable for c in constraints]
            _write_vector_sequence(f, constraints, Structs.STRUCT_STOREDCONSTRAINT, "constraints")
    except Exception, e:
        print(e)
        raise RuntimeError("Could not write constraints file!")

# INTERPRETATION OF SAVED CONSTRAINTS ------------------------------------------

def InterpretStoredConstraints(points, storedconstraints):
    """Interprets the results of loading a *.cons file and builds
    Autoknit Constraints from them."""
    points = deque(points)
    constraints = []
    for i, c in enumerate(storedconstraints):
        vertices = [points.popleft() for x in range(c.Count)]
        constraints.append(Constraint(i, vertices, c.Value, c.Radius))
    return constraints

# LOADING AND SAVING OF MODELS (OBJ FILES) -------------------------------------

def LoadObj(filepath):
    """Reads from an *.obj file and returns a mesh"""
    # create a new, empty Rhino mesh
    model = RhinoMesh()
    # read from the file in text mode
    with open(filepath, "rt") as f:
        while True:
            #scriptcontext.escape_test()

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
                vertex = RhinoPoint3f(vx, vy, vz)
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

def SaveObj(filepath, mesh):
    """Saves a Rhino mesh as an *.obj file."""
    # run some checks on the input
    if not mesh or type(mesh) is not RhinoMesh:
        raise ValueError("Supplied mesh is not a valid Rhino mesh!")
    if not filepath or type(filepath) is not str:
        raise ValueError("Supplied filepath is not a valid filepath!")

    # remove trailing newlines from the filepath and check for file extension
    filepath = path.normpath(filepath.rstrip("\n\r"))
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
        #scriptcontext.escape_test()
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
            if len(temp) == 4 and temp[-2] == temp[-1]:
                    temp.pop()
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

# MAIN -------------------------------------------------------------------------
if __name__ == '__main__':
    pass
