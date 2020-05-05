"""
Create a mesh from a KnitNetwork by finding the cycles (faces) of the
network.
    Inputs:
        Toggle: Set to True to activate the component. {item, boolean}
        KnitNetwork: The KnitNetwork to mesh. {item, KnitNetwork}
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
        Mesh: The Rhino mesh. {item, mesh}
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
ghenv.Component.Name = "CreateMeshFromKnitNetwork"
ghenv.Component.NickName ="CMFKN"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "6 KnitNetwork"

class CMFKN(component):
    
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
        
        # initialize Mesh
        Mesh = Grasshopper.DataTree[Rhino.Geometry.Mesh]()
        
        if Toggle and KnitNetwork:
            # create mesh from knitnetwork
            Mesh = KnitNetwork.CreateMesh(mode=CyclesMode)
            
            return Mesh
        else:
            return Mesh
