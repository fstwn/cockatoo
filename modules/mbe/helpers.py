"""
Helper and utility functions for writing GHPython scripts / components.
Author: Max Eschenbach
License: Apache License 2.0
Version: 200414
"""
# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import absolute_import
from __future__ import division
import string

# RHINO IMPORTS
import Rhino

def removeTrailingNewlines(s):
    """
    Removes trailing newlines from a string (most of the time a filepath).
    """

    if not s:
        return None
    elif s.endswith("\n"):
        s = removeTrailingNewlines(s[:-1])
    elif s.endswith("\r"):
        s = removeTrailingNewlines(s[:-1])
    return s

def mapValuesAsColors(values, srcMin, srcMax, targetMin = 0.0, targetMax = 0.7):
    """
    Make a list of HSL colors where the values are mapped onto a
    targetMin-targetMax hue domain. Meaning that low values will be red, medium
    values green and large values blue if targetMin: 0.0 and targetMax: 0.7

    Original code by Anders Holden Deleuran
    License: Apache License 2.0
    """

    # Remap numbers into new numeric domain
    remappedValues = []
    for v in values:
        if srcMax-srcMin > 0:
            rv = ((v-srcMin)/(srcMax-srcMin))*(targetMax-targetMin)+targetMin
        else:
            rv = (targetMin+targetMax)/2
        remappedValues.append(rv)

    # Make colors and return
    colors = []
    for v in remappedValues:
        c = Rhino.Display.ColorHSL(v,1.0,0.5).ToArgbColor()
        colors.append(c)

    return colors
