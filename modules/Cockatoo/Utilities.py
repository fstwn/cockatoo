"""
Static utility functions for Cockatoo.

Author: Max Eschenbach
License: Apache License 2.0
Version: 200503
"""

# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from itertools import tee
from math import acos
from math import degrees

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from .Environment import IsRhinoInside

# RHINO IMPORTS ----------------------------------------------------------------
if IsRhinoInside():
    import rhinoinside
    rhinoinside.load()
    from Rhino.Geometry import Vector3d as RhinoVector3d
else:
    from Rhino.Geometry import Vector3d as RhinoVector3d

# AUTHORSHIP -------------------------------------------------------------------
__author__ = """Max Eschenbach (post@maxeschenbach.com)"""

# ALL DICTIONARY ---------------------------------------------------------------
__all__ = [
    "is_ccw_xy",
    "pairwise"
]

# ACTUAL FUNCTION DEFINTIONS ---------------------------------------------------

def is_ccw_xy(a, b, c, colinear=False):
    """
    Determine if c is on the left of ab when looking from a to b,
    and assuming that all points lie in the XY plane.

    Parameters
    ----------
    a : sequence of float
        XY(Z) coordinates of the base point.
    b : sequence of float
        XY(Z) coordinates of the first end point.
    c : sequence of float
        XY(Z) coordinates of the second end point.
    colinear : bool, optional
        Allow points to be colinear.
        Default is ``False``.

    Returns
    -------
    bool
        ``True`` if ccw.
        ``False`` otherwise.

    Notes
    -----
    Based on an implementation inside the COMPAS framework.
    For more info, see [1]_ and [2]_.

    References
    ----------
    .. [1] Van Mele, Tom *COMPAS - open-source, Python-based framework for computational research and collaboration in architecture, engineering and digital fabrication*.
           See: https://github.com/compas-dev/compas/blob/e313502995b0dd86d460f86e622cafc0e29d1b75/src/compas/geometry/_core/queries.py#L61
    .. [1] Marsh, C. *Computational Geometry in Python: From Theory to Application*.
           Available at: https://www.toptal.com/python/computational-geometry-in-python-from-theory-to-implementation

    Examples
    --------
    >>> print(is_ccw_xy([0,0,0], [0,1,0], [-1, 0, 0]))
    True
    >>> print(is_ccw_xy([0,0,0], [0,1,0], [+1, 0, 0]))
    False
    >>> print(is_ccw_xy([0,0,0], [1,0,0], [2,0,0]))
    False
    >>> print(is_ccw_xy([0,0,0], [1,0,0], [2,0,0], True))
    True
    """

    ab_x = b[0] - a[0]
    ab_y = b[1] - a[1]
    ac_x = c[0] - a[0]
    ac_y = c[1] - a[1]

    if colinear:
        return ab_x * ac_y - ab_y * ac_x >= 0
    return ab_x * ac_y - ab_y * ac_x > 0

def pairwise(iterable):
    """Returns the data of iterable in pairs (2-tuples).

    Parameters
    ----------
    iterable : iterable
        An iterable sequence of items.

    Yields
    ------
    tuple
        Two items per iteration, if there are at least two items in the iterable.

    Examples
    --------
    >>> print(pairwise(range(4))):
    ...
    [(0, 1), (1, 2), (2, 3)]

    Notes
    -----
    For more info see [1]_ .

    References
    ----------
    .. [1] Python itertools Recipes.
           See: https://docs.python.org/2.7/library/itertools.html#recipes

    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)
