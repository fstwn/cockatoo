"""
Initialize a KnitNetwork from a set of KnitContours (i.e. isocurves / isolines)
and an optional reference geometry.
---
[NOTE] The ReferenceGeometry is a mesh or surface which is described by the network.
While it is optional, it is **HIGHLY** recommended to provide it, as downstream
methods like meshing or creating a dual might fail without it.
    Inputs:
        KnitContours: The contours of the knitting pattern.
                      {list, curve/polyline}
        CourseHeight: The course height of the knitting machine.
                      {item, float}
        ReferenceGeometry: The reference geometry this network is based on.
                           {item, mesh/surface)
    Output:
        KnitNetwork: The initialized KnitNetwork.
                     {item, KnitNetwork}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200615
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division

# GPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "InitializeKnitNetwork"
ghenv.Component.NickName ="IKN"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "06 KnitNetwork"

# LOCAL MODULE IMPORTS
try:
    import cockatoo
except ImportError:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

class InitializeKnitNetwork(component):
    
    def RunScript(self, KnitContours, CourseHeight, ReferenceGeometry):
        
        if KnitContours and CourseHeight:
            # create KnitNetwork (inherits from nx.Graph)
            KN = cockatoo.KnitNetwork.create_from_contours(KnitContours,
                                                           CourseHeight,
                                                           ReferenceGeometry)
        elif not KnitContours:
            rml = self.RuntimeMessageLevel.Warning
            rMsg = "No KnitContours input!"
            self.AddRuntimeMessage(rml, rMsg)
            return Grasshopper.DataTree[object]()
        elif not CourseHeight:
            rml = self.RuntimeMessageLevel.Warning
            rMsg = "No CourseHeight input!"
            self.AddRuntimeMessage(rml, rMsg)
            return Grasshopper.DataTree[object]()
        else:
            return Grasshopper.DataTree[object]()
        
        # return outputs if you have them; here I try it for you:
        return KN
