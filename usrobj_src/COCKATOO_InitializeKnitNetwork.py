"""
Initialize a KnitNetwork from a set of KnitContours (i.e. isocurves / isolines)
and an optional GeometryBase.
The GeometryBase is a mesh or surface which should be described by the
network. While it is optional, it is **HIGHLY** recommended to provide it!
    Inputs:
        KnitContours: The contours of the knitting pattern. {item, curve}
        CourseHeight: The course height of the knitting machine. {item, float}
        GeometryBase: The geometry his network is based on. {item, mesh/surface)
    Output:
        KnitNetwork: The initialized KnitNetwork. {item, KnitNetwork}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200506
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division

# GPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# LOCAL MODULE IMPORTS
import Cockatoo

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "InitializeKnitNetwork"
ghenv.Component.NickName ="IKN"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "6 KnitNetwork"

class InitializeKnitNetwork(component):
    
    def RunScript(self, KnitContours, CourseHeight, GeometryBase):
        
        if KnitContours and CourseHeight:
            # create KnitNetwork (inherits from nx.Graph)
            KN = Cockatoo.KnitNetwork.CreateFromContours(KnitContours,
                                                         CourseHeight,
                                                         GeometryBase)
        else:
            return Grasshopper.DataTree[object]()
        
        # return outputs if you have them; here I try it for you:
        return KN
