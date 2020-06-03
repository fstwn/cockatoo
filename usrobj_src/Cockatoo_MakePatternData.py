"""
Make knitting pattern data from a KnitNetwork dual. This will convert the input
dual network into a directed acyclic graph by grouping all 'weft' edge chains
and 'warp' edge chains. Then, a topological sort is performed on that graph to
sort the stitches into rows and columns.
---
[NOTE] If this fails, something is wrong with the topology or geometry of the
dual network or the underlying KnitNetwork and thus it can not be represented as
a directed acyclic graph.
---
For more details on the underlying concepts see
https://en.wikipedia.org/wiki/Directed_acyclic_graph
https://en.wikipedia.org/wiki/Topological_sorting
    Inputs:
        Toggle: Set to True to activate the component. {item, boolean}
        KnitNetworkDual: The input dual network of the KnitNetwork.
                         {item, KnitDiNetwork}
        Consolidate: If True, will try to consolidate the pattern data
                     Defaults to True.
                     {item, bool}
    Outputs:
        PatternData: {list/tree, int}
        CommandData: {list/tree, int}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200603
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# THIRD PARTY MODULE IMPORTS
from ghpythonlib import treehelpers as th

# LOCAL MODULE IMPORTS
try:
    from cockatoo.exception import KnitNetworkTopologyError
except ImportError:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "MakePatternData"
ghenv.Component.NickName ="MPD"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "8 Pattern Data"

class MakePatternData(component):
    
    def RunScript(self, DualNetwork, Consolidate=True):
        
        PatternData = Grasshopper.DataTree[object]()
        
        if DualNetwork:
            # CREATE CSV DATA (ROWS AND COLUMNS) -------------------------------
            
            try:
                PatternData = DualNetwork.make_pattern_data(consolidate=Consolidate)
            except Exception as e:
                rml = self.RuntimeMessageLevel.Error
                rMsg = "Could not perform topological sort on input network!"
                self.AddRuntimeMessage(rml, rMsg)
                print(e.message)
            
            # CONVERT CSV DATA TO COMMANDS -------------------------------------
            
            try:
                cmd_rows = []
                for i, row in enumerate(PatternData):
                    cmd_row = []
                    for node in row:
                        if node < 0:
                            cmd_row.append("O")
                        else:
                            node_data = DualNetwork.node[node]
                            if node_data["end"]:
                                cmd_row.append("E")
                            elif node_data["increase"]:
                                cmd_row.append("I")
                            elif node_data["decrease"]:
                                cmd_row.append("D")
                            else:
                                cmd_row.append("K")
                    cmd_rows.append(cmd_row)
            except Exception as e:
                rml = self.RuntimeMessageLevel.Error
                rMsg = "Could not convert rows to commands!"
                self.AddRuntimeMessage(rml, rMsg)
                print(e.message)
        else:
            rml = self.RuntimeMessageLevel.Warning
            rMsg = "No DualNetwork input!"
            self.AddRuntimeMessage(rml, rMsg)
        
        return PatternData, cmd_rows