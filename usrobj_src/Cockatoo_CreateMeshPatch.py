"""
Construct a mesh patch from a variety of input geometry. Direct implementation
of the Rhino.Geometry.Mesh.CreatePatch method.
    Inputs:
        OuterBoundary: (optional: can be None) Outer boundary polyline, if 
                       provided this will become the outer boundary of the
                       resulting mesh. Any of the input that is completely
                       outside the outer boundary will be ignored and have no
                       impact on the result. If any of the input intersects the
                       outer boundary the result will be unpredictable and is
                       likely to not include the entire outer boundary.
                       {item, polyline}
        AngleTolerance: Maximum angle (in radians) between unit tangents and
                        adjacent verticies. Used to divide curve inputs that
                        cannot otherwise be represented as a polyline.
                        {item, float}
        PullbackSurface: (optional: can be None) Initial surface where 3d input
                         will be pulled to make a 2d representation used by the
                         function that generates the mesh. Providing a
                         PullbackSurface can be helpful when it is similar in
                         shape to the pattern of the input, the pulled 2d points
                         will be a better representation of the 3d points. If 
                         all of the input is more or less coplanar to start 
                         with, providing pullbackSurface has no real benefit.
                         {item, surface)
        InnerBoundaryCurves: (optional: can be None) Polylines to create holes
                             in the output mesh. If innerBoundaryCurves are the
                             only input then the result may be None if trimback
                             is set to false (see comments for trimback) because
                             the resulting mesh could be invalid (all faces
                             created contained vertexes from the perimeter
                             boundary).
                             {list, polyline}
        InnerBothSideCurves: (optional: can be None) These polylines will create
                             faces on both sides of the edge. If there are only
                             input points(innerPoints) there is no way to
                             guarantee a triangulation that will create an edge
                             between two particular points. Adding a line, or
                             polyline, to innerBothsideCurves that includes
                             points from innerPoints will help guide the
                             triangulation.
                             {list, polyline}
        InnerPoints: (optional: can be None) Points to be used to generate the
                     mesh. If outerBoundary is not null, points outside of that
                     boundary after it has been pulled to pullbackSurface
                     (or the best plane through the input if pullbackSurface is
                     null) will be ignored.
                     {list, point}
        TrimBack:  Only used when a outerBoundary has not been provided. When 
                   hat is the case, the function uses the perimeter of the
                   surface as the outer boundary instead. If true, any face of
                   the resulting triangulated mesh that contains a vertex of the
                   perimeter boundary will be removed.
                   {item, bool}
        Divisions:  Only used when a outerBoundary has not been provided. When
                    that is the case, division becomes the number of divisions
                    each side of the surface's perimeter will be divided into
                    to create an outer boundary to work with.
                    {item, int}
    Output:
        Mesh: The mesh patch on success; None on failure.
              {item/list, mesh}
    Remarks:
        Author: Max Eschenbach
        License: MIT License
        Version: 200705
"""

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

ghenv.Component.Name = "CreateMeshPatch"
ghenv.Component.NickName = "CMP"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "02 Meshing & Remeshing"

class CreateMeshPatch(component):
    
    def RunScript(
    self, OuterBoundary, AngleTolerance, PullbackSurface, InnerBoundaryCurves,
    InnerBothSideCurves, InnerPoints, TrimBack, Divisions
    ):
        if not PullbackSurface or PullbackSurface == []:
            InnerBoundaryCurves = None
        if not InnerBoundaryCurves or InnerBoundaryCurves == []:
            InnerBoundaryCurves = None
        if not InnerBothSideCurves or InnerBothSideCurves == []:
            InnerBothSideCurves = None
        if not InnerPoints or InnerPoints == []:
            InnerPoints = None
        
        if (OuterBoundary or PullbackSurface or InnerBoundaryCurves or 
        InnerBothSideCurves or InnerPoints):
            try:
                Mesh = Rhino.Geometry.Mesh.CreatePatch(OuterBoundary,
                                                AngleTolerance,
                                                PullbackSurface,
                                                InnerBoundaryCurves,
                                                InnerBothSideCurves,
                                                InnerPoints,
                                                TrimBack,
                                                Divisions)
            except Exception, errMsg:
                rml = self.RuntimeMessageLevel.Error
                self.AddRuntimeMessage(rml, str(errMsg))
        else:
            Mesh = None
        
        # return outputs if you have them; here I try it for you:
        return Mesh
