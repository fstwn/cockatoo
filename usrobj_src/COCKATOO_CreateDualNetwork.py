"""
Create the dual network of a KnitNetwork
    Inputs:
        Toggle: Set to True to activate the component. {item, boolean}
        KnitNetwork: The KnitNetwork to create the dual network to. {item, KnitNetwork}
        CyclesMode: Determines how the neighbors of each node are sorted when
                    finding cycles for the network.
                    [-1] equals to using the world XY plane (default)
                     [0] equals to using a plane normal to the origin nodes 
                       closest point on the geometrybase
                     [1] equals to using a plane normal to the average of the 
                       origin and neighbor nodes' closest points on the
                       geometrybase
                     [2] equals to using an average plane between a plane fit to 
                       the origin and its neighbor nodes and a plane normal to 
                       the origin nodes closest point on the geometrybase.
                    Defaults to [-1]. {item, int}
    Outputs:
        DualNetwork: The dual network of the input KnitNetwork. {item, KnitNetwork}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200505
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "CreateDualNetwork"
ghenv.Component.NickName ="CDN"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "6 KnitNetwork"

class CDN(component):
    
    def RunScript(self, Toggle, KnitNetwork, CyclesMode):
        
        # sanitize inputs
        if CyclesMode == None:
            CyclesMode = -1
        elif CyclesMode < 0:
            CyclesMode = -1
        elif CyclesMode > 2:
            CyclesMode = 2
        
        if not KnitNetwork:
            rml = self.RuntimeMessageLevel.Warning
            rMsg = "No KnitNetwork input!"
            self.AddRuntimeMessage(rml, rMsg)
        
        # initialize Output
        Dual = Grasshopper.DataTree[object]()
        
        if Toggle and KnitNetwork:
            # create mesh from knitnetwork
            Dual = KnitNetwork.CreateDual(mode=CyclesMode)
            
            return Dual
        else:
            return Dual
