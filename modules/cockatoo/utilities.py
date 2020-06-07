"""
.. currentmodule:: cockatoo.utilities

.. autosummary::
    :nosignatures:

    break_polyline
    map_values_as_colors
    tween_planes
    is_ccw_xy
    resolve_order_by_backtracking
"""

# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from collections import deque
from itertools import tee
from math import acos
from math import cos
from math import degrees
from math import pi

# DUNDER -----------------------------------------------------------------------
__author__ = """Max Eschenbach (post@maxeschenbach.com)"""
__all__ = [
    "break_polyline",
    "map_values_as_colors",
    "tween_planes",
    "is_ccw_xy",
    "resolve_order_by_backtracking",
    "pairwise"
]

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from cockatoo.environment import RHINOINSIDE
from cockatoo.exception import *

# RHINO IMPORTS ----------------------------------------------------------------
if RHINOINSIDE:
    import rhinoinside
    rhinoinside.load()
    from Rhino.Display import ColorHSL as RhinoColorHSL
    from Rhino.Geometry import Polyline as RhinoPolyline
    from Rhino.Geometry import Quaternion as RhinoQuaternion
    from Rhino.Geometry import Vector3d as RhinoVector3d
else:
    from Rhino.Display import ColorHSL as RhinoColorHSL
    from Rhino.Geometry import Polyline as RhinoPolyline
    from Rhino.Geometry import Quaternion as RhinoQuaternion
    from Rhino.Geometry import Vector3d as RhinoVector3d

# RHINO GEOMETRY ---------------------------------------------------------------

def break_polyline(polyline, break_angle):
    """
    Breaks a polyline at kinks based on a specified angle. Will move the seam
    of closed polylines to the first kink discovered.
    """

    # get all the polyline segments
    segments = deque(polyline.GetSegments())

    # check if polyline in closed
    if polyline.IsClosed:
        closedSeamAtKink = False
    else:
        closedSeamAtKink = True

    # initialize containers
    plcs = []
    pl = RhinoPolyline()

    # process all segments
    while len(segments) > 0:
        # if there is only one segment left, add the endpoint to the new pl
        if len(segments) == 1:
            ln = segments.popleft()
            pl.Add(ln.To)
            plcs.append(pl.ToPolylineCurve())
            break

        # get unitized directions of this and next segment
        thisdir = segments[0].Direction
        nextdir = segments[1].Direction
        thisdir.Unitize()
        nextdir.Unitize()

        # compute angle
        vdp = thisdir * nextdir
        angle = cos(vdp / (thisdir.Length * nextdir.Length))
        angle = RhinoVector3d.VectorAngle(thisdir, nextdir)

        # check angles and execute breaks
        if angle >= break_angle:
            if not closedSeamAtKink:
                segments.rotate(-1)
                pl.Add(segments.popleft().From)
                closedSeamAtKink = True
            elif closedSeamAtKink:
                ln = segments.popleft()
                pl.Add(ln.From)
                pl.Add(ln.To)
                plcs.append(pl.ToPolylineCurve())
                pl = RhinoPolyline()
        else:
            if not closedSeamAtKink:
                segments.rotate(-1)
            else:
                pl.Add(segments.popleft().From)

    return plcs

def tween_planes(pa, pb, t):
    """
    Tweens between two planes using quaternion rotation.
    """

    # handle dotnet dependency in a nice way
    try:
        from clr import Reference
        from System import Double
    except ImportError as e:
        errMsg = "Could not import System. This function cannot execute!"
        raise SystemNotPresentError(errMsg)

    # create the quternion rotation between the two input planes
    Q = RhinoQuaternion.Rotation(pa, pb)

    # prepare out parameters
    qAngle = Reference[Double]()
    qAxis = Reference[RhinoVector3d]()

    # get the rotation of the quaternion
    Q.GetRotation(qAngle, qAxis)

    axis = RhinoVector3d(qAxis.X, qAxis.Y, qAxis.Z)
    angle = float(qAngle) - 2 * pi if float(qAngle) > pi else float(qAngle)

    out_plane = pa.Clone()
    out_plane.Rotate(t * angle, axis, out_plane.Origin)
    translation = RhinoVector3d(pb.Origin - pa.Origin)
    out_plane.Translate(translation * t)

    return out_plane

# RHINO DISPLAY ----------------------------------------------------------------

