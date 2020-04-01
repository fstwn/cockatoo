"""Creates 'weft' edges in a given initialized KnitNetwork.
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
        Version: 200325
"""

# PYTHON LIBRARY IMPORTS
from __future__ import division

# GPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# CUSTOM MODULE IMPORTS
import Cockatoo

ghenv.Component.Name = "CreateWeftConnections"
ghenv.Component.NickName ="CWC"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "6 KnitNetwork"

class CreateWeftConnections(component):
    
    def RunScript(self, Toggle, KN, SplittingIndex, Precise=False):
        
        if Toggle and KN:
            # copy the input network to not mess with previous components
            KN = Cockatoo.KnitNetwork(KN)
            
            if SplittingIndex < 0:
                SplittingIndex = None
            
            # create weft connections on the copy of the network
            KN.CreateWeftConnections(startIndex=SplittingIndex,
                                      precise=Precise,
                                      verbose=False)
            
        elif not Toggle and KN:
            return KN
        else:
            return Grasshopper.DataTree[object]()
        
        return KN