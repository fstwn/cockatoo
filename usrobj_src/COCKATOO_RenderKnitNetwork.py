"""
Renders the nodes and edges of a given KnitNetwork
TODO: Update docstring!
    Inputs:
        KnitNetwork: A KnitNetwork. {item, KnitNetwork}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200519
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
        
        DirectionalDisplay = False
        
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
                    egeo = ce[2]["geo"]
                    if type(egeo) == Rhino.Geometry.Line:
                        geo = Rhino.Geometry.LineCurve(egeo)
                    elif type(egeo) == Rhino.Geometry.Polyline:
                        geo = egeo.ToPolylineCurve()
                    
                    if DirectionalDisplay:
                        ptFrom = geo.PointAtStart
                        ptTo = geo.PointAtEnd
                        dvec = Rhino.Geometry.Vector3d(ptTo - ptFrom)
                        #viz.AddVector(ptFrom, dvec, contourcol, False)
                        viz.AddCurve(geo, contourcol, 2)
                    else:
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
                    egeo = weft[2]["geo"]
                    if DirectionalDisplay:
                        dvec = Rhino.Geometry.Vector3d(egeo.To - egeo.From)
                        viz.AddVector(egeo.From, dvec, weftcol, False)
                    else:
                        linegeo = Rhino.Geometry.LineCurve(egeo)
                        viz.AddCurve(linegeo, weftcol, 2)
                    
                    # RENDERING OF WEFT DGE DATA -------------------------------
                    if RenderWeftEdgeData:
                        EdgeTextPlane.Origin = egeo.PointAtNormalizedLength(0.5)
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
                    egeo = warp[2]["geo"]
                    if DirectionalDisplay:
                        dvec = Rhino.Geometry.Vector3d(egeo.To - egeo.From)
                        viz.AddVector(egeo.From, dvec, warpcol, False)
                    else:
                        linegeo = Rhino.Geometry.LineCurve(egeo)
                        viz.AddCurve(linegeo, warpcol, 2)
                    
                    # RENDERING OF WARP EDGE DATA ------------------------------
                    if RenderWarpEdgeData:
                        EdgeTextPlane.Origin = egeo.PointAtNormalizedLength(0.5)
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
            colEnd = System.Drawing.Color.Blue
            colLeaf = System.Drawing.Color.Cyan
            colEndLeaf = System.Drawing.Color.Orange
            colRegular = System.Drawing.Color.Black
            colIncreaseEnd = System.Drawing.Color.Purple
            colDecreaseEnd = System.Drawing.Color.DarkViolet
            colIncrease = System.Drawing.Color.Red
            colDecrease = System.Drawing.Color.DarkRed
            
            if RenderNodes or RenderNodeIndices or RenderNodeData:
                nodes = KN.nodes(data=True)
                
                for i, node in enumerate(nodes):
                    data = node[1]
                    # END BUT NOT LEAF
                    if data["end"] and not data["leaf"]:
                        if not data["increase"] and not data["decrease"]:
                            nodecol = colEnd
                            pStyle = psEnd
                            pSize = 3
                        elif data["increase"] and not data["decrease"]:
                            nodecol = colIncreaseEnd
                            pStyle = psEnd
                            pSize = 3
                        elif not data["increase"] and data["decrease"]:
                            nodecol = colDecreaseEnd
                            pStyle = psEnd
                            pSize = 3
                    # END AND LEAF
                    elif data["end"] and data["leaf"]:
                        nodecol = colEndLeaf
                        pStyle = psLeaf
                        pSize = 3
                    # NO END BUT LEAF
                    elif not data["end"] and data["leaf"]:
                        nodecol = colLeaf
                        pStyle = psLeaf
                        pSize = 3
                    # NO END NO LEAF
                    elif not data["end"] and not data["leaf"]:
                        if data["increase"] and not data["decrease"]:
                            nodecol = colIncrease
                            pStyle = psEnd
                            pSize = 3
                        elif not data["increase"] and data["decrease"]:
                            nodecol = colDecrease
                            pStyle = psEnd
                            pSize = 3
                        else:
                            nodecol = colRegular
                            pStyle = psRegular
                            pSize = 2
                    
                    if RenderNodes:
                        viz.AddPoint(data["geo"], nodecol, pStyle, pSize)
                    
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
