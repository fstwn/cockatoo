"""Renders the nodes and edges of a given KnitMeshNetwork
    Inputs:
        KnitMeshNetwork: A KnitMeshNetwork. {item, KnitMeshNetwork}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200324
"""

# PYTHON LIBRARY IMPORTS
from __future__ import division

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# CUSTOM MODULE IMPORTS
from mbe.component import customDisplay
from cockatoo import KnitMeshNetwork

ghenv.Component.Name = "RenderKnitMeshNetwork"
ghenv.Component.NickName ="RKMN"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "9 Utilities"

class RenderKnitMeshNetwork(component):
    
    def RunScript(self, KMN, VizNodes, VizNodeData, NodeTextPlane, NodeTextHeight, VizContours, VizWeftEdges, VizWarpEdges, VizEdgeData, EdgeTextHeight, EdgeTextPlane):
        
        if NodeTextHeight == None:
            NodeTextHeight = 0.1
        if NodeTextPlane == None:
            NodeTextPlane = Rhino.Geometry.Plane.WorldZX
            NodeTextPlane.Flip()
        
        if EdgeTextHeight == None:
            EdgeTextHeight = 0.1
        if EdgeTextPlane == None:
            EdgeTextPlane = Rhino.Geometry.Plane.WorldZX
            EdgeTextPlane.Flip()
        
        if KMN and (VizNodes or VizContours or VizWeftEdges or VizWarpEdges):
            # create customdisplay
            viz = customDisplay(self, True)
            
            if VizContours:
                contourcol = System.Drawing.Color.Gray
                ContourEdges = KMN.ContourEdges
                for ce in ContourEdges:
                    geo = ce[2]["geo"]
                    if type(geo) == Rhino.Geometry.Line:
                        geo = Rhino.Geometry.LineCurve(geo)
                    elif type(geo) == Rhino.Geometry.Polyline:
                        geo = geo.ToPolylineCurve()
                    viz.AddCurve(geo, contourcol, 2)
            
            if VizWeftEdges:
                weftcol = System.Drawing.Color.Blue
                WeftEdges = KMN.WeftEdges
                for weft in WeftEdges:
                    geo = Rhino.Geometry.LineCurve(weft[2]["geo"])
                    viz.AddCurve(geo, weftcol, 2)
                    
                    if VizEdgeData:
                        EdgeTextPlane.Origin = geo.PointAtNormalizedLength(0.5)
                        edgeLabel = [(k, weft[2][k]) for k in weft[2] if k != "geo"]
                        edgeLabel = ["{}: {}".format(t[0], t[1]) for t in edgeLabel]
                        edgeLabel = [str(weft[0]) + "-" + str(weft[1])] + edgeLabel
                        edgeLabel = "\n".join(edgeLabel)
                        tagTxt = Rhino.Display.Text3d(str(edgeLabel),
                                                      EdgeTextPlane,
                                                      EdgeTextHeight)
                        tagTxt.FontFace = "Lato Light"
                        viz.AddText(tagTxt, System.Drawing.Color.Blue)
            
            if VizWarpEdges:
                warpcol = System.Drawing.Color.Red
                WarpEdges = KMN.WarpEdges
                for warp in WarpEdges:
                    geo = Rhino.Geometry.LineCurve(warp[2]["geo"])
                    viz.AddCurve(geo, warpcol, 2)
                    
                    if VizEdgeData:
                        EdgeTextPlane.Origin = geo.PointAtNormalizedLength(0.5)
                        edgeLabel = [(k, warp[2][k]) for k in warp[2] if k != "geo"]
                        edgeLabel = ["{}: {}".format(t[0], t[1]) for t in edgeLabel]
                        edgeLabel = [str(warp[0]) + "-" + str(warp[1])] + edgeLabel
                        edgeLabel = "\n".join(edgeLabel)
                        tagTxt = Rhino.Display.Text3d(str(edgeLabel),
                                                      EdgeTextPlane,
                                                      EdgeTextHeight)
                        tagTxt.FontFace = "Lato Light"
                        viz.AddText(tagTxt, System.Drawing.Color.Red)
            
            # define point styles for nodes
            psEnd = Rhino.Display.PointStyle.Circle
            psLeaf = Rhino.Display.PointStyle.Circle
            psRegular = Rhino.Display.PointStyle.RoundControlPoint
            
            # define colours for nodes and node texts
            colEnd = System.Drawing.Color.Red
            colLeaf = System.Drawing.Color.Green
            colRegular = System.Drawing.Color.Black
            
            if VizNodes or VizNodeData:
                nodes = KMN.nodes(data=True)
                
                for i, node in enumerate(nodes):
                    data = node[1]
                    if data["end"] == True:
                        if VizNodes:
                            viz.AddPoint(data["geo"], colEnd, psEnd, 2)
                    elif data["leaf"] == True:
                        if VizNodes:
                            viz.AddPoint(data["geo"], colLeaf, psLeaf, 3)
                    elif data["leaf"] == False and data["end"] == False:
                        if VizNodes:
                            viz.AddPoint(data["geo"], colRegular, psRegular, 2)
                    
                    if VizNodeData:
                        NodeTextPlane.Origin = data["geo"]
                        tagTxt = Rhino.Display.Text3d(str(node[0]),
                                                          NodeTextPlane,
                                                          NodeTextHeight)
                        tagTxt.FontFace = "Lato Light"
                        if data["end"] == True:
                            nodecol = colEnd
                        elif data["leaf"] == True:
                            nodecol = colLeaf
                        elif data["leaf"] == False and data["end"] == False:
                            nodecol = colRegular
                        viz.AddText(tagTxt, nodecol)
                        
                        nodeLabel = [(k, data[k]) for k in data \
                                     if k != "geo" and \
                                        k != "x" and \
                                        k != "y" and \
                                        k != "z"]
                        nodeLabel = ["{}: {}".format(t[0], t[1]) for t in nodeLabel]
                        nodeLabel = [""] + nodeLabel
                        nodeLabel = "\n".join(nodeLabel)
                        nodeTxt = Rhino.Display.Text3d(str(nodeLabel),
                                                      NodeTextPlane,
                                                      NodeTextHeight*0.3)
                        nodeTxt.FontFace = "Lato Light"
                        viz.AddText(nodeTxt, nodecol)
            
        else:
            viz = customDisplay(self, False)
