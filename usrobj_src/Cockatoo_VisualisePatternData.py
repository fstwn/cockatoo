"""
Draws a custom 2d graph layout of a KnitNetwork and the corresponding 2d pattern
data.
---
[WARNING!]
Be careful when using the DrawData parameter. Drawing of text tags is very slow
in rhino and since there are a looooot of text tags in such a graph, it may
become unresponsive for quite some time. Definitely save your file before
switching this to True!
    Inputs:
        KnitNetworkDual: The dual graph of the KnitNetwork.
                         {item, KnitDiNetwork)
        PatternData: The topological sorted 2d pattern data optained from the
                     MakePatternData component.
                     {item, PatternData}
        Plane: The plane to draw the graph layout onto.
               {item, plane}
        NodeRadius: The radius (i.e. size) of the nodes to draw.
                    {item, float}
        NodeDisplay: Display nodes either as circles or as squares.
                     [0] = circle
                     [1] = square
                     {item, int}
        PaddingX: The spacing between nodes in plane x-direction.
                  {item, float}
        PaddingY: The spacing between the nodes in plane y-direction.
                  {item, float}
        DirectionalDisplay: Set to True to draw arrows for edges instead of
                            undirected lines.
                            {item, bool}
        DrawData: Set to True to also draw the attributes as text tags. This
                  can be very slow!
                  {item, bool}
    Outputs:
        FlatDual: A 'falt' version of the KnitNetworkDual where all nodes and
                  edges are on the defined plane.
                  {item, KnitDiNetwork}
        NodeCurves: The circles/squares that are used for drawing the nodes.
                    {list, curve}
        WeftEdgeLines: The lines that are used for drawing the 'weft' edges.
                       {list, line}
        WarpEdgeLines: The lines that are used for drawing the 'warp' edges.
                       {list, line}
        TextTags: If DrawData is True, the text tags with all the attributes of
                  nodes and edges.
                  {list, TextGoo}
    Outputs:
    Remarks:
        Author: Max Eschenbach
        License: MIT License
        Version: 200813
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division
from math import sqrt

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# ADDITIONAL MODULE IMPORTS
from ghpythonlib import treehelpers as th
from scriptcontext import doc

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "VisualisePatternData"
ghenv.Component.NickName ="VPD"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "08 Visualisation"

# LOCAL MODULE IMPORTS
try:
    import cockatoo
except ImportError:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

class TextGoo(Grasshopper.Kernel.Types.GH_GeometricGoo[Rhino.Display.Text3d], Grasshopper.Kernel.IGH_BakeAwareData, Grasshopper.Kernel.IGH_PreviewData):
    """
    Custom TextGoo class.
    Based on an example by Giulio Piacentino & David Rutten.
    https://discourse.mcneel.com/t/creating-text-objects-and-outputting-them-as-normal-rhino-geometry/47834/10
    """
    
    #region construction
    def __init__(self, text):
        self.m_value = text
    
    @staticmethod
    def DuplicateText3d(original):
        if original is None: return None
        text = Rhino.Display.Text3d(original.Text, original.TextPlane, original.Height)
        text.Bold = original.Bold,
        text.Italic = original.Italic,
        text.FontFace = original.FontFace
        return text
    
    def DuplicateGeometry(self):
        return TextGoo(TextGoo.DuplicateText3d(self.m_value))
    
    #region properties
    def get_TypeName(self):
        return "3D Text"
        
    def get_TypeDescription(self):
        return "3D Text"
    
    def ToString(self):
        if self.m_value is None: return "<null>"
        return self.m_value.Text
        
    def get_Boundingbox(self):
        if self.m_value is None:
            return Rhino.Geometry.BoundingBox.Empty;
        return self.m_value.BoundingBox;
        
    def GetBoundingBox(self, xform):
        if self.m_value is None:
            return Rhino.Geometry.BoundingBox.Empty
        box = self.m_value.BoundingBox
        corners = xform.TransformList(box.GetCorners())
        return Rhino.Geometry.BoundingBox(corners)
    
    #region methods
    def Transform(self, xform):
        text = TextGoo.DuplicateText3d(self.m_value)
        if text is None: return TextGoo(None)
        
        plane = text.TextPlane
        point = plane.PointAt(1, 1)
        
        plane.Transform(xform)
        point.Transform(xform)
        dd = point.DistanceTo(plane.Origin)
        
        text.TextPlane = plane;
        text.Height *= dd / sqrt(2)
        return TextGoo(text)
        
    def Morph(self, xmorph):
        return self.DuplicateGeometry()

    #region preview
    def get_ClippingBox(self):
        return self.get_Boundingbox()
        
    def DrawViewportWires(self, args):
        if self.m_value is None: return
        args.Pipeline.Draw3dText(self.m_value, args.Color)
      
    def DrawViewportMeshes(self, args):
        # Do not draw in meshing layer.
        pass

    #region baking
    def BakeGeometry(self, doc, att, id):
        id = System.Guid.Empty
        
        if self.m_value is None:
            return false, id
        
        if att is None:
            att = doc.CreateDefaultAttributes()
        
        id = doc.Objects.AddText(self.m_value, att)
        
        return True, id


class VisualisePatternData(component):
    
    def __init__(self):
        super(VisualisePatternData, self).__init__()
        
        self.drawing_nodes = []
        self.drawing_edges = []
        self.drawing_data = []
        self.draw_directional = False
        self.node_display = 0
    
    def get_ClippingBox(self):
        return Rhino.Geometry.BoundingBox()
    
    def DrawViewportWires(self, args):
        try:
            # get display from args
            display = args.Display
            
            # draw all catalogued nodes
            for node in self.drawing_nodes:
                node_display = self.node_display
                if node_display == 0:
                #display.DrawPoint(node[0], node[1], node[2], node[3])
                    display.DrawCircle(node[0], node[1])
                elif node_display == 1:
                    display.DrawCurve(node[0], node[1])
            
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
    
    def node_color(self, data):
        """
        checks the node and returns the appropriate drawing color
        """
        
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
        
        # END BUT NOT LEAF
        if data["end"] and not data["leaf"]:
            if not data["increase"] and not data["decrease"]:
                if data["start"]:
                    nodecol = colStartEnd
                else:
                    nodecol = colEnd
            elif data["increase"] and not data["decrease"]:
                nodecol = colIncreaseEnd
            elif not data["increase"] and data["decrease"]:
                nodecol = colDecreaseEnd
        # END AND LEAF
        elif data["end"] and data["leaf"]:
            if data["start"]:
                nodecol = colStartLeafEnd
            else:
                nodecol = colEndLeaf
        # NO END BUT LEAF
        elif not data["end"] and data["leaf"]:
            if data["start"]:
                nodecol = colStartLeaf
            else:
                nodecol = colLeaf
        # NO END NO LEAF
        elif not data["end"] and not data["leaf"]:
            if data["increase"] and not data["decrease"]:
                nodecol = colIncrease
            elif not data["increase"] and data["decrease"]:
                nodecol = colDecrease
            else:
                if data["color"]:
                    nodecol = System.Drawing.Color.FromArgb(
                                                *data["color"])
                else:
                    nodecol = colRegular
        
        # return the color
        return nodecol
    
    def RunScript(self, KnitNetworkDual, PatternData, Plane, NodeRadius, NodeDisplay, PaddingX, PaddingY, DirectionalDisplay, DrawData):
        
        # set defaults and catch missing params
        if NodeRadius == None:
            NodeRadius = 0.1
        if PaddingX == None:
            PaddingX = NodeRadius * 1.5
        if PaddingY == None:
            PaddingY = NodeRadius * 1.5
        if NodeDisplay == None or NodeDisplay < 0:
            NodeDisplay = 0
        elif NodeDisplay > 1:
            NodeDisplay = 1
        if DirectionalDisplay == None:
            DirectionalDisplay = False
        if Plane == None:
            Plane = Rhino.Geometry.Plane.WorldXY
        
        self.drawing_nodes = []
        self.drawing_edges = []
        self.drawing_data = []
        
        # set directional display
        self.draw_directional = DirectionalDisplay
        self.node_display = NodeDisplay
        
        # set font faces for display/drawing
        nodeFontFace = "Helvetica"
        contourFontFace = "Helvetica"
        weftFontFace = "Helvetica"
        warpFontFace = "Helvetica"
        
        # set edge colors for display/drawing
        contourcol = System.Drawing.Color.Gray
        weftcol = System.Drawing.Color.Blue
        warpcol = System.Drawing.Color.Red
        
        # create a copy version of the knitnetwork
        FlatDual = cockatoo.KnitDiNetwork(KnitNetworkDual)
        
        if FlatDual and PatternData:
            
            # set origin
            origin = Plane.Origin
            origin += Plane.XAxis * NodeRadius
            origin += Plane.YAxis * NodeRadius
            
            # modify the padding according to node radius
            PaddingX += NodeRadius * 2
            PaddingY += NodeRadius * 2
            
            # create containers for the geometry data
            grid = [[] for row in PatternData]
            GraphNodes = []
            edgelines = []
            
            # create containers for the drawing data
            node_drawing_list = []
            edge_drawing_list = []
            data_drawing_list = []
            
            # loop over all the rows of the pattern data
            for i, row in enumerate(PatternData):
                # compute the y-coordinate
                yval = PaddingY * i
                
                # loop over all items in the current row (columns)
                for j, value in enumerate(row):
                    # if the current value is not a placeholder, set the flat node
                    # coordinates and create the node in the layout
                    if value >= 0:
                        # compute point location for flat layout
                        pt = origin + Rhino.Geometry.Vector3d(PaddingX * j, yval, 0)
                        
                        # append point to output list
                        grid[i].append(pt)
                        
                        # set the node coordinates of the flat network
                        FlatDual.node[value]["geo"] = pt
                        FlatDual.node[value]["x"] = pt.X
                        FlatDual.node[value]["y"] = pt.Y
                        FlatDual.node[value]["z"] = pt.Z
                        
                        # create the display geometry
                        if NodeDisplay == 0:
                            graphnode = Rhino.Geometry.Circle(pt, NodeRadius)
                        elif NodeDisplay == 1:
                            recpln = Plane.Clone()
                            recpln.Origin = pt
                            recinterval = Rhino.Geometry.Interval(NodeRadius * -1,
                                                                  NodeRadius)
                            graphnode = Rhino.Geometry.Rectangle3d(recpln,
                                                                   recinterval,
                                                                   recinterval)
                            graphnode = graphnode.ToNurbsCurve()
                        # append geometry to output list
                        GraphNodes.append(graphnode)
                        
                        # get the node data from the dual
                        node_data = FlatDual.node[value]
                        node_color = self.node_color(node_data)
                        node_drawing_list.append((graphnode, node_color))
                        
                        if DrawData:
                            NodeTextPlane = Plane.Clone()
                            NodeTextPlane.Origin = (pt + 
                                Rhino.Geometry.Vector3d(NodeRadius * -0.33,
                                                        NodeRadius * 0.5,
                                                        0))
                            tagTxt = Rhino.Display.Text3d(str(value),
                                                              NodeTextPlane,
                                                              NodeRadius * 0.15)
                            tagTxt.FontFace = "Source Sans Pro"
                            data_drawing_list.append((tagTxt, node_color))
                            
                            nodeLabel = [(k, node_data[k]) for k in node_data
                                         if k != "geo" and
                                            k != "x" and
                                            k != "y" and
                                            k != "z"]
                            nodeLabel = ["{}: {}".format(t[0], t[1])
                                         for t in nodeLabel]
                            nodeLabel.sort()
                            nodeLabel = ["", ""] + nodeLabel
                            nodeLabel = "\n".join(nodeLabel)
                            nodeTxt = Rhino.Display.Text3d(str(nodeLabel),
                                                          NodeTextPlane,
                                                          NodeRadius * 0.06)
                            nodeTxt.FontFace = "Source Sans Pro"
                            data_drawing_list.append((nodeTxt, node_color))
                        
                    else:
                        continue
            
            WeftEdgeLines = []
            WarpEdgeLines = []
            
            # loop over all edges in the dual and create the flat geometry
            # for the layout
            for edge in FlatDual.edges_iter(data=True):
                # get from and to point
                ptA = FlatDual.node[edge[0]]["geo"]
                ptB = FlatDual.node[edge[1]]["geo"]
                # create line
                ln = Rhino.Geometry.Line(ptA, ptB)
                edge[2]["geo"] = ln
                # shorten line according to node radius
                ln = Rhino.Geometry.Line(ln.PointAtLength(NodeRadius),
                                         ln.PointAtLength(ln.Length - NodeRadius))
                # create drawing display
                if not edge[2]["weft"] and not edge[2]["warp"]:
                    edge_drawing_list.append((ln, contourcol))
                    
                    
                    data_drawing_list.append((tagTxt, contourcol))
                elif edge[2]["weft"]:
                    WeftEdgeLines.append(ln)
                    edge_drawing_list.append((ln, weftcol))
                    
                    if DrawData:
                        EdgeTextPlane = Plane.Clone()
                        EdgeTextPlane.Origin = (ln.PointAt(0.5) 
                                                - Rhino.Geometry.Vector3d(
                                                            NodeRadius * 0.4,
                                                            NodeRadius * 0.2,
                                                            0))
                        edgeLabel = [(k, edge[2][k]) for k
                                     in edge[2] if k != "geo"]
                        edgeLabel = ["{}: {}".format(t[0], t[1]) for t
                                     in edgeLabel]
                        edgeLabel.sort()
                        edgeLabel = [str(edge[0]) + "-" +
                                     str(edge[1])] + edgeLabel
                        edgeLabel = "\n".join(edgeLabel)
                        tagTxt = Rhino.Display.Text3d(str(edgeLabel),
                                                      EdgeTextPlane,
                                                      NodeRadius * 0.09)
                        tagTxt.FontFace = "Source Sans Pro"
                        data_drawing_list.append((tagTxt, weftcol))
                    
                elif edge[2]["warp"]:
                    WarpEdgeLines.append(ln)
                    edge_drawing_list.append((ln, warpcol))
                    
                    if DrawData:
                        EdgeTextPlane = Plane.Clone()
                        EdgeTextPlane.Origin = (ln.PointAt(0.5) 
                                                + Rhino.Geometry.Vector3d(
                                                            NodeRadius * 0.1,
                                                            NodeRadius * 0.2,
                                                            0))
                        edgeLabel = [(k, edge[2][k]) for k
                                     in edge[2] if k != "geo"]
                        edgeLabel = ["{}: {}".format(t[0], t[1]) for t
                                     in edgeLabel]
                        edgeLabel.sort()
                        edgeLabel = [str(edge[0]) + "-" +
                                     str(edge[1])] + edgeLabel
                        edgeLabel = "\n".join(edgeLabel)
                        tagTxt = Rhino.Display.Text3d(str(edgeLabel),
                                                      EdgeTextPlane,
                                                      NodeRadius * 0.09)
                        tagTxt.FontFace = "Source Sans Pro"
                        data_drawing_list.append((tagTxt, warpcol))
            
            # set attributes and draw
            self.drawing_nodes = node_drawing_list
            self.drawing_edges = edge_drawing_list
            self.drawing_data = data_drawing_list
            
            TextTags = [TextGoo(t[0]) for t in data_drawing_list]
            
            # return outputs if you have them; here I try it for you:
            return FlatDual, GraphNodes, WeftEdgeLines, WarpEdgeLines, TextTags
        
        else:
            self.drawing_nodes = []
            self.drawing_edges = []
            self.drawing_data = []
