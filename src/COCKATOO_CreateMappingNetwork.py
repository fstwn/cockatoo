"""
Creates a mapping network from segmented weft edges.
TODO: Update docstring!
    Inputs:
        Toggle: Set to true to activate {item, boolean}
        KnitMeshNetwork: An initialized KnitMeshNetwork. {item, KnitMeshNetwork}
    Output:
        KnitMeshNetwork: The KnitMeshNetwork with 'weft' connections created. {item, polyline}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200324
"""

# PYTHON LIBRARY IMPORTS
from __future__ import division
import operator
from collections import deque

# GPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# CUSTOM MODULE IMPORTS
import cockatoo

ghenv.Component.Name = "CreateMappingNetwork"
ghenv.Component.NickName ="CMN"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "6 KnitMeshNetwork"

class CreateMappingNetwork(component):
    
    def RunScript(self, Toggle, KMN):
        
        if Toggle and KMN:
            # copy the input network to not mess with previous components
            MappingNetwork = cockatoo.KnitMeshNetwork()
            
            # get all edges by segment
            
            WeftEdges = sorted(KMN.WeftEdges, key=lambda x: x[2]["segment"])
            WarpEdges = KMN.WarpEdges
            
            segment_ids = deque()
            for edge in WeftEdges:
                segment_id = edge[2]["segment"]
                if not segment_id in segment_ids:
                    segment_ids.append(segment_id)
            
            for id in segment_ids:
                segment_edges = [e for e in WeftEdges if e[2]["segment"] == id]
                segment_edges.sort(key=lambda x: x[0])
                
                startNode = (id[0], KMN.node[id[0]])
                endNode = (id[1], KMN.node[id[1]])
                
                segment_geo = [e[2]["geo"] for e in segment_edges]
                
                res = MappingNetwork.CreateMappingEdge(startNode, endNode, segment_geo)
                
                if not res:
                    print id
            
            [MappingNetwork.add_edge(e[0], e[1], e[2]) for e in WarpEdges]
            
            return MappingNetwork
        elif not Toggle and KMN:
            pass
        else:
            KMN = Grasshopper.DataTree[object]()
        
        # return outputs if you have them; here I try it for you:
        return KMN