"""
Create a mesh from a KnitNetwork by finding the cycles (faces) of the
network.
---
[NOTE] This algorithm relies on finding cycles (quads and triangles) for the
supplied network. This is not a trivial task in 3d space - at least to my
knowledge. Assigning a geometrybase to the KnitNetwork on initialization
and choosing cyclesmode 1 or 2 greatly improves reliability!
None the less, success is very dependent on the curvature of the original
surface or mesh used.
---
[IMPLEMENTATION DETAIL] N-Gons are deliberately deactivated but can be activated
when editing the function call inside the scripting component and increasing
the max_valence value.
    Inputs:
        Toggle: Set to True to activate the component.
                {item, boolean}
        KnitNetwork: The KnitNetwork to mesh.
                     {item, KnitNetwork}
        CyclesMode: Determines how the neighbors of each node are sorted when
                    finding the cycles of the network.
                    [-1] equals to using the world XY plane (default)
                    [0] equals to using a plane normal to the origin nodes 
                        closest point on the geometrybase
                    [1] equals to using a plane normal to the average of the 
                        origin and neighbor nodes' closest points on the
                        geometrybase
                    [2] equals to using an average plane between a plane fit to 
                        the origin and its neighbor nodes and a plane normal to 
                        the origin nodes closest point on the geometrybase.
                    Defaults to -1.
                    {item, int}
    Outputs:
        Mesh: The Rhino mesh. {item, mesh}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200608
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
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "6 KnitNetwork"

# LOCAL MODULE IMPORTS
try:
    from cockatoo import KnitNetwork
    from cockatoo import KnitDiNetwork
except ImportError:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

class CreateMeshFromKnitNetwork(component):
    
    def RunScript(self, Toggle, KN, CyclesMode):
        
        # sanitize inputs
        if CyclesMode == None:
            CyclesMode = -1
        elif CyclesMode < 0:
            CyclesMode = -1
        elif CyclesMode > 2:
            CyclesMode = 2
        
        if not KN:
            rml = self.RuntimeMessageLevel.Warning
            rMsg = "No KnitNetwork input!"
            self.AddRuntimeMessage(rml, rMsg)
        
        # initialize Mesh
        Mesh = Grasshopper.DataTree[Rhino.Geometry.Mesh]()
        
        if Toggle and KN:
            # create mesh from knitnetwork
            if isinstance(KN, KnitNetwork):
                Mesh = KN.create_mesh(mode=CyclesMode,
                                      max_valence=4)
            elif isinstance(KN, KnitDiNetwork):
                if KN.verify_dual_form():
                    Mesh = KnitNetwork(KN).create_mesh(mode=CyclesMode,
                                                      max_valence=4)
        return Mesh
