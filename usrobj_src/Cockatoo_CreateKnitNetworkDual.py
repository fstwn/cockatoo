"""
Create the dual network of a KnitNetwork. The supplied network should consist
of the finalized 'weft' and 'warp' edges. The resulting dual will have a node
for each cycle (quad or triangle) of the original network, each representing a
stitch for the knitting pattern.
Cycles with two 'warp' and two 'weft' edges represent a regular stitch.
Cycles with one 'warp' and two 'weft' edges represent the start or the end of
a short row.
Cycles with two 'warp' edges and one 'weft' edge represent an increase or
decrease of stitches, relative to the previous or next row of
stitches.
---
[NOTE] This algorithm relies on finding cycles (quads and triangles) for the
supplied network. This is not a trivial task in 3d space - at least to my
knowlege. Assigning a geometrybase to the KnitNetwork on initialization
and choosing cyclesmode 1 or 2 greatly improves reliability!
None the less, success is very dependent on the curvature of the original
surface or mesh used.
---
[WARNING] If the topology of the supplied network is not as 
expected, it will yield unpredictable results.
---
[IMPLEMENTATION DETAIL] N-Gons are deliberately ignored. The output will be of
type KnitDiNetwork.
    Inputs:
        Toggle: Set to True to activate the component.
                {item, bool}
        KnitNetwork: The KnitNetwork to create the dual network to.
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
                    Defaults to [-1].
                    {item, int}
        MergeAdjacentCreases: If True, will merge adjacent 'increase' and
                              'decrease' nodes connected by a 'weft' edge into a
                              single node. This effectively simplifies the
                              pattern, as a decrease is unneccessary to perform
                              if an increase is right beside it - both nodes
                              can be replaced by a single regular node (stitch).
                              Defaults to True.
                              {item, bool}
        MendTrailingRows: If True, will attempt to remove trailing rows at
                          the left and right bounds of the network by moving
                          increases and decreases that occur to the left or
                          right of the previous row inside of the bounds.
                          Defaults to False.
                          {item, bool}
    Outputs:
        KnitNetworkDual: The dual network of the input KnitNetwork.
                     {item, KnitNetwork}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200603
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division
from collections import deque

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# LOCAL MODULE IMPORTS
try:
    from cockatoo.exception import KnitNetworkTopologyError
except ImportError:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "CreateKnitNetworkDual"
ghenv.Component.NickName ="CKND"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "6 KnitNetwork"

class CreateKnitNetworkDual(component):
    
    def RunScript(self, Toggle, KnitNetwork, CyclesMode, MergeAdjacentCreases=True, MendTrailingRows=True):
        
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
            
            # CREATE DUAL ------------------------------------------------------
            try:
                Dual = KnitNetwork.create_dual(
                                    mode=CyclesMode,
                                    merge_adj_creases=MergeAdjacentCreases,
                                    mend_trailing_rows=MendTrailingRows)
            except NotImplementedError as e:
                if MendTrailingRows:
                    Dual = KnitNetwork.create_dual(
                                    mode=CyclesMode,
                                    merge_adj_creases=MergeAdjacentCreases,
                                    mend_trailing_rows=False)
                    rml = self.RuntimeMessageLevel.Warning
                    rMsg = "Not implemented option MendTrailingRows was ignored!"
                    self.AddRuntimeMessage(rml, rMsg)
                    self.AddRuntimeMessage(rml, e.message)
            except Exception as e:
                rml = self.RuntimeMessageLevel.Error
                rMsg = "Dual could not be created for the input network!"
                self.AddRuntimeMessage(rml, rMsg)
                self.AddRuntimeMessage(rml, e.message)
        
        return Dual
