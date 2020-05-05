"""
Renders the nodes and edges of a given KnitNetwork
TODO: Update docstring!
    Inputs:
        KnitNetwork: A KnitNetwork. {item, KnitNetwork}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200414
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# LOCAL MODULE IMPORTS
from mbe.component import customDisplay
from Cockatoo import KnitNetwork

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "RenderKnitNetwork"
ghenv.Component.NickName ="RKN"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "7 Visualisation"

class RenderKnitNetwork(component):
    
    def RunScript(self, Toggle, KN, RenderNodes, RenderNodeIndices, RenderNodeData, NodeTextPlane, NodeTextHeight, RenderContourEdges, RenderContourEdgeData, RenderWeftEdges, RenderWeftEdgeData, RenderWarpEdges, RenderWarpEdgeData, EdgeTextHeight, EdgeTextPlane):
        
        # SET DEFAULTS ---------------------------------------------------------
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
        
        # RENDER ACCORDING TO SET PARAMETERS -----------------------------------
        
        if Toggle and KN and (RenderNodes or \
                              RenderContourEdges or \
                              RenderWeftEdges or \
                              RenderWarpEdges):
            
            # create customdisplay
            viz = customDisplay(self, True)
            
            # RENDERING OF CONTOUR EDGES ---------------------------------------
            if RenderContourEdges:
                contourcol = System.Drawing.Color.Gray
                ContourEdges = KN.ContourEdges
                for ce in ContourEdges:
                    geo = ce[2]["geo"]
                    if type(geo) == Rhino.Geometry.Line:
                        geo = Rhino.Geometry.LineCurve(geo)
                    elif type(geo) == Rhino.Geometry.Polyline:
                        geo = geo.ToPolylineCurve()
                    viz.AddCurve(geo, contourcol, 2)
                    
                    # RENDERING OF CONTOUR EDGE DATA ---------------------------
                    if RenderContourEdgeData:
                        EdgeTextPlane.Origin = geo.PointAtNormalizedLength(0.5)
                        edgeLabel = [(k, ce[2][k]) for k \
                                     in ce[2] if k != "geo"]
                        edgeLabel = ["{}: {}".format(t[0], t[1]) for t \
                                     in edgeLabel]
                        edgeLabel = [str(ce[0]) + "-" + \
                                     str(ce[1])] + edgeLabel
                        edgeLabel = "\n".join(edgeLabel)
                        tagTxt = Rhino.Display.Text3d(str(edgeLabel),
                                                      EdgeTextPlane,
                                                      EdgeTextHeight)
                        tagTxt.FontFace = "Lato Light"
                        viz.AddText(tagTxt, contourcol)
            
            # RENDERING OF WEFT EDGES ------------------------------------------
            if RenderWeftEdges:
                weftcol = System.Drawing.Color.Blue
                WeftEdges = KN.WeftEdges
                for weft in WeftEdges:
                    geo = Rhino.Geometry.LineCurve(weft[2]["geo"])
                    viz.AddCurve(geo, weftcol, 2)
                    
                    # RENDERING OF WEFT DGE DATA -------------------------------
                    if RenderWeftEdgeData:
                        EdgeTextPlane.Origin = geo.PointAtNormalizedLength(0.5)
                        edgeLabel = [(k, weft[2][k]) for k \
                                     in weft[2] if k != "geo"]
                        edgeLabel = ["{}: {}".format(t[0], t[1]) for t \
                                     in edgeLabel]
                        edgeLabel = [str(weft[0]) + "-" + \
                                     str(weft[1])] + edgeLabel
                        edgeLabel = "\n".join(edgeLabel)
                        tagTxt = Rhino.Display.Text3d(str(edgeLabel),
                                                      EdgeTextPlane,
                                                      EdgeTextHeight)
                        tagTxt.FontFace = "Lato Light"
                        viz.AddText(tagTxt, weftcol)
            
            # RENDERING OF WARP EDGES ------------------------------------------
            if RenderWarpEdges:
                warpcol = System.Drawing.Color.Red
                WarpEdges = KN.WarpEdges
                for warp in WarpEdges:
                    geo = Rhino.Geometry.LineCurve(warp[2]["geo"])
                    viz.AddCurve(geo, warpcol, 2)
                    
                    # RENDERING OF WARP EDGE DATA ------------------------------
                    if RenderWarpEdgeData:
                        EdgeTextPlane.Origin = geo.PointAtNormalizedLength(0.5)
                        edgeLabel = [(k, warp[2][k]) for k \
                                     in warp[2] if k != "geo"]
                        edgeLabel = ["{}: {}".format(t[0], t[1]) for t \
                                     in edgeLabel]
                        edgeLabel = [str(warp[0]) + "-" + \
                                     str(warp[1])] + edgeLabel
                        edgeLabel = "\n".join(edgeLabel)
                        tagTxt = Rhino.Display.Text3d(str(edgeLabel),
                                                      EdgeTextPlane,
                                                      EdgeTextHeight)
                        tagTxt.FontFace = "Lato Light"
                        viz.AddText(tagTxt, warpcol)
            
            # RENDERING OF NODES -----------------------------------------------
            
            # define point styles for nodes
            psEnd = Rhino.Display.PointStyle.Circle
            psLeaf = Rhino.Display.PointStyle.Circle
            psRegular = Rhino.Display.PointStyle.RoundControlPoint
            
            # define colours for nodes and node texts
            colEnd = System.Drawing.Color.Red
            colLeaf = System.Drawing.Color.Green
            colEndLeaf = System.Drawing.Color.Orange
            colRegular = System.Drawing.Color.Black
            
            if RenderNodes or RenderNodeIndices or RenderNodeData:
                nodes = KN.nodes(data=True)
                
                for i, node in enumerate(nodes):
                    data = node[1]
                    if data["end"] == True and data["leaf"] == False:
                        if RenderNodes:
                            viz.AddPoint(data["geo"], colEnd, psEnd, 3)
                    elif data["end"] == False and data["leaf"] == True:
                        if RenderNodes:
                            viz.AddPoint(data["geo"], colLeaf, psLeaf, 3)
                    elif data["end"] == True and data["leaf"] == True:
                        if RenderNodes:
                            viz.AddPoint(data["geo"], colEndLeaf, psLeaf, 3)
                    elif data["leaf"] == False and data["end"] == False:
                        if RenderNodes:
                            viz.AddPoint(data["geo"], colRegular, psRegular, 2)
                    
                    if RenderNodeIndices or RenderNodeData:
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
                        
                        if RenderNodeData:
                            nodeLabel = [(k, data[k]) for k in data \
                                         if k != "geo" and \
                                            k != "x" and \
                                            k != "y" and \
                                            k != "z"]
                            nodeLabel = ["{}: {}".format(t[0], t[1]) \
                                         for t in nodeLabel]
                            nodeLabel = [""] + nodeLabel
                            nodeLabel = "\n".join(nodeLabel)
                            nodeTxt = Rhino.Display.Text3d(str(nodeLabel),
                                                          NodeTextPlane,
                                                          NodeTextHeight*0.3)
                            nodeTxt.FontFace = "Lato Light"
                            viz.AddText(nodeTxt, nodecol)
            
        else:
            viz = customDisplay(self, False)
