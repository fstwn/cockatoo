"""Create preliminary 'weft' connections and first 'warp' connections
for a given initialized KnitNetwork.
    Inputs:
        Toggle: Set to True to activate the component {item, boolean}
        KnitNetwork: An initialized KnitNetwork. {item, KnitNetwork}
        SplittingIndex: Optional splitting index for splitting the contours into two sets (left and right). If no value or -1 is supplied, the longest contour will be used. {item, integer}
        Precise: If True, the more precise DistanceTo() function will be used instead of DistanceToSquared(). Default is False. {item, boolean}
    Output:
        KnitNetwork: The KnitNetwork with 'weft' connections created. {item, polyline}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200414
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
    
    def RunScript(self, Toggle, KN, SplittingIndex, Precise=False):
        
        if Toggle and KN:
            # copy the input network to not mess with previous components
            KN = Cockatoo.KnitNetwork(KN)
            
            if SplittingIndex < 0:
                SplittingIndex = None
            
            # initialize 'weft' edges between 'leaf' nodes
            KN.InitializeLeafConnections()
            
            # create preliminary 'weft' connections on the copy of the network
            KN.InitializeWeftEdges(start_index=SplittingIndex,
                                   include_leaves=True,
                                   max_connections=4,
                                   least_connected=False,
                                   precise=Precise,
                                   verbose=False)
            
            # initialize first 'warp' connections
            KN.InitializeWarpEdges(contour_set=None,
                                   verbose=False)
            
        elif not Toggle and KN:
            return KN
        else:
            return Grasshopper.DataTree[object]()
        
        return KN
