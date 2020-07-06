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
        License: MIT License
        Version: 200705
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
ghenv.Component.SubCategory = "09 Pattern Data"

class WriteKnittingPatternToBitmap(component):
    
    def RunScript(self, Write, PixelData, Path):
        
        if Write and PixelData and Path:
            # reverse the data so that the start is at the bottom of the image
            PixelData.reverse()
            
            # Get number of columns and rows in csv data
            columns = max([len(row) for row in PixelData])
            rows = len(PixelData)
            
            # initialize empty bitmap
            bitmap = System.Drawing.Bitmap(columns, rows)
            
            # add pixels
            for i in range(columns):
                for j in range(rows):
                    
                    try:
                        col = PixelData[j][i]
                    except IndexError:
                        col = System.Drawing.Color.Gray
                    
                    # set pixel
                    bitmap.SetPixel(i, j, col)
                    
            # save to file
            bitmap.Save(path.normpath(Path.strip("\n\r")),
                        System.Drawing.Imaging.ImageFormat.Bmp)
        
        else:
            if not PixelData:
                rml = self.RuntimeMessageLevel.Warning
                self.AddRuntimeMessage(rml, "No PixelData input!")
            if not Path:
                rml = self.RuntimeMessageLevel.Warning
                self.AddRuntimeMessage(rml, "No Path input!")
