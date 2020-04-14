# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division

# RHINO IMPORTS
from Rhino.Geometry import Point3d, Polyline, PolylineCurve

class Constraint(object):
    """Class for representing autoknit constraints separate from the model.
    The chain is stored as vertex coordinates."""

    def __init__(self, id, vertices, value, radius):
        """Create a new autoknit Constraint."""
        self._set_id(id)
        self._set_vertices(vertices)
        self._set_value(value)
        self._set_radius(radius)

    def ToString(self):
        name = "Autoknit Constraint"
        data = "({}, {}, {}, {})".format(self.Id,
                                         self.Vertices,
                                         self.Value,
                                         self.Radius)
        return name + data

    @classmethod
    def FromPolyline(cls, polyline):
        """Make Constraint from a Rhino Polyline"""
        raise NotImplementedError("This has not been implemented yet!")

    # BASE PROPERTIES ----------------------------------------------------------

    # ID PROPERTY --------------------------------------------------------------
    def _get_id(self):
        """Gets the id (index) of this constraint."""
        return self._id

    def _set_id(self, id):
        """Sets the id (index) of this constraint."""
        if not type(id) == int:
            try:
                id = int(id)
            except:
                raise ValueError("Expected integer value for id!")
        self._id = id

    Id = property(_get_id, _set_id, None,
                  "The Id (index) of this constraint.")

    # VERTICES PROPERTY --------------------------------------------------------
    def _get_vertices(self):
        """Gets the vertex coordinates of this constraint as list of tuples."""
        return self._vertices

    def _set_vertices(self, vertices):
        if type(vertices) is not list:
            raise ValueError("Expected list of vertices!")
        try:
            for i, item in enumerate(vertices):
                if type(item) is Point3d:
                    vertices[i] = (item.X, item.Y, item.Z)
                elif type(item) is tuple and len(item) == 3:
                    continue
        except:
            raise RuntimeError("Some of the given vertices " + \
                               "failed to convert to tuples!")
        self._vertices = vertices

    Vertices = property(_get_vertices, _set_vertices, None,
                     "The vertex coordinates of the constraint.")

    # TIME VALUE PROPERTY ------------------------------------------------------
    def _get_value(self):
        """Gets the time value fro this constraint."""
        return self._value

    def _set_value(self, value):
        """Sets the time value for this constraint."""
        try:
            value = float(value)
        except Exception, e:
            raise RuntimeError("Failed to set time value for constraint " + \
                               "{} // {}".format(str(self), e))
        self._value = value

    Value = property(_get_value, _set_value, None,
                     "The time value of the constraint.")

    # RADIUS PROPERTY ----------------------------------------------------------
    def _get_radius(self):
        return self._radius

    def _set_radius(self, value):
        try:
            value = float(value)
        except Exception, e:
            raise RuntimeError("Failed to set radius for constraint " + \
                               "{} // {}".format(str(self), e))
        self._radius = value

    Radius = property(_get_radius, None, None,
                      "The radius of the constraint.")

    # VALIDATION PROPERTY ------------------------------------------------------
    def _get_valid(self):
        """Returns True if the Constraint is valid."""
        if self.Id != None:
            id = True
        if self.Vertices != None and len(self.Vertices) > 0:
            cv = True
        if self.Value != None:
            vv = True
        if self.Radius != None:
            rv = True
        return id == cv == vv == rv

    IsValid = property(_get_valid, None, None,
                       "Identifier if this constraint is valid.")
