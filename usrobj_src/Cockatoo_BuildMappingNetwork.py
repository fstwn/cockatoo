"""
Assign 'segment' attributes to nodes and 'weft' edges based on their position
between two 'end' nodes and build a mapping network used for final loop
generation.
    Inputs:
        Toggle: Set to true to activate
                {item, bool}
        KnitNetwork: An initialized KnitNetwork with preliminary 'weft' and
                     first 'warp' connections (edges).
                     {item, KnitNetwork}
    Output:
        KnitNetwork: The KnitNetwork, consisting only of 'warp' edges and their
                     'end' nodes but with an embedded MappingNetwork for final
                     loop generation.
                     {item, KnitNetwork}
        KnitMappingNetwork: Only the mapping network of the KnitNetwork.
                            NOTE The mapping network is also embedded in the
                            KnitNetwork during this step and can be accessed by
                            the KnitNetwork.MappingNetwork property. It is
                            returned here as a seperate output for reasons of
                            visualisation, analysis and troubleshooting.
                            {item, KnitMappingNetwork}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200615
"""

# GPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "BuildMappingNetwork"
ghenv.Component.NickName ="BMN"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "06 KnitNetwork"

# LOCAL MODULE IMPORTS
try:
    import cockatoo
except ImportError:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

class BuildMappingNetwork(component):
    
    def RunScript(self, Toggle, KN):
        
        if Toggle and KN:
            # copy the input network to not mess with previous components
            KN = cockatoo.KnitNetwork(KN)
            
            # CREATE SEGMENTATION AND ASSIGN ATTRIBUTES ------------------------
            
            KN.assign_segment_attributes()
            
            # CHECK THE RESULTS ------------------------------------------------
            
            for edge in KN.edges(data=True):
                s = edge[2]["segment"]
                w = edge[2]["weft"]
                if w and not s:
                    vStr = "'weft' edge {} has no segment value!"
                    vStr = vStr.format((edge[0], edge[1]))
                    rml = self.RuntimeMessageLevel.Warning
                    self.AddRuntimeMessage(rml, vStr)
            
            for node in KN.nodes(data=True):
                e = node[1]["end"]
                s = node[1]["segment"]
                if not s:
                    if not e:
                        vStr = "node {} has no segment value!"
                        vStr = vStr.format(node[0])
                        rml = self.RuntimeMessageLevel.Warning
                        self.AddRuntimeMessage(rml, vStr)
            
            # CREATE MAPPING NETWORK -------------------------------------------
            
            KN.create_mapping_network()
            
        elif not Toggle and KN:
            return KN
        elif Toggle and not KN:
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, "No KnitNetwork input!")
            return Grasshopper.DataTree[object](), Grasshopper.DataTree[object]()
        
        # return outputs if you have them; here I try it for you:
        return KN, KN.mapping_network