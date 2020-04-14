"""
Geometry tools for GHPython scripts
Author: Max Eschenbach
License: Apache License 2.0
Version: 200414
"""
# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import absolute_import
from __future__ import division
from collections import deque
import math

# RHINO IMPORTS
import Rhino
import scriptcontext

def BreakPolyline(Polyline, BreakAngle):
    """
    Breaks a polyline at kinks based on a specified angle.
    """

    # get all the polyline segments
    segments = deque(Polyline.GetSegments())

    # initialize containers
    if Polyline.IsClosed:
        closedSeamAtKink = False
    else:
        closedSeamAtKink = True
    plcs = []
    pl = Rhino.Geometry.Polyline()

    # process all segments
    while len(segments) > 0:
        scriptcontext.escape_test()

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
        angle = math.cos(vdp / (thisdir.Length * nextdir.Length))
        angle = Rhino.Geometry.Vector3d.VectorAngle(thisdir, nextdir)

        # check angles and execute breaks
        if angle >= BreakAngle:
            if not closedSeamAtKink:
                segments.rotate(-1)
                pl.Add(segments.popleft().From)
                closedSeamAtKink = True
            elif closedSeamAtKink:
                ln = segments.popleft()
                pl.Add(ln.From)
                pl.Add(ln.To)
                plcs.append(pl.ToPolylineCurve())
                pl = Rhino.Geometry.Polyline()
        else:
            if not closedSeamAtKink:
                segments.rotate(-1)
            else:
                pl.Add(segments.popleft().From)

    return plcs
