"""
Initialize preliminary 'weft' connections (edges) and first 'warp' connections
(edges) for a given KnitNetwork.
---
[WARNING] The implementation used is research-level code and not optimized. This
can lead to substantial computation time, depending on size of the mesh, stitch
parameters and hardware of the machine!
    Inputs:
        Toggle: Set to True to activate the component.
                {item, bool}
        KnitNetwork: An initialized KnitNetwork.
                     {item, KnitNetwork}
        SplittingIndex: Optional splitting index for splitting the contours into
                        two sets (left and right). If no value or -1 is
                        supplied, the longest contour will be used.
                        {item, integer}
        ContinuousStart: If True, forces the first row of stitches to be
                         continuous.
                         Defaults to False.
                         {item, bool}
        ContinuousEnd: If True, forces the last row of stitchtes to be
                       continuous.
                       Defaults to False.
                       {item, bool}
        PropagateFromCenter: If True, will propagate left and right set of 
                             contours from the center contour defined by
                             SplittingIndex ( < | > ). Otherwise, the
                             propagation of the contours left to the center will
                             start at the left boundary ( > | > ).
                             Defaults to False.
                             {item, bool}
        Precise: If True, the more precise but slower DistanceTo() function will
                 be used instead of DistanceToSquared().
                 Defaults to False.
                 {item, bool}
    Output:
        KnitNetwork: The KnitNetwork with preliminary 'weft' and 'warp' edges 
                     created.
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
ghenv.Component.Name = "InitializeWeftAndWarpEdges"
ghenv.Component.NickName ="IWAWE"
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

class InitializeWeftAndWarpEdges(component):
    
    def RunScript(self, Toggle, KN, SplittingIndex=None, ContinuousStart=False, ContinuousEnd=False, PropagateFromCenter=False, Precise=False):
        
        if Toggle and KN:
            # copy the input network to not mess with previous components
            KN = cockatoo.KnitNetwork(KN)
            
            if SplittingIndex < 0:
                SplittingIndex = None
            
            # initialize 'weft' edges between 'leaf' nodes
            KN.initialize_leaf_connections()
            
            # create preliminary 'weft' connections on the copy of the network
            KN.initialize_weft_edges(start_index=SplittingIndex,
                                     propagate_from_center=PropagateFromCenter,
                                     force_continuous_start=ContinuousStart,
                                     force_continuous_end=ContinuousEnd,
                                     max_connections=4,
                                     least_connected=False,
                                     precise=Precise,
                                     verbose=False)
            
            # initialize first 'warp' connections
            KN.initialize_warp_edges(contour_set=None,
                                     verbose=False)
            
        elif not Toggle and KN:
            return Grasshopper.DataTree[object]()
        elif not KN:
            rml = self.RuntimeMessageLevel.Warning
            rMsg = "No KnitNetwork input!"
            self.AddRuntimeMessage(rml, rMsg)
            return Grasshopper.DataTree[object]()
        else:
            return Grasshopper.DataTree[object]()
        
        return KN