# PYTHON STANDARD LIBRARY IMPORTS ---------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# DUNDER ----------------------------------------------------------------------
__all__ = [
    "KnitConstraint"
]

# LOCAL MODULE IMPORTS --------------------------------------------------------
from cockatoo.environment import RHINOINSIDE

# RHINO IMPORTS ---------------------------------------------------------------
if RHINOINSIDE:
    import rhinoinside
    rhinoinside.load()
    from Rhino.Geometry import Curve as RhinoCurve
else:
    from Rhino.Geometry import Curve as RhinoCurve

# CLASS DECLARATION -----------------------------------------------------------


class KnitConstraint(object):
    """
    Datastructure for representing constraints derived from a mesh. Used for
    the automatic generation of knitting patterns.
    """

    def __init__(self,
                 start_course,
                 end_course,
                 left_boundary,
                 right_boundary):
        if not isinstance(start_course, RhinoCurve):
            raise ValueError("start_course has to be of type Curve!")
        if not isinstance(end_course, RhinoCurve):
            raise ValueError("end_course has to be of type Curve!")
        self.cons = {"start": start_course,
                     "end": end_course,
                     "left": [],
                     "right": []}
        for lb in left_boundary:
            if not isinstance(lb, RhinoCurve):
                errMsg = "All items of left_boundary have to be of type " + \
                         "Curve!"
                raise ValueError(errMsg)
            self.cons["left"].append(lb)
        for rb in right_boundary:
            if not isinstance(rb, RhinoCurve):
                errMsg = "All items of right_boundary have to be of type " + \
                         "Curve!"
                raise ValueError()
            self.cons["right"].append(rb)

    # TEXTUAL REPRESENTATION --------------------------------------------------

    def __repr__(self):
        """
        Return a textual description of the constraint.

        Returns
        -------
        description : str
            A textual description of the constraint
        """

        name = "KnitConstraint"

        ll = len(self.cons["left"])
        lr = len(self.cons["right"])
        data = ("({} Left Boundaries, {} Right Boundaries)")
        data = data.format(ll, lr)

        return name + data

    def ToString(self):
        """
        Return a textual description of the constraint.

        Returns
        -------
        description : str
            A textual description of the constraint.

        Notes
        -----
        Used for overloading the Grasshopper display in data parameters.
        """

        return repr(self)

    # PROPERTIES --------------------------------------------------------------

    def _get_start_course(self):
        return self.cons["start"]

    start_course = property(_get_start_course, None, None,
                            "The start course of the KnitConstraint")

    def _get_end_course(self):
        return self.cons["end"]

    end_course = property(_get_end_course, None, None,
                          "The end course of the KnitConstraint")

    def _get_left_boundary(self):
        return self.cons["left"]

    left_boundary = property(_get_left_boundary, None, None,
                             "The left boundary of the KnitConstraint")

    def _get_right_boundary(self):
        return self.cons["right"]

    right_boundary = property(_get_right_boundary, None, None,
                              "The right boundary of the KnitConstraint")