def map_values_as_colors(values, srcMin, srcMax, targetMin = 0.0, targetMax = 0.7):
    """
    Make a list of HSL colors where the values are mapped onto a
    targetMin-targetMax hue domain. Meaning that low values will be red, medium
    values green and large values blue if targetMin: 0.0 and targetMax: 0.7

    Parameters
    ----------
    values : list
        List of values to map as colors.

    srcMin : float
        Lower bounds of the value domain.

    srcMax : float
        Upper bounds of the value domain.

    targetMin : float
        Lower bounds of the target (color) domain.
        Defaults to 0.

    targetMax : float
        Upper bounds of the target (color) domain.
        Defaults to 0.7 .

    Returns
    -------
    colors : list
        List of RGB colors corresponding to the input values.

    Notes
    -----
    Based on code by Anders Holden Deleuran. Code was only changed in regards
    of defaults and names.
    For more info see [10]_ .

    References
    ----------
    .. [10] mapValuesAsColors.py - gist by Anders Holden Deleuran
           See: https://gist.github.com/AndersDeleuran/82fa2a8a69ec10ac68176e1b848fdeea
    """

    # Remap numbers into new numeric domain
    remappedValues = []
    for v in values:
        if srcMax-srcMin > 0:
            rv = ((v-srcMin)/(srcMax-srcMin))*(targetMax-targetMin)+targetMin
        else:
            rv = (targetMin+targetMax)/2
        remappedValues.append(rv)

    # Make colors and return
    colors = []
    for v in remappedValues:
        c = RhinoColorHSL(v,1.0,0.5).ToArgbColor()
        colors.append(c)

    return colors

# FUNCTIONAL GRAPH UTILITIES ---------------------------------------------------

def _backtrack_node(G, node, pos, ordered_stack):
    """
    Backtracks a node until no new predecessors are found and
    inserts the node and all dependencies in order into the
    ordered stack list.
    """

    # check the node for dependencies
    dependencies = [pred for pred in G.predecessors_iter(node) \
                    if pred not in ordered_stack]

    # if node has no dependencies that are not already in the stack,
    # insert into the ordered stack of nodes and increment the pointer
    if not dependencies:
        if node not in ordered_stack:
            ordered_stack.insert(pos, node)
            pos += 1
            return pos, ordered_stack
    else:
        # if node has dependencies, build a local stack of dependencies
        dependencies = deque(dependencies)

        # backtrack all dependencies
        while len(dependencies) > 0:
            dependency = dependencies.pop()
            pos, ordered_stack = _backtrack_node(G,
                                                 dependency,
                                                 pos,
                                                 ordered_stack)

            # after all its dependencies are solved, insert the
            # dependent node at the current pointer position
            if dependency not in ordered_stack:
                ordered_stack.insert(pos, dependency)
                pos += 1

        # after dependencies and sub-dependencies are solved, insert the node
        ordered_stack.insert(pos, node)
        pos += 1

    # return the current pos and the filled ordered stack
    return pos, ordered_stack

def resolve_order_by_backtracking(G):
    """
    Resolve topological order of a networkx DiGraph through backtracking of
    all nodes in the graph. Nodes are only inserted into the output list if
    all their dependencies (predecessor nodes) are already inside the output
    list, otherwise the algorithm will first resolve all open dependencies.
    """

    # rais if graph is not directed
    if not G.is_directed():
        raise ValueError("This works only on directed graphs!")

    # stack is every node that has not been inserted yet
    stack = deque(G.nodes())
    # pos is the current pointer for insertion
    pos = 0
    # ordered stack is the target list for insertion
    ordered_stack = []
    # backtrack the whole stack
    while len(stack) > 0:
        # pop an arbitrary node from the stack
        current_node = stack.pop()
        # backtrack that node and resolve all its dependencies
        pos, ordered_stack = _backtrack_node(G,
                                             current_node,
                                             pos,
                                             ordered_stack)
    # return the ordered stack
    return ordered_stack

# PURE PYTHON GEOMETRY ---------------------------------------------------------

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
    For more info, see [2]_ and [3]_.

    References
    ----------
    .. [2] Van Mele, Tom *COMPAS - open-source, Python-based framework for computational research and collaboration in architecture, engineering and digital fabrication*.
           See: https://github.com/compas-dev/compas/blob/e313502995b0dd86d460f86e622cafc0e29d1b75/src/compas/geometry/_core/queries.py#L61
    .. [3] Marsh, C. *Computational Geometry in Python: From Theory to Application*.
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

# PYTHON HELPERS AND UTILITIES -------------------------------------------------

def pairwise(iterable):
    """
    Returns the data of iterable in pairs (2-tuples).

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
    For more info see [4]_ .

    References
    ----------
    .. [4] Python itertools Recipes.
           See: https://docs.python.org/2.7/library/itertools.html#recipes

    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)
