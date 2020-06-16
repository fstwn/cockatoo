"""
Caches some Data by storing it as Persistent Data (aka internalising it) in a connected Param.
    Inputs:
        LiveData: The Data that should be cached (internalised) {tree, data}
        CachedData: Connect a Data Param here where the Data can be internalised {list, data}
        Toggle: If True, Data will be cached by internalising it into the Param connected to IntData. {item, boolean}
    Outputs:
        Data: If Toggle is True the internalised Data, otherwise the incoming Live-Data {list, data}}
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200615
"""
ghenv.Component.Name = "DataCache"
ghenv.Component.NickName = "DC"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "10 Utilities"

# GHPYTHON SDK MODE IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# CUSTOM IMPORTS
from scriptcontext import sticky as st

class DataCache(component):
    
    def RunScript(self, LiveData, CachedData, Toggle):
        
        # get the gh document
        ghDoc = ghenv.Component.OnPingDocument()
        
        # get the guid of this instance to ensure private sticky entries
        ig = self.InstanceGuid
        
        # define a marker for the state of caching/internalisation
        Flag = str(ig) + "___INTERNALISEDFLAG"
        if not Flag in st:
            if CachedData:
                st[Flag] = True
            else:
                st[Flag] = None
        
        # PARAM HANDLING -------------------------------------------------------
        LiveDataParam = ghenv.Component.Params.Input[0]
        CachedDataParam = ghenv.Component.Params.Input[1]
        
        # try to get the connected param, otherwise set a warning and return
        if CachedDataParam.Sources:
            CachedSrc = CachedDataParam.Sources[0]
        else:
            rmlevel = self.RuntimeMessageLevel.Warning
            ghenv.Component.AddRuntimeMessage(rmlevel, "Please connect a Data" +
                                              " Param to the IntData input!")
            return None
        
        
        # HANDLING OF CACHED DATA ----------------------------------------------
        if CachedData and Toggle:
            for i, D in enumerate(CachedData):
                if D == str(ig) + "___NONE___":
                    CachedData[i] = None
            self.Message = "Streaming CachedData"
            Data = CachedData
            return Data
        else:
            self.Message = "Streaming LiveData"
            Data = LiveData
        
        
        # CACHING OF DATA ------------------------------------------------------
        if LiveData and Toggle and not st[Flag]:
            # sanitize the none values
            for i, D in enumerate(LiveData):
                if D == None:
                    LiveData[i] = str(ig) + "___NONE___"
            # create a dotnet list and add all the data items to it
            dList = System.Collections.Generic.List[object]()
            [dList.Add(o) for o in LiveData]
            # switch the marker and set message
            st[Flag] = True
            
            # define delegate for adding persistent data between solutions
            def sln_delegate(doc):
                CachedSrc.Script_AddPersistentData(dList)
                ghenv.Component.ExpireSolution(False)
            
            # schedule new solutin using the defined delegate
            ghDoc.ScheduleSolution(1, sln_delegate)
        
        # # RESET OF CACHED DATA ON FALSE TOGGLE -------------------------------
        elif Toggle == False:
            if st[Flag] == True:
                # set the marker
                st[Flag] = None
                # clear the persistent data and set message
                CachedSrc.Script_ClearPersistentData()
                # expire the solution so everything gets updated
                CachedSrc.ExpireSolution(True)
        
        # return outputs if you have them; here I try it for you:
        return Data