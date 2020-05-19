# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import division
import datetime
from os import path

# RHINO IMPORTS ----------------------------------------------------------------
from scriptcontext import sticky as st

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from Cockatoo.Autoknit.Environment import _AK_PATH_, _AK_INTERFACE_
from Cockatoo.Autoknit.FileIO import SaveObj, SaveConstraints

# ALL LIST ---------------------------------------------------------------------
__all__ = [
    "InitializeComponentInterface",
    "TempFilePaths",
    "CompileCommand",
    "WriteTempFiles"
]

def InitializeComponentInterface(component):
    """
    Initializes the necessary things in the Rhino sticky.
    """

    ig = str(component.InstanceGuid)
    running_key = ig + "___AKRUNNING"
    reset_key = ig + "___RESET"

    if running_key not in st:
        st[running_key] = False
    if reset_key not in st:
        st[reset_key] = False

    return (running_key, reset_key)

def TempFilePaths(filedir):
    """
    Creates filepaths for temporary autoknit files.
    """

    # create timestamp
    n = datetime.datetime.now()
    yy = str(n.year)[-2:]
    mm = str(n.month).zfill(2)
    dd = str(n.day).zfill(2)
    ho = str(n.hour).zfill(2)
    mt = str(n.minute).zfill(2)
    sc = str(n.second).zfill(2)
    ts = yy + mm + dd + "-" + ho + mt + sc

    # define filepaths
    temp_modelfile = filedir + "\\._ak_temp_" + ts + ".obj"
    temp_consfile = filedir + "\\._ak_temp_" + ts + ".cons"

    return (temp_modelfile, temp_consfile)

def CompileCommand(obj, constraints, obj_scale = None, stitch_width = None, stitch_height = None, save_traced = None, peel_step = None):
    """
    Compiles a command with arguments for running autoknit.
    """

    if not obj or not constraints:
        raise ValueError("Expected *.obj and *.cons file," + \
                         "received {} and {}." + \
                         "Check your inputs!".format(obj, constraints))
    # make basic command arguments
    cmdargs = ["obj:" + obj, "constraints:" + constraints]

    # handle obj-scale parameter -----------------------------------------------
    if obj_scale:
        try:
            obj_scale = float(obj_scale)
            cmdargs.append("obj-scale:{}".format(str(obj_scale)))
        except Exception, e:
            raise ValueError("Could not convert supplied " + \
                             "obj-scale to float! Ignoring this option..." + \
                             " // " + e)
    # handle stitch-width parameter --------------------------------------------
    if stitch_width:
        try:
            stitch_width = float(stitch_width)
            cmdargs.append("stitch-width:{}".format(str(stitch_width)))
        except Exception, e:
            raise ValueError("Could not convert supplied stitch-width " + \
                             "to float! Ignoring this option..." + \
                             " // " + e)
    # handle stitch-height parameter -------------------------------------------
    if stitch_height:
        try:
            stitch_height = float(stitch_height)
            cmdargs.append("stitch-height:{}".format(str(stitch_height)))
        except Exception, e:
            raise ValueError("Could not convert supplied stitch-height " + \
                             "to float! Ignoring this option..." + \
                             " // " + e)
    # handle save-traced parameter ---------------------------------------------
    if save_traced:
        try:
            save_traced = path.normpath(save_traced.rstrip("\n\r"))
            if not save_traced.endswith(".st"):
                save_traced = save_traced + ".st"
            cmdargs.append("save-traced:{}".format(save_traced))
        except Exception, e:
            raise ValueError("Could not convert supplied save_traced " + \
                             "path to string! Ignoring this option..." + \
                             " // " + e)
    # handle peel-step parameter -----------------------------------------------
    if peel_step:
        try:
            peel_step = int(peel_step)
            if peel_step < -1:
                peel_step = -1
            cmdargs.append("peel-step:{}".format(str(peel_step)))
        except:
            raise ValueError("Could not convert supplied peel-step " + \
                             "to int! Ignoring this option..." + \
                             " // " + e)
    # make the command and return it
    Command = [_AK_INTERFACE_]
    Command.extend(cmdargs)
    return Command

def WriteTempFiles(model, obj_file, cons_file):
    """
    Writes temporary files for starting autoknit.
    """
    SaveObj(obj_file, model.Mesh)
    SaveConstraints(cons_file, model.ConstraintCoordinates, model.Constraints)

# MAIN -------------------------------------------------------------------------
if __name__ == '__main__':
    pass
