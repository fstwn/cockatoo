"""
Writes a Graph to different data formats. The graph can be a KnitNetwork or a
graph prepared for GraphViz / Gephi.
---
Code for writing graph to dot file by Anders Holden Deleuran.
    Inputs:
        Toggle: Set to True to write the file.
                {item, boolean}
        Graph: A graph to write to the file. Can be either a KnitNetwork or a
               graph prepared for GraphViz / Gephi.
               {item, Graph / KnitNetwork}
        FileFormat: Selection of a file format used for writing. Can be GraphML,
                    JSON, GML or DOT.
                    [0] = GraphML
                    [1] = JSON
                    [2] = GML
                    [3] = DOT
                    Defaults to 0.
                    {item, int}
        Name: The filename of the file to write.
              {item, str}
    Output:
        Folder: The folder were the file was written.
                {item, str}
    Remarks:
        Author: Max Eschenbach
        License: MIT License
        Version: 200809
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
        Ensures a specific subfolder inside the GH def folder.
        
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
        Write a GML .gml file.
        """
        
        nx.write_gml(graph, file)
    
    def write_graph_to_dot(self, graph, file, label="", dpi=72, node_sep=None):
        """
        Write and edit a dot file. Implements the pydot and dot_parser modules.
        
        Based on code by Anders Holden Deleuran.
        """
        
        nx.write_dot(graph, file)
        
        # Get the lines in the dot file
        df = open(file, 'r')
        df_lines = df.readlines()
        df.close()
        
        # Add additional properties to the dot file
        df_lines.insert(1, 'label="' + str(label) + '" dpi=' + str(dpi) + ' overlap=scalexy nodesep=' + str(node_sep) + ' rankdir=BT' + ';\n')
        df_string = ''.join(df_lines)
        
        # Open and overwrite dot file
        df = open(file, 'w')
        df.write(df_string)
        df.close()
    
    def RunScript(self, Toggle, Graph, FileFormat, Name):
        
        if FileFormat == None or FileFormat < 0:
            FileFormat = 0
        elif FileFormat > 3:
            FileFormat = 3
        
        if Toggle and Graph and FileFormat != None and Name:
            if FileFormat == 0:
                if isinstance(Graph, cockatoo.KnitNetworkBase):
                    Graph = cockatoo.KnitNetwork(Graph)
                    # sanitize graph attributes
                    if Graph.graph.has_key("reference_geometry"):
                        del Graph.graph["reference_geometry"]
                    # sanitize nodes
                    for node in Graph.node:
                        if Graph.node[node].has_key("geo"):
                            del Graph.node[node]["geo"]
                        for key in Graph.node[node]:
                            Graph.node[node][key] = str(Graph.node[node][key])
                    # sanitize edges
                    for edge in Graph.edges_iter(data=True):
                        if edge[2].has_key("geo"):
                            del edge[2]["geo"]
                        for key in edge[2]:
                            edge[2][key] = str(edge[2][key])
                
                folder = self.ensure_folder("GraphML")
                file = folder + "\\" + Name + ".graphml"
                self.write_graph_to_graphml(Graph, file)
            
            elif FileFormat == 1:
                if isinstance(Graph, cockatoo.KnitNetworkBase):
                    Graph = cockatoo.KnitNetwork(Graph)
                    # sanitize graph attributes
                    if Graph.graph.has_key("reference_geometry"):
                        del Graph.graph["reference_geometry"]
                    # sanitize nodes
                    for node in Graph.node:
                        if Graph.node[node].has_key("geo"):
                            del Graph.node[node]["geo"]
                        for key in Graph.node[node]:
                            Graph.node[node][key] = str(Graph.node[node][key])
                    # sanitize edges
                    for edge in Graph.edges_iter(data=True):
                        if edge[2].has_key("geo"):
                            del edge[2]["geo"]
                        for key in edge[2]:
                            edge[2][key] = str(edge[2][key])
                
                folder = self.ensure_folder("JSONGraph")
                file = folder + "\\" + Name + ".json"
                self.write_graph_to_json(Graph, file)
            
            elif FileFormat == 2:
                if isinstance(Graph, cockatoo.KnitNetworkBase):
                    Graph = cockatoo.KnitNetwork(Graph)
                    # sanitize graph attributes
                    if Graph.graph.has_key("reference_geometry"):
                        del Graph.graph["reference_geometry"]
                    # sanitize nodes
                    for node in Graph.node:
                        if Graph.node[node].has_key("geo"):
                            del Graph.node[node]["geo"]
                        for key in Graph.node[node]:
                            Graph.node[node][key] = str(Graph.node[node][key])
                    # sanitize edges
                    for edge in Graph.edges_iter(data=True):
                        if edge[2].has_key("geo"):
                            del edge[2]["geo"]
                        for key in edge[2]:
                            edge[2][key] = str(edge[2][key])
                
                folder = self.ensure_folder("GML")
                file = folder + "\\" + Name + ".gml"
                self.write_graph_to_gml(Graph, file)
            
            elif FileFormat == 3:
                if isinstance(Graph, cockatoo.KnitNetworkBase):
                    Graph = cockatoo.KnitNetwork(Graph)
                    # sanitize graph attributes
                    if Graph.graph.has_key("reference_geometry"):
                        del Graph.graph["reference_geometry"]
                    # sanitize nodes
                    for node in Graph.node:
                        if Graph.node[node].has_key("geo"):
                            del Graph.node[node]["geo"]
                        for key in Graph.node[node]:
                            Graph.node[node][key] = str(Graph.node[node][key])
                    # sanitize edges
                    for edge in Graph.edges_iter(data=True):
                        if edge[2].has_key("geo"):
                            del edge[2]["geo"]
                        for key in edge[2]:
                            edge[2][key] = str(edge[2][key])
                
                folder = self.ensure_folder("Dot")
                file = folder + "\\" + Name + ".dot"
                self.write_graph_to_dot(Graph, file)
            
            return folder
        else:
            if Toggle and not Graph:
                rml = self.RuntimeMessageLevel.Warning
                self.AddRuntimeMessage(rml, "No Graph / KnitNetwork input!")
            if Toggle and not Name:
                rml = self.RuntimeMessageLevel.Warning
                self.AddRuntimeMessage(rml, "No Name input!")
        
        return Grasshopper.DataTree[object]()