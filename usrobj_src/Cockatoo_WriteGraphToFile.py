"""
Get the segmentation for loop generation and assign segment attributes
to 'weft' edges and vertices.
TODO: Update docstring!
    Inputs:
        Toggle: {item, boolean}
        KnitNetwork: An initialized KnitNetwork. {item, KnitNetwork}
    Output:
        GraphVizGraph: The KnitNetwork with 'weft' connections created. {item, polyline}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200615
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division
import os
import json

# GPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "WriteGraphToFile"
ghenv.Component.NickName ="WGTF"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "08 Visualisation"

# LOCAL MODULE IMPORTS
try:
    import cockatoo
    import networkx as nx
except ImportError:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

class WriteGraphToFile(component):
   
    def ensure_folder(self, foldername):
        """
        Ensures a "JSONGraph" folder inside the GH def folder.
        
        Based on code by Anders Holden Deleuran
        """
        
        if ghdoc.Path:
            folder = os.path.dirname(ghdoc.Path)
            folder = folder + "\\" + foldername
            if not os.path.isdir(folder):
                os.makedirs(folder)
            return folder
    
    def write_graph_to_json(self, graph, file):
        """
        Write a JSON Graph .json file.
        """
        
        json_data = nx.readwrite.adjacency_data(graph)
        
        jf = open(file, 'w')
        json.dump(json_data, jf)
        jf.close()
    
    def write_graph_to_graphml(self, graph, file):
        """
        Write a GraphML .graphml file.
        """
        
        nx.write_graphml(graph, file)
    
    def write_graph_to_gml(self, graph, file):
        """
        Write a GraphML .graphml file.
        """
        
        nx.write_gml(graph, file)
    
    def RunScript(self, Toggle, KN, Name):
        
        if Toggle and KN:
            
            MODE = 2
            
            if MODE == 0:
                folder = self.ensure_folder("JSONGraph")
                file = folder + "\\" + Name + ".json"
                self.write_graph_to_json(KN, file)
            
            elif MODE == 1:
                folder = self.ensure_folder("GraphML")
                file = folder + "\\" + Name + ".graphml"
                self.write_graph_to_graphml(KN, file)
            
            elif MODE == 2:
                folder = self.ensure_folder("GML")
                file = folder + "\\" + Name + ".gml"
                self.write_graph_to_gml(KN, file)
            
            return folder
        
        return Grasshopper.DataTree[object]()