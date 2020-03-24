"""
Listens for changes in a list of values and sends a True value if anything changes
(this can be used to reset the Kangaroo Solver for example).
    Inputs:
        WatchedValues: These are the values that are being watched. Has to be a flat list ideally (but might work with datatrees, too). {list, data}
        Enable: If True, the ValueWatchdog is active. If false, it isn't. Connect a Toggle to switch it on and off. {item,boolean}
    Outputs:
        solverReset: Triggers a True when anything has changed, otherwise false. {list,polyline/curve}
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

ghenv.Component.Name = "ValueWatchdog"
ghenv.Component.NickName = "VWD"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "1 Pipeline Controlling"

class ValueWatchDog(component):
    
    def updateComponent(self):
        # define callback action
        def callBack(e):
            self.ExpireSolution(False)
        # get ghDoc
        ghDoc = self.OnPingDocument()
        # schedule new solution
        ghDoc.ScheduleSolution(1, 
                   Grasshopper.Kernel.GH_Document.GH_ScheduleDelegate(callBack))
    
    def RunScript(self, WatchedValues, Enable):
        ig = self.InstanceGuid
        vKey = str(ig) + "___WATCHEDVALUES"
        
        if Enable:
            if vKey not in st:
                st[vKey] = WatchedValues
                Reset = False
            if st[vKey] != WatchedValues:
                print "reset!"
                Reset = True
                st[vKey] = WatchedValues
                self.Message = str(Reset)
                self.updateComponent()
            else:
                Reset = False
                self.Message = str(Reset)
            
        else:
            self.Message = "ValueWatchdog disabled!"
            Reset = False
        
        # return outputs if you have them; here I try it for you:
        return Reset
