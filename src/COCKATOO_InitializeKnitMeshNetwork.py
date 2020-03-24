"""Initialize KnitMeshNetwok from a set of contours.
    Inputs:
        KnitMeshContours: The contours of the knitting pattern. {item, curve}
        CourseHeight: The course height of the knitting machine. {item, float}
    Output:
        KnitMeshNetwork: The initialized KnitMeshNetwork. {item, KnitMeshNetwork}
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

ghenv.Component.Name = "InitializeKnitMeshNetwork"
ghenv.Component.NickName ="IKMN"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "9 Utilities"

class InitializeKnitMeshNetwork(component):
    
    def RunScript(self, KnitMeshContours, CourseHeight):
        
        if KnitMeshContours and CourseHeight:
            
            # DECLARE OUTPUTS ------------------------------------------------------
            
            # create KnitMeshNetwork (subclass of nx.Graph)
            KMN = cockatoo.KnitMeshNetwork()
            
            # create datatree for vertices output
            Vertices = Grasshopper.DataTree[object]()
            
            # LOOP THROUGH NODES AND FILL NETWORK ----------------------------------
            nodenum = 0
            for i, plc in enumerate(KnitMeshContours):
                # get path and polylinecurve
                ghpath = Grasshopper.Kernel.Data.GH_Path(i)
                
                # compute divisioncount and divide contour
                dc = round(plc.GetLength() / CourseHeight)
                tplc = plc.DivideByCount(dc, True)
                dpts = [plc.PointAt(t) for t in tplc]
                
                # loop through all vertices on the current contour
                for j, vertex in enumerate(dpts):
                    # declare node attributes
                    vx = vertex.X
                    vy = vertex.Y
                    vz = vertex.Z
                    vpos = i
                    vnum = j
                    if j == 0 or j == len(dpts) - 1:
                        vleaf = True
                    else:
                        vleaf = False
                    vend = False
                    vsegment = None
                    
                    # define attribute dictionary
                    vertex_attrs = {"x": vx,
                                    "y": vy,
                                    "z": vz,
                                    "position": vpos,
                                    "num": vnum,
                                    "leaf": vleaf,
                                    "end": vend,
                                    "segment": vsegment,
                                    "geo": vertex}
                    
                    # add nodes to the network
                    KMN.add_node(nodenum, vertex_attrs)
                    # increment counter
                    nodenum += 1
            
            # INITIALIZE CONTOUR EDGES ---------------------------------------------
            
            KMN.InitializeContourEdges()
            
            # MAKE LEAF VERTEX CONNECTIONS -----------------------------------------
            
            KMN.CreateLeafConnections()
        
        else:
            
            KMN = Grasshopper.DataTree[object]()
        
        # return outputs if you have them; here I try it for you:
        return KMN
