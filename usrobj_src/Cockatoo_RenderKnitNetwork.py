"""
Renders the nodes and edges of a given KnitNetwork to the Rhino viewport.
---
[WARNING] Rendering the associated data (attributes) as text or the directions
of the edges (DirectionalDisplay) can be **VERY** computation-intensive,
especially on large networks, and freeze Grasshopper & Rhino for a
substantial amount of time!
    Inputs:
        Toggle: {item, bool}
        KnitNetwork: A network of type KnitNetworkBase, this can be a
                     KnitNetwork, KnitMappingNetwork, KnitDiNetwork .
                     {item, KnitNetwork}
        RenderNodes: If True, colored nodes will be rendered to the viewport.
                     Defaults to False. {item, bool}
        RenderNodeIndices: If True, the identifiers of the nodes in the network
                           will be rendered to the viewport as text.
                           Defaults to False. {item, bool}
        RenderNodeData: If True, the associated data (attributes) of the nodes
                        will be rendered to the viewport as text. {item, bool}
        NodeTextPlane: The plane for orientation of the node identifiers and 
                       data text.
                       Defaults to World XZ. {item, plane}
        NodeTextHeight: The text size for the node identifiers and data in
                        model units.
                        Defaults to 0.1 . {item, float}
        RenderContourEdges: If True, the contour edges of the network will be
                            rendered to the viewport.
                            Defaults to False. {item, bool}
        RenderContourEdgeData: If True, the identifiers and associated data
                               (attributes) of contour edges will be rendered
                               to the viewport as text.
                               Defaults to False. {item, bool}
        RenderWeftEdges: If True, the 'weft' edges of the network will be
                         rendered to the viewport in blue.
                         Defaults to True. {item, bool}
        RenderWeftEdgeData: If True, the identifiers and associated data
                            (attributes) of 'weft' edges will be rendered
                            to the viewport as text.
                            Defaults to False. {item, bool}
        RenderWarpEdges: If True, the 'warp' edges of the network will be
                         rendered to the viewport in blue.
                         Defaults to True. {item, bool}
        RenderWarpEdgeData: If True, the identifiers and associated data
                            (attributes) of 'warp' edges will be rendered
                            to the viewport as text.
                            Defaults to False. {item, bool}
        DirectionalDisplay: If True, edges will be rendered as vectors instead
                            of using their associated line/polyline geometry.
                            Defaults to False. {item, bool}
        EdgeTextPlane: The plane for orientation of the edge identifiers and
                       data text.
                       Defaults to World XZ. {item, plane}
        EdgeTextHeight: The text size for the edge identifiers and data in
                        model units.
                        Defaults to 0.1 . {item, float}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200607
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
try:
    from cockatoo import KnitNetwork
except ImportError:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "RenderKnitNetwork"
ghenv.Component.NickName ="RKN"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "7 Visualisation"

class RenderKnitNetwork(component):
    
    def __init__(self):
        super(RenderKnitNetwork, self).__init__()
        
        self.drawing_nodes = []
        self.drawing_edges = []
        self.drawing_data = []
        self.draw_directional = False
    
    def get_BoundingBox(self):
        return Rhino.Geometry.BoundingBox()
    
    def DrawViewportWires(self, args):
        try:
            # get display from args
            display = args.Display
            
            # draw all catalogued nodes
            for node in self.drawing_nodes:
                display.DrawPoint(node[0], node[1], node[2], node[3])
            
            # draw all catalogued edges
            if self.draw_directional:
                for edge in self.drawing_edges:
                    display.DrawArrow(edge[0], edge[1])
            else:
                for edge in self.drawing_edges:
                    display.DrawLine(edge[0], edge[1], 2)
            
            # draw all catalogued data text tags
            for txtag in self.drawing_data:
                if display.IsVisible(txtag[0].TextPlane.Origin):
                    display.Draw3dText(txtag[0], txtag[1])
        
        except Exception, e:
            System.Windows.Forms.MessageBox.Show(str(e),
                                                 "Error while drawing preview!")
    
    def RunScript(self, KN, RenderNodes=False, RenderNodeIndices=False, RenderNodeData=False, NodeTextPlane=None, NodeTextHeight=0.1, RenderContourEdges=False, RenderContourEdgeData=False, RenderWeftEdges=True, RenderWeftEdgeData=False, RenderWarpEdges=True, RenderWarpEdgeData=False, DirectionalDisplay=False, EdgeTextPlane=None, EdgeTextHeight=0.1):
        
        # SET DEFAULTS ---------------------------------------------------------
        
        if NodeTextPlane is None:
            NodeTextPlane = Rhino.Geometry.Plane.WorldZX
            NodeTextPlane.Flip()
        
        if EdgeTextPlane is None:
            EdgeTextPlane = Rhino.Geometry.Plane.WorldZX
            EdgeTextPlane.Flip()
        
        if DirectionalDisplay is None:
            DirectionalDisplay = False
        
        # set directional drawing attribute for drawing method
        self.draw_directional = DirectionalDisplay
        
        # SET FONT FACES FOR DISPLAY -------------------------------------------
        
        nodeFontFace = "Helvetica"
        contourFontFace = "Helvetica"
        weftFontFace = "Helvetica"
        warpFontFace = "Helvetica"
        
        # RENDER ACCORDING TO SET PARAMETERS -----------------------------------
        
        node_drawing_list = []
        edge_drawing_list = []
        data_drawing_list = []
        
        if KN and (RenderNodes or \
                   RenderContourEdges or \
                   RenderWeftEdges or \
                   RenderWarpEdges):
            
            # RENDERING OF CONTOUR EDGES ---------------------------------------
            
            if RenderContourEdges:
                contourcol = System.Drawing.Color.Gray
                contour_edges = KN.contour_edges
                
                for ce in contour_edges:
                    egeo = ce[2]["geo"]
                    edge_drawing_list.append((egeo, contourcol))
                    
                    # RENDERING OF CONTOUR EDGE DATA ---------------------------
                    
                    if RenderContourEdgeData:
                        EdgeTextPlane.Origin = egeo.PointAt(0.5)
                        edgeLabel = [(k, ce[2][k]) for k \
                                     in ce[2] if k != "geo"]
                        edgeLabel = ["{}: {}".format(t[0], t[1]) for t \
                                     in edgeLabel]
                        edgeLabel.sort()
                        edgeLabel = [str(ce[0]) + "-" + \
                                     str(ce[1])] + edgeLabel
                        edgeLabel = "\n".join(edgeLabel)
                        tagTxt = Rhino.Display.Text3d(str(edgeLabel),
                                                      EdgeTextPlane,
                                                      EdgeTextHeight)
                        tagTxt.FontFace = contourFontFace
                        
                        data_drawing_list.append((tagTxt, contourcol))
            
            # RENDERING OF WEFT EDGES ------------------------------------------
            
            if RenderWeftEdges:
                weftcol = System.Drawing.Color.Blue
                weft_edges = KN.weft_edges
                for weft in weft_edges:
                    egeo = weft[2]["geo"]
                    edge_drawing_list.append((egeo, weftcol))
                    
                    # RENDERING OF WEFT DGE DATA -------------------------------
                    
                    if RenderWeftEdgeData:
                        EdgeTextPlane.Origin = egeo.PointAt(0.5)
                        edgeLabel = [(k, weft[2][k]) for k \
                                     in weft[2] if k != "geo"]
                        edgeLabel = ["{}: {}".format(t[0], t[1]) for t \
                                     in edgeLabel]
                        edgeLabel.sort()
                        edgeLabel = [str(weft[0]) + "-" + \
                                     str(weft[1])] + edgeLabel
                        edgeLabel = "\n".join(edgeLabel)
                        tagTxt = Rhino.Display.Text3d(str(edgeLabel),
                                                      EdgeTextPlane,
                                                      EdgeTextHeight)
                        tagTxt.FontFace = weftFontFace
                        data_drawing_list.append((tagTxt, weftcol))
            
            # RENDERING OF WARP EDGES ------------------------------------------
            
            if RenderWarpEdges:
                warpcol = System.Drawing.Color.Red
                warp_edges = KN.warp_edges
                for warp in warp_edges:
                    egeo = warp[2]["geo"]
                    edge_drawing_list.append((egeo, warpcol))
                    
                    # RENDERING OF WARP EDGE DATA ------------------------------
                    
                    if RenderWarpEdgeData:
                        EdgeTextPlane.Origin = egeo.PointAt(0.5)
                        edgeLabel = [(k, warp[2][k]) for k \
                                     in warp[2] if k != "geo"]
                        edgeLabel = ["{}: {}".format(t[0], t[1]) for t \
                                     in edgeLabel]
                        edgeLabel.sort()
                        edgeLabel = [str(warp[0]) + "-" + \
                                     str(warp[1])] + edgeLabel
                        edgeLabel = "\n".join(edgeLabel)
                        tagTxt = Rhino.Display.Text3d(str(edgeLabel),
                                                      EdgeTextPlane,
                                                      EdgeTextHeight)
                        tagTxt.FontFace = warpFontFace
                        data_drawing_list.append((tagTxt, warpcol))
            
            # RENDERING OF NODES -----------------------------------------------
            
            # define point styles for nodes
            psEnd = Rhino.Display.PointStyle.Circle
            psLeaf = Rhino.Display.PointStyle.Circle
            psRegular = Rhino.Display.PointStyle.RoundControlPoint
            
            # define colours for nodes and node texts
            colStart = System.Drawing.Color.Green
            colStartLeaf = System.Drawing.Color.SeaGreen
            colStartLeafEnd = System.Drawing.Color.Orange
            colStartEnd = System.Drawing.Color.DarkGreen
            colEnd = System.Drawing.Color.Blue
            colLeaf = System.Drawing.Color.Cyan
            colEndLeaf = System.Drawing.Color.Magenta
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
                            if data["start"]:
                                nodecol = colStartEnd
                            else:
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
                        if data["start"]:
                            nodecol = colStartLeafEnd
                        else:
                            nodecol = colEndLeaf
                        pStyle = psLeaf
                        pSize = 3
                    # NO END BUT LEAF
                    elif not data["end"] and data["leaf"]:
                        if data["start"]:
                            nodecol = colStartLeaf
                        else:
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
                        node_drawing_list.append((data["geo"], pStyle, pSize, nodecol))
                    
                    # RENDER NODE DATA AND INDICES -----------------------------
                    
                    if RenderNodeIndices or RenderNodeData:
                        NodeTextPlane.Origin = data["geo"]
                        tagTxt = Rhino.Display.Text3d(str(node[0]),
                                                          NodeTextPlane,
                                                          NodeTextHeight)
                        tagTxt.FontFace = nodeFontFace
                        if data["end"] == True:
                            nodecol = colEnd
                        elif data["leaf"] == True:
                            nodecol = colLeaf
                        elif data["leaf"] == False and data["end"] == False:
                            nodecol = colRegular
                        data_drawing_list.append((tagTxt, nodecol))
                        
                        if RenderNodeData:
                            nodeLabel = [(k, data[k]) for k in data \
                                         if k != "geo" and \
                                            k != "x" and \
                                            k != "y" and \
                                            k != "z"]
                            nodeLabel = ["{}: {}".format(t[0], t[1]) \
                                         for t in nodeLabel]
                            nodeLabel.sort()
                            nodeLabel = [""] + nodeLabel
                            nodeLabel = "\n".join(nodeLabel)
                            nodeTxt = Rhino.Display.Text3d(str(nodeLabel),
                                                          NodeTextPlane,
                                                          NodeTextHeight*0.3)
                            nodeTxt.FontFace = nodeFontFace
                            data_drawing_list.append((nodeTxt, nodecol))
            
            # set attributes and draw
            self.drawing_nodes = node_drawing_list
            self.drawing_edges = edge_drawing_list
            self.drawing_data = data_drawing_list
            
        else:
            if not KN:
                self.drawing_nodes = []
                self.drawing_edges = []
                self.drawing_data = []
                rml = self.RuntimeMessageLevel.Warning
                self.AddRuntimeMessage(rml, "No KnitNetwork input!")
