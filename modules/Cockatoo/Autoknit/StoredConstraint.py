# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division

# LOCAL MODULE IMPORTS
from . import Structs

class StoredConstraint(object):
    """Class for representing a stored autoknit Constraint."""

    # INITIALIZATION -----------------------------------------------------------

    def __init__(self, count, value, radius):
        """Creates a new StoredConstraint."""
        self._set_count(count)
        self._set_value(value)
        self._set_radius(radius)

    def ToString(self):
        name = "Autoknit StoredConstraint"
        data = "({}, {}, {})".format(self.Count, self.Value, self.Radius)
        return name + data

    # BASIC PROPERTIES ---------------------------------------------------------

    # CHAIN PROPERTY -----------------------------------------------------------
    def _get_count(self):
        return self._count

    def _set_count(self, count):
        if type(count) != int:
            try:
                count = int(count)
            except:
                raise ValueError("Expected vertex count as single integer!")
        self._count = count

    Count = property(_get_count, _set_count, None,
                     "The number of vertices constrained by this constraint.")

    # TIME VALUE PROPERTY ------------------------------------------------------
    def _get_value(self):
        return self._value

    def _set_value(self, value):
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

    Radius = property(_get_radius, _set_radius, None,
                      "The radius of the constraint.")

    # VALIDATION PROPERTY ------------------------------------------------------
    def _get_valid(self):
        """Returns True if the StoredConstraint is valid."""
        if self.Count != None and self.Count > 0:
            cv = True
        if self.Value != None:
            vv = True
        if self.Radius != None:
            rv = True
        return cv == vv == rv

    IsValid = property(_get_valid, None, None,
                       "Identifier if this constraint is valid.")

    # DATA PROPERTY ------------------------------------------------------------
    def _get_data(self):
        """Gets the data of this StoredConstraint as tuple."""
        if self.IsValid:
            return (self.Count, self.Value, self.Radius)
        else:
            return None

    Data = property(_get_data, None, None,
                    "The data of the StoredConstraint as tuple: " + \
                    "(Count, Value, Radius).")

    # BYTES FOR WRITING FILES --------------------------------------------------

    def _get_bytes(self):
        return Structs.STRUCT_STOREDCONSTRAINT.pack(self.Count,
                                                    self.Value,
                                                    self.Radius)

    Bytes = property(_get_bytes, None, None,
                     "The bytecode representation of this Constraint.")
