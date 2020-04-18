# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# RHINO IMPORTS ----------------------------------------------------------------
from Rhino.Geometry import Mesh as RhinoMesh

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from .EmbeddedConstraint import EmbeddedConstraint
from .StoredConstraint import StoredConstraint
from .Constraint import Constraint
from .FileIO import LoadConstraints, SaveConstraints, SaveObj, LoadObj
from .Utility import AttributeList, make_kd_tree, get_nearest

# ALL DICTIONARY ---------------------------------------------------------------
__all__ = [
    "Model"
]

# ACTUAL CLASS -----------------------------------------------------------------
class Model(object):
    """Class for representing a constrained Model."""

    # INITIALIZATION -----------------------------------------------------------

    def __init__(self, mesh, constraints = None):
        """Initializes a new constrained model."""
        self._set_mesh(mesh)
        if not constraints or len(constraints) == 0:
            self._constraints = []
        else:
            self._set_constraints(constraints)

    def ToString(self):
        name = "Autoknit Model"
        mv = self.Mesh.Vertices.Count
        mf = self.Mesh.Faces.Count
        mesh = "Mesh (V:{} F:{})".format(mv, mf)
        cons = "{} Constraints".format(str(len(self.Constraints)))
        return name + "({}, {})".format(mesh, cons)

    # BASIC PROPERTIES ---------------------------------------------------------

    # MESH ---------------------------------------------------------------------
    def _get_mesh(self):
        return self._mesh

    def _set_mesh(self, mesh):
        if type(mesh) != RhinoMesh:
            raise ValueError("Expected a Rhino Mesh!")
        self._mesh = mesh

    Mesh = property(_get_mesh, _set_mesh, None,
                    "The underlying mesh of the constrained model.")

    # CONSTRAINTS --------------------------------------------------------------

    def _get_constraints(self):
        """Gets the constraints stored within this model."""
        return self._constraints

    def _set_constraints(self, constraints):
        """Set the constraints for this model."""
        newcons = []
        noid = []
        try:
            constraints = sorted(constraints, key=lambda x: x.Id)
        except:
            raise ValueError("Could not set the constraints. \
                              Check if all supplied constraints are valid \
                              Constraint instances.")
        for i, cons in enumerate(constraints):
            if cons.Id == -1:
                noid.append(cons)
            else:
                newcons.append(cons)
        if len(newcons) > 0:
            nextid = newcons[-1].Id + 1
        else:
            nextid = 0
        for i, addcons in enumerate(noid):
            if len(newcons) > 0:
                addcons.Id = newcons[-1].Id + 1
            else:
                addcons.Id = nextid
            newcons.append(addcons)
        embcons = [self._embed_constraint(c, 0.0001) for c in newcons]
        self._constraints = self._sort_constraints(embcons)

    Constraints = property(_get_constraints, None, None,
                           "The constraints of this constrained model.")

    # CONSTRAINT COORDINATES ---------------------------------------------------

    def _get_constraint_coordinates(self):
        """Gets the coordinates of all embedded constraints."""
        vertices = list(self.Mesh.Vertices.ToPoint3dArray())
        coordinates = []
        for cons in self.Constraints:
            points = []
            for vidx in cons.Chain:
                points.append((vertices[vidx].X, vertices[vidx].Y, vertices[vidx].Z))
            coordinates.append(points)
        return coordinates

    ConstraintCoordinates = property(_get_constraint_coordinates, None, None,
                            "The coodinates of all the model's constraints.")

    # EMBEDDING OF CONSTRAINTS -------------------------------------------------

    def _embed_constraint(self, constraint, tolerance):
        """Embeds a constraint within the model and returns an
        Autoknit EmbeddedConstraint object"""
        # get all the vertices of the mesh embedded within the model
        mv = [AttributeList([p.X, p.Y, p.Z], idx=i) for i, p in \
                        enumerate(list(self.Mesh.Vertices.ToPoint3dArray()))]

        # make kdtree from mesh vertices for looking up constraint coordinates
        kd_tree = make_kd_tree(mv, 3)
        # define euclidean distance function
        euc_dist = lambda a, b: sum((a[i] - b[i]) ** 2 for i in xrange(3))

        # get the vertices of the constraint and lookup nearest node in the tree
        chain = []
        for v in constraint.Vertices:
            dist, nv = get_nearest(kd_tree, list(v), 3, euc_dist, True)
            if dist > tolerance:

                #TODO: implement better handling if point is not within tol
                print("too high!")
                continue
            chain.append(nv)

        # get the indices of the found chain points
        chain_indices = [v.idx for v in chain]

        # build an embedded constraint from the indices, value and radius
        value = constraint.Value
        radius = constraint.Radius
        ec = EmbeddedConstraint(chain_indices, value, radius)
        return ec

    # ORDERING OF CONSTRAINTS BASED ON TIME VALUES -----------------------------

    def _sort_constraints(self, constraints):
        """Sorts a bunch of constraints based on their time value"""
        return sorted(constraints, key=lambda x: x.Value)

    # ADDING OF NEW CONSTRAINTS ------------------------------------------------

    def AddConstraint(self, constraint):
        """Adds a constraint to the model. Returns true on success, false otherwise."""
        cons = self.Constraints
        try:
            cons.append(self._embed_constraint(constraint))
            self._set_constraints(constraint)
            return True
        except:
            return False

# MAIN -------------------------------------------------------------------------
if __name__ == '__main__':
    pass
