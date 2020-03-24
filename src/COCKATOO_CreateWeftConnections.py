"""Creates 'weft' edges in a given initialized KnitMeshNetwork.
    Inputs:
        Toggle: Set to True to activate the component {item, boolean}
        KnitMeshNetwork: An initialized KnitMeshNetwork. {item, KnitMeshNetwork}
        SplittingIndex: Optional splitting index for splitting the contours into two sets (left and right). If no value or -1 is supplied, the longest contour will be used. {item, integer}
        Precise: If True, the more precise DistanceTo() function will be used instead of DistanceToSquared(). Default is False. {item, boolean}
    Output:
        KnitMeshNetwork: The KnitMeshNetwork with 'weft' connections created. {item, polyline}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200324
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
import cockatoo

ghenv.Component.Name = "CreateWeftConnections"
ghenv.Component.NickName ="CWC"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "9 Utilities"

class CreateWeftConnections(component):
    
    def RunScript(self, Toggle, KMN, SplittingIndex, Precise=False):
        
        if Toggle and KMN:
            # copy the input network to not mess with previous components
            KMN = cockatoo.KnitMeshNetwork(KMN)
            
            if SplittingIndex < 0:
                SplittingIndex = None
            
            # create weft connections on the copy of the network
            KMN.CreateWeftConnections(startIndex=SplittingIndex,
                                      precise=Precise,
                                      verbose=False)
        elif not Toggle and KMN:
            KMN = cockatoo.KnitMeshNetwork(KMN)
        else:
            KMN = Grasshopper.DataTree[object]()
        
        # return outputs if you have them; here I try it for you:
        return KMN