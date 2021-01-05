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
        License: MIT License
        Version: 210105
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

ghenv.Component.Name = "ValueWatchdog"
ghenv.Component.NickName = "VWD"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "01 Pipeline Controlling"

class ValueWatchDog(component):
    
    def updateComponent(self, values, key):
        # define callback action
        def callBack(e):
            st[key] = values
            self.ExpireSolution(False)
        # get ghDoc
        ghDoc = self.OnPingDocument()
        # schedule new solution
        ghDoc.ScheduleSolution(1, 
                   Grasshopper.Kernel.GH_Document.GH_ScheduleDelegate(callBack))
    
    def RunScript(self, WatchedValues, Enable):
        
        # preprocess value tree
        WatchedValues.Flatten()
        WatchedValues = th.tree_to_list(WatchedValues)
        
        # get instance guid and init stickey key
        ig = self.InstanceGuid
        v_key = str(ig) + "_VWD_VALUES"
        
        # define initial condition
        Reset = False
        
        if Enable and WatchedValues:
            if v_key not in st:
                #print "Setting values"
                st[v_key] = WatchedValues
                Reset = False
            if st[v_key] != WatchedValues:
                #print "Reset!"
                Reset = True
                self.Message = str(Reset)
                self.updateComponent(WatchedValues, v_key)
            else:
                Reset = False
                self.Message = str(Reset)
        else:
            if not Enable:
                self.Message = "ValueWatchdog disabled!"
            if not WatchedValues:
                rml = self.RuntimeMessageLevel.Warning
                rmsg = "Input WatchedValues failed to collect Data!"
                self.Message = "No Values to watch..."
                self.AddRuntimeMessage(rml, rmsg)
        
        # return outputs if you have them; here I try it for you:
        return Reset
