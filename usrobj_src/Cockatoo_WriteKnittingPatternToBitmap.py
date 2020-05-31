"""
Write knitting pattern data to a bitmap file.
---
Based on an example by Anders Holden Deleuran
https://discourse.mcneel.com/t/write-a-bitmap-pixel-by-pixel-in-python/81116/2
    Inputs:
        Toggle: Set to True to save the bitmap file.
                {item, bool}
        PatternData: The knitting pattern data to write to the bitmap file.
                     {item, data}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200531
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division
from os import path

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "WriteKnittingPatternToBitmap"
ghenv.Component.NickName ="WKPTB"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "8 Pattern Data"

class WriteKnittingPatternToBitmap(component):
    
    def RunScript(self, Write, PatternData, Path):
        
        if Write and PatternData and Path:
            # reverse pattern data so that the start is at the bottom of the image
            PatternData.reverse()
            # Get number of columns and rows in csv data
            columns = len(PatternData[0])
            rows = len(PatternData)
            
            # initialize empty bitmap
            bitmap = System.Drawing.Bitmap(columns, rows)
            
            # add pixels
            for i in range(columns):
                for j in range(rows):
                    # Get data in cell
                    try:
                        cd = PatternData[j][i]
                    except IndexError:
                        cd = "XXXXX"
                    
                    # Make color depending on cell data
                    if cd in ["k", "K"]:
                        col = System.Drawing.Color.White
                    elif cd in ["e", "E"]:
                        col = System.Drawing.Color.Blue
                    elif cd in ["i", "I"]:
                        col = System.Drawing.Color.Red
                    elif cd in ["d", "D"]:
                        col = System.Drawing.Color.DarkRed
                    elif cd in ["o", "O"]:
                        col = System.Drawing.Color.Gray
                    elif cd == "XXXXX":
                        col = System.Drawing.Color.Black
                    # Set pixel
                    bitmap.SetPixel(i, j, col)
                    
            # Save to file
            bitmap.Save(path.normpath(Path.strip("\n\r")), System.Drawing.Imaging.ImageFormat.Bmp)