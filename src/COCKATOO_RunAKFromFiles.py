"""
Run Autoknit as a threaded subprocess from specified files.
    Inputs:
        Run: Connect a button and set to true to start the autoknit instance {item, boolean}
        AKPATH: Path to the autoknit installation (the folder in which interface.exe lies) {item, str}
        OBJ: Path to the *.obj file to read the model from {item, str}
        CONS: Path to the *.cons file to read the constraints from {item, str}
        TRACED: Path where the traced file (*.st) should be saved when peeling is finished {item, str}
        obj_scale: {item, float}
        stitch_width: {item, float}
        stitch_height: {item, float}
        peel_step: {item, int}
    Outputs:
        R: Boolean identifying if this autoknit instance is currently running or not {item, bpolean}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200324
"""

# PYTHON MODULE IMPORTS
from __future__ import division
import subprocess
import threading

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# CUSTOM RHINO IMPORTS
from scriptcontext import sticky as st

# CUSTOM MODULE IMPORTS
from cockatoo import autoknit as cak

ghenv.Component.Name = "RunAKFromFiles"
ghenv.Component.NickName ="RAKFF"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "8 Autoknit Pipeline"

class AKRunFromFiles(component):
    
    def RunScript(self, Run, obj, constraints, obj_scale, stitch_width, stitch_height, save_traced, peel_step):
        
        # SETUP CODE -----------------------------------------------------------
        
        running_key, reset_key = cak.AKEngine.InitializeComponentInterface(self)
        
        if running_key not in st:
            st[running_key] = False
        if reset_key not in st:
            st[reset_key] = False
        
        # THREADED FUNCTION DEFINTION ------------------------------------------
        
        # define threaded call function
        def threaded_call():
            retcode = subprocess.call(Command)
            st[running_key] = False
            st[reset_key] = True
            
            self.ExpireSolution(True)
            return retcode
        
        # COMMAND COMPILATION --------------------------------------------------
        
        Command = cak.AKEngine.CompileCommand(obj,
                                              constraints,
                                              obj_scale,
                                              stitch_width,
                                              stitch_height,
                                              save_traced,
                                              peel_step)
        
        # START AUTOKNIT THREAD ------------------------------------------------
        
        if Run and st[running_key] is False:
            # make thread and start it
            thread = threading.Thread(target=threaded_call)
            thread.start()
            # set keys
            st[running_key] = True
            st[reset_key] = False
        
        if st[reset_key] is True:
            st[running_key] = False
        
        # return info about running autoknit thread
        R = st[running_key]
        self.Message = "Autoknit Running: " + str(st[running_key])
        
        # return outputs if you have them; here I try it for you:
        return R