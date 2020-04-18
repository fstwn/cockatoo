"""
Listens for changes in geometry and sends a True value if anything changes
(this can be used to reset the Kangaroo Solver for example).
    Inputs:
        Geometry: This is the geometry that is being watched for changes. {list, geometry}
        Enable: If True, the PipelineWatchdog is active. If false, it isn't. Connect a Toggle to switch it on and off. {item, boolean}
    Outputs:
        solverReset: Triggers a True when anything has changed, otherwise false. {item, boolean}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200324
"""

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# CUSTOM RHINO IMPORTS
from scriptcontext import sticky as st

ghenv.Component.Name = "GeometryWatchDog"
ghenv.Component.NickName = "GWD"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "1 Pipeline Controlling"

class GeometryWatchDog(component):
    
    def updateComponent(self):
        # define callback action
        def callBack(e):
            self.ExpireSolution(False)
        # get ghDoc
        ghDoc = self.OnPingDocument()
        # schedule new solution
        ghDoc.ScheduleSolution(1, 
                   Grasshopper.Kernel.GH_Document.GH_ScheduleDelegate(callBack))
    
    def RunScript(self, Geometry, Enable):
        
        ig = self.InstanceGuid
        geoKey = str(ig) + "___WATCHEDGEOMETRY"
        resetKey = str(ig) + "___RESETFLAG"
        
        if Enable and Geometry and Geometry != []:
            if geoKey not in st or resetKey not in st or st[resetKey] == True:
                print "Setting geometry"
                st[geoKey] = Geometry
                st[resetKey] = False
                Reset = False
                self.Message = str(Reset)
            elif st[geoKey] != Geometry:
                print "Reset!"
                Reset = True
                st[resetKey] = True
                st[geoKey] = Geometry
                self.Message = str(Reset)
                self.updateComponent()
            else:
                solverReset = False
                Reset = False
                self.Message = str(Reset)
            
        else:
            self.Message = "GeometryWatchdog disabled!"
            Reset = False
        
        # return outputs if you have them; here I try it for you:
        return Reset
