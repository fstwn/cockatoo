"""
Listens for changes in geometry and sends a True value if anything changes
(this can be used to reset the Kangaroo Solver for example).
    Inputs:
        Geometry: This is the geometry that is being watched for changes.
                  {tree, geometry}
        Enable: If True, the PipelineWatchdog is active. If false, it isn't.
                Connect a Toggle to switch it on and off.
                {item, boolean}
    Outputs:
        Reset: Triggers a True when anything has changed, otherwise false.
               {item, boolean}
    Remarks:
        Author: Max Eschenbach
        License: MIT License
        Version: 2010105
"""

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# CUSTOM RHINO IMPORTS
from scriptcontext import sticky as st
from ghpythonlib import treehelpers as th

ghenv.Component.Name = "GeometryWatchDog"
ghenv.Component.NickName = "GWD"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "01 Pipeline Controlling"

class GeometryWatchDog(component):
    
    def updateComponent(self, geo, key):
        # define callback action
        def callBack(e):
            st[key] = geo
            self.ExpireSolution(False)
        # get ghDoc
        ghDoc = self.OnPingDocument()
        # schedule new solution
        ghDoc.ScheduleSolution(1, 
                   Grasshopper.Kernel.GH_Document.GH_ScheduleDelegate(callBack))
    
    def RunScript(self, Geometry, Enable):
        
        # preprocess geometry tree
        Geometry.Flatten()
        Geometry = th.tree_to_list(Geometry)
        
        # get instance guid and set sticky keys
        ig = self.InstanceGuid
        geo_key = str(ig) + "_GWD_GEO"
        reset_key = str(ig) + "_GWD_RESET"
        
        # define initial condition
        Reset = False
        
        if Enable and Geometry:
            if geo_key not in st or reset_key not in st or st[reset_key] == True:
                #print "Setting geometry"
                st[geo_key] = Geometry
                st[reset_key] = False
                Reset = False
                self.Message = str(Reset)
            elif st[geo_key] != Geometry:
                #print "Reset!"
                Reset = True
                st[reset_key] = True
                self.Message = str(Reset)
                self.updateComponent(Geometry, geo_key)
            else:
                Reset = False
                st[reset_key] = False
                self.Message = str(Reset)
        else:
            if not Enable:
                self.Message = "GeometryWatchdog disabled!"
            if not Geometry:
                rml = self.RuntimeMessageLevel.Warning
                rmsg = "Input Geometry failed to collect Data!"
                self.Message = "No Geometry to watch..."
                self.AddRuntimeMessage(rml, rmsg)
        
        # return outputs if you have them; here I try it for you:
        return Reset
