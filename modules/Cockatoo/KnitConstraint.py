"""
Representation of constraints derived from a mesh for automatic generation
of knitting patterns.

Author: Max Eschenbach
License: Apache License 2.0
Version: 200503
"""

# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from Cockatoo.Environment import IsRhinoInside
from Cockatoo.Exceptions import *

# RHINO IMPORTS ----------------------------------------------------------------
if IsRhinoInside():
    import rhinoinside
    rhinoinside.load()
    from Rhino.Geometry import PolylineCurve as RhinoPolylineCurve
else:
    from Rhino.Geometry import PolylineCurve as RhinoPolylineCurve

# AUTHORSHIP -------------------------------------------------------------------

__author__ = """Max Eschenbach (post@maxeschenbach.com)"""

# ALL LIST ---------------------------------------------------------------------
__all__ = [
    "KnitConstraint"
]

# ACTUAL CLASS -----------------------------------------------------------------
class KnitConstraint(object):
    """
    Datastructure for representing a constraint based on a mesh used for
    generating 3d knitting patterns.
    """

    def __init__(self, StartCourse, EndCourse, LeftBoundary, RightBoundary):
        if not isinstance(StartCourse, RhinoPolylineCurve):
            raise ValueError("StartCourse has to be of type PolylineCurve!")
        if not isinstance(EndCourse, RhinoPolylineCurve):
            raise ValueError("EndCourse has to be of type PolylineCurve!")
        self.cons = {"start" : StartCourse,
                     "end" : EndCourse,
                     "left" : [],
                     "right" : []}
        for lb in LeftBoundary:
            if not isinstance(lb, RhinoPolylineCurve):
                raise ValueError("All items of LeftBoundary have to be of type PolylineCurve!")
            self.cons["left"].append(lb)
        for rb in RightBoundary:
            if not isinstance(rb, RhinoPolylineCurve):
                raise ValueError("All items of RightBoundary have to be of type PolylineCurve!")
            self.cons["right"].append(rb)

    def ToString(self):
        """
        Return a textual description of the constraint.
        """

        name = "KnitConstraint"
        ll = len(self.cons["left"])
        lr = len(self.cons["right"])
        data = ("({} Left Boundaries, {} Right Boundaries)")
        data = data.format(ll, lr)
        return name + data

    # PROPERTIES ---------------------------------------------------------------

    def _get_StartCourse(self):
        return self.cons["start"]

    StartCourse = property(_get_StartCourse, None, None,
                           "The StartCourse of the KnitConstraint")

    def _get_EndCourse(self):
        return self.cons["end"]

    EndCourse = property(_get_EndCourse, None, None,
                           "The EndCourse of the KnitConstraint")

    def _get_LeftBoundary(self):
        return self.cons["left"]

    LeftBoundary = property(_get_LeftBoundary, None, None,
                           "The LeftBoundary of the KnitConstraint")

    def _get_RightBoundary(self):
        return self.cons["right"]

    RightBoundary = property(_get_RightBoundary, None, None,
                           "The RightBoundary of the KnitConstraint")
