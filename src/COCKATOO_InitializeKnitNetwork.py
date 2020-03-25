"""Initialize KnitNetwork from a set of contours.
    Inputs:
        KnitContours: The contours of the knitting pattern. {item, curve}
        CourseHeight: The course height of the knitting machine. {item, float}
    Output:
        KnitNetwork: The initialized KnitNetwork. {item, KnitNetwork}
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

ghenv.Component.Name = "InitializeKnitNetwork"
ghenv.Component.NickName ="IKN"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "6 KnitNetwork"

class InitializeKnitNetwork(component):
    
    def RunScript(self, KnitContours, CourseHeight):
        
        if KnitContours and CourseHeight:
            # DECLARE OUTPUTS ------------------------------------------------------
            
            # create KnitNetwork (inherits from nx.Graph)
            KN = Cockatoo.KnitNetwork()
            
            # create datatree for vertices output
            Vertices = Grasshopper.DataTree[object]()
            
            # LOOP THROUGH NODES AND FILL NETWORK ----------------------------------
            nodenum = 0
            for i, plc in enumerate(KnitContours):
                # get path and polylinecurve
                ghpath = Grasshopper.Kernel.Data.GH_Path(i)
                
                # compute divisioncount and divide contour
                dc = round(plc.GetLength() / CourseHeight)
                tplc = plc.DivideByCount(dc, True)
                dpts = [plc.PointAt(t) for t in tplc]
                
                # loop through all vertices on the current contour
                for j, vertex in enumerate(dpts):
                    # declare node attributes
                    vpos = i
                    vnum = j
                    if j == 0 or j == len(dpts) - 1:
                        vleaf = True
                    else:
                        vleaf = False
                    
                    KN.NodeFromPoint3d(nodenum,
                                        vertex,
                                        vpos,
                                        vnum,
                                        vleaf,
                                        False,
                                        None)
                    
                    # increment counter
                    nodenum += 1
            
            # INITIALIZE CONTOUR EDGES ---------------------------------------------
            
            KN.InitializePositionContourEdges()
            
            # MAKE LEAF VERTEX CONNECTIONS -----------------------------------------
            
            KN.CreateLeafConnections()
        
        else:
            return Grasshopper.DataTree[object]()
        
        # return outputs if you have them; here I try it for you:
        return KN
