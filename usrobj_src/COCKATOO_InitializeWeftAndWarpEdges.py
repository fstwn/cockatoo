"""
Initialize preliminary 'weft' connections (edges) and first 'warp' connections
(edges) for a given KnitNetwork.
    Inputs:
        Toggle: Set to True to activate the component {item, boolean}
        KnitNetwork: An initialized KnitNetwork. {item, KnitNetwork}
        SplittingIndex: Optional splitting index for splitting the contours into
                        two sets (left and right). If no value or -1 is
                        supplied, the longest contour will be used.
                        {item, integer}
        ContinuousStart: If True, forces the first row of stitches to be
                         continuous. Defaults to False. {item, bool}
        ContinuousEnd: If True, forces the last row of stitchtes to be
                       continuous. Defaults to False. {item, bool}
        PropagateFromCenter: If True, will propagate left and right set of 
                             contours from the center contour defined by
                             SplittingIndex ( < | > ). Otherwise, the
                             propagation of the contours left to the center will
                             start at the left boundary ( > | > ).
                             Defaults to False.
        Precise: If True, the more precise but slower DistanceTo() function will
                 be used instead of DistanceToSquared(). Default is False.
                 {item, boolean}
    Output:
        KnitNetwork: The KnitNetwork with preliminary 'weft' and 'warp' edges 
                     created. {item, polyline}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200525
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
ghenv.Component.Name = "InitializeWeftAndWarpEdges"
ghenv.Component.NickName ="IWAWE"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "6 KnitNetwork"

class InitializeWeftAndWarpEdges(component):
    
    def RunScript(self, Toggle, KN, SplittingIndex=None, ContinuousStart=False, ContinuousEnd=False, PropagateFromCenter=False, Precise=False):
        
        if Toggle and KN:
            # copy the input network to not mess with previous components
            KN = Cockatoo.KnitNetwork(KN)
            
            if SplittingIndex < 0:
                SplittingIndex = None
            
            # initialize 'weft' edges between 'leaf' nodes
            KN.InitializeLeafConnections()
            
            # create preliminary 'weft' connections on the copy of the network
            KN.InitializeWeftEdges(start_index=SplittingIndex,
                                   propagate_from_center=PropagateFromCenter,
                                   force_continuous_start=ContinuousStart,
                                   force_continuous_end=ContinuousEnd,
                                   max_connections=4,
                                   least_connected=False,
                                   precise=Precise,
                                   verbose=False)
            
            # initialize first 'warp' connections
            KN.InitializeWarpEdges(contour_set=None,
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