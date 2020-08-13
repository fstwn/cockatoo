"""
Make knitting pattern data from a KnitNetwork dual. This will convert the input
dual network into a directed acyclic graph by grouping all 'weft' edge chains
and 'warp' edge chains. Then, a topological sort is performed on that graph to
sort the stitches into rows and columns.
---
[NOTE] If this fails, something is wrong with the topology or geometry of the
dual network or the underlying KnitNetwork and thus it can not be represented as
a directed acyclic graph.
---
[WARNING]
SAVE YOUR FILE before activating this! It can crash rhino and grasshopper for
reasons currently unknown. 
---
For more details on the underlying concepts see
https://en.wikipedia.org/wiki/Directed_acyclic_graph
https://en.wikipedia.org/wiki/Topological_sorting
    Inputs:
        Toggle: Set to True to activate the component. {item, boolean}
        KnitNetworkDual: The input dual network of the KnitNetwork.
                         {item, KnitDiNetwork}
        Consolidate: If True, will try to consolidate the pattern data
                     Defaults to False.
                     {item, bool}
        ColorMode: Determines how node colors wil be treated when generating
                   the pattern data.
                   [0] will prioritize colors for instructions like increases
                       or decreases over the 'color' attribute of the node if
                       set.
                   [1] will prioritize the 'color' attribute of the node if set.
                   [2] will create a blended color between the instruction color
                       and the node color specified through the 'color'
                       attribute.
                   Defaults to [0].
                   {item, int}
        FillerColor: Color to use for filling pixels without stitch information.
                     Defaults to Black.
                     {item, System.Drawing.Color}
        StitchColor: Color to use for regular stitch pixels if no 'color'
                     attribute is assigned to the node.
                     Defaults to White.
                     {item, System.Drawing.Color}
        IncreaseColor: Color to use for stitch pixels marked as 'increase'.
                       Defaults to Green.
                       {item, System.Drawing.Color}
        DecreaseColor: Color to use for stitch pixels marked as 'decrease'.
                       Defaults to Orange.
                       {item, System.Drawing.Color}
        EndColor: Color to use for stitch pixels marked as 'end'.
                  Defaults to Blue.
                  {item, System.Drawing.Color}
    Outputs:
        PatternData: The 2d pattern data as a matrix of rows and columns.
                     Contains the node indices. The value '-1' is used as a
                     filler.
                     {tuple, int}
        PixelData: The 2d pixel data as a matrix of rows and columns.
                   Contains the colors of each stitch as as System Color.
                   {tuple, System.Drawing.Color}
    Remarks:
        Author: Max Eschenbach
        License: MIT License
        Version: 200813
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# THIRD PARTY MODULE IMPORTS
from ghpythonlib import treehelpers as th

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "MakePatternData"
ghenv.Component.NickName ="MPD"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "09 Pattern Data"

# LOCAL MODULE IMPORTS
try:
    import cockatoo
except ImportError:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

class MakePatternData(component):
    
    def RunScript(self, Toggle, DualNetwork, Consolidate, ColorMode, FillerColor, StitchColor, IncreaseColor, DecreaseColor, EndColor):
        
        # set defaults and snitize inputs
        if Consolidate == None:
            Consolidate=False
        if ColorMode == None or ColorMode < 0:
            ColorMode = 0
        elif ColorMode > 2:
            ColorMode = 2
        if FillerColor == None:
            FillerColor = System.Drawing.Color.Black
        if StitchColor == None:
            StitchColor = System.Drawing.Color.White
        if IncreaseColor == None:
            IncreaseColor = System.Drawing.Color.Green
        if DecreaseColor == None:
            DecreaseColor = System.Drawing.Color.Orange
        if EndColor == None:
            EndColor = System.Drawing.Color.Blue
        
        PatternData = Grasshopper.DataTree[object]()
        PixelData = Grasshopper.DataTree[object]()
        
        if Toggle and DualNetwork:
            # CREATE PATTERN DATA (ROWS AND COLUMNS) ---------------------------
            
            try:
                PatternData = DualNetwork.make_pattern_data(
                                                    consolidate=Consolidate)
                PatternData = tuple([tuple(row) for row in PatternData])
            except Exception as e:
                rml = self.RuntimeMessageLevel.Error
                rMsg = "Could not perform topological sort on input network!"
                self.AddRuntimeMessage(rml, rMsg)
                print(e.message)
            
            # CONVERT PATTERN DATA TO PIXELS -----------------------------------
            try:
                PixelData = []
                for i, row in enumerate(PatternData):
                    pixel_row = []
                    for node in row:
                        # set filler color if this is not a valid node
                        if node < 0:
                            pixel_row.append(FillerColor)
                            continue
                        
                        # get node data and color
                        node_data = DualNetwork.node[node]
                        node_col = node_data["color"]
                        
                        # END NODE PIXEL COLOR ---------------------------------
                        if node_data["end"]:
                            if node_col and ColorMode == 1:
                                syscol = System.Drawing.Color.FromArgb(
                                                            *node_col)
                                pixel_row.append(syscol)
                            elif node_col and ColorMode == 2:
                                rgbcol = (EndColor.R,
                                          EndColor.G,
                                          EndColor.B)
                                blend = cockatoo.utilities.blend_colors(
                                                    rgbcol,
                                                    node_col)
                                sysblend = System.Drawing.Color.FromArgb(
                                                            *blend)
                                pixel_row.append(sysblend)
                            else:
                                if node_data["increase"]:
                                    pixel_row.append(IncreaseColor)
                                elif node_data["decrease"]:
                                    pixel_row.append(DecreaseColor)
                                else:
                                    pixel_row.append(EndColor)
                        
                        # INCREASE NODE PIXEL COLOR ----------------------------
                        elif node_data["increase"]:
                            if node_col and ColorMode == 1:
                                syscol = System.Drawing.Color.FromArgb(
                                                            *node_col)
                                pixel_row.append(syscol)
                            elif node_col and ColorMode == 2:
                                rgbcol = (IncreaseColor.R,
                                          IncreaseColor.G,
                                          IncreaseColor.B)
                                blend = cockatoo.utilities.blend_colors(
                                                    rgbcol,
                                                    node_col)
                                sysblend = System.Drawing.Color.FromArgb(
                                                            *blend)
                                pixel_row.append(sysblend)
                            else:
                                pixel_row.append(IncreaseColor)
                        
                        # DECREASE NODE PIXEL COLOR ----------------------------
                        elif node_data["decrease"]:
                            if node_col and ColorMode == 1:
                                syscol = System.Drawing.Color.FromArgb(
                                                            *node_col)
                                pixel_row.append(syscol)
                            elif node_col and ColorMode == 2:
                                rgbcol = (DecreaseColor.R,
                                          DecreaseColor.G,
                                          DecreaseColor.B)
                                blend = cockatoo.utilities.blend_colors(
                                                    rgbcol,
                                                    node_col)
                                sysblend = System.Drawing.Color.FromArgb(
                                                            *blend)
                                pixel_row.append(sysblend)
                            else:
                                pixel_row.append(DecreaseColor)
                        
                        # REGULAR NODE PIXEL COLOR -----------------------------
                        else:
                            if node_col:
                                syscol = System.Drawing.Color.FromArgb(
                                                                *node_col)
                                pixel_row.append(syscol)
                            else:
                                pixel_row.append(StitchColor)
                    
                    # append row to pixel data
                    PixelData.append(pixel_row)
                
                PixelData = tuple([tuple(row) for row in PixelData])
                
            except Exception as e:
                rml = self.RuntimeMessageLevel.Error
                rMsg = "Could not convert pattern data to pixel colors!"
                self.AddRuntimeMessage(rml, rMsg)
                print(e.message)
        
        elif Toggle and not DualNetwork:
            rml = self.RuntimeMessageLevel.Warning
            rMsg = "No DualNetwork input!"
            self.AddRuntimeMessage(rml, rMsg)
        
        return PatternData, PixelData