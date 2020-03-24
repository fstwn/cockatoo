"""
Component tools for GHPython scripts
Author: Max Eschenbach
License: Apache License 2.0
Version: 200315
"""

from scriptcontext import sticky as st
import Rhino

def customDisplay(component, toggle):
    """
    Make a custom display which is unique to the component and lives in the
    sticky dictionary.

    Original code by Anders Holden Deleuran
    License: Apache License 2.0
    """

    # Make unique name and custom display
    displayKey = str(component.InstanceGuid) + "___CUSTOMDISPLAY"
    if displayKey not in st:
        st[displayKey] = Rhino.Display.CustomDisplay(True)

    # Clear display each time component runs
    st[displayKey].Clear()

    # Return the display or get rid of it
    if toggle:
        return st[displayKey]
    else:
        st[displayKey].Dispose()
        del st[displayKey]
        return None

def killCustomDisplays():
    """
    Clear any custom displays living in the sticky dictionary.

    Original code by Anders Holden Deleuran
    License: Apache License 2.0
    """

    for k,v in st.items():
        if type(v) is rc.Display.CustomDisplay:
            v.Dispose()
            del st[k]

# COMPONENT RUNTIME MESSAGES ---------------------------------------------------

def addRuntimeRemark(component, msg):
    """
    Adds a Remark-RuntimeMessage to the supplied component.
    """

    if type(msg) is not str:
        try:
            msg = str(msg)
        except Exception, e:
            raise RuntimeError("Could not convert supplied message to string!")
    rml = component.RuntimeMessageLevel.Remark
    component.AddRuntimeMessage(rml, msg)

def addRuntimeWarning(component, msg):
    """
    Adds a Warning-RuntimeMessage to the supplied component.
    """

    if type(msg) is not str:
        try:
            msg = str(msg)
        except Exception, e:
            raise RuntimeError("Could not convert supplied message to string!")
    rml = component.RuntimeMessageLevel.Warning
    component.AddRuntimeMessage(rml, msg)

def addRuntimeError(component, msg):
    """
    Adds an Error-RuntimeMessage to the supplied component.
    """
    if type(msg) is not str:
        try:
            msg = str(msg)
        except Exception, e:
            raise RuntimeError("Could not convert supplied message to string!")
    rml = component.RuntimeMessageLevel.Error
    component.AddRuntimeMessage(rml, msg)
