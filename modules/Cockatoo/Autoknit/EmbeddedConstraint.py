# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import division

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from Cockatoo.Autoknit.StoredConstraint import StoredConstraint

# ALL DICTIONARY ---------------------------------------------------------------
__all__ = [
    "EmbeddedConstraint"
]

# ACTUAL CLASS -----------------------------------------------------------------
class EmbeddedConstraint(object):
    """
    Class for representing an autoknit constraint in relation to the model.
    The chain is only stored as vertex indices.
    """

    def __init__(self, chain, value, radius):
        """Create a new autoknit Constraint."""
        self._set_chain(chain)
        self._set_value(value)
        self._set_radius(radius)

    def ToString(self):
        name = "Autoknit EmbeddedConstraint"
        data = "({}, {}, {})".format(self.Chain, self.Value, self.Radius)
        return name + data

    # BASE PROPERTIES ----------------------------------------------------------

    # CHAIN PROPERTY -----------------------------------------------------------
    def _get_chain(self):
        return self._chain

    def _set_chain(self, chain):
        if type(chain) != list:
            raise RuntimeError("Expected list of vertex indices as chain!")
        try:
            for i, item in enumerate(chain):
                chain[i] = int(item)
        except:
            raise RuntimeError("Some of the indices in the given chain " + \
                               "failed to convert to integers!")
        self._chain = chain

    Chain = property(_get_chain, _set_chain, None,
                     "The chain of points of the constraint.")

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

    def _set_radius(self, radius):
        try:
            radius = float(radius)
        except Exception, e:
            raise RuntimeError("Failed to set radius for constraint " + \
                               "{} // {}".format(str(self), e))
        self._radius = radius

    Radius = property(_get_radius, _set_radius, None,
                      "The radius of the constraint.")

    # CONVERT CONSTRAINT FOR STORAGE -------------------------------------------
    def _get_storable(self):
        count = len(self.Chain)
        storable = (count, self.Value, self.Radius)
        return storable

    Storable = property(_get_storable, None, None,
                        "A storable version of this constraint.")

# MAIN -------------------------------------------------------------------------
if __name__ == '__main__':
    pass
