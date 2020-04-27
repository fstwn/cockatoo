"""
This components plotts curves based on particle input. Intended to be used with
Kangaroo2 Solver output or similar. Basically it stores incoming moving
particles in a list in the sticky dictionary and then draws a curve from them.

NOTE: Incoming particles will only be added to the storage if they don't equal
to the last added particle. Plotted curve will only be drawn if there is more
than one particle in the storage.
    Inputs:
        Particle: The moving particles to plot {item, Point3d}
        Mode: 0 equals Polyline output, 1 equals to Interpolated Curve output {item, int}
        Run: If True, the incoming particles are stored and a curve is drawn from them {item, bool}
        Reset: If True, the particle storage is cleared {item, bool}
    Output:
        PlottedCurve: The a output variable
    Remarks:
        Author: Max Eschenbach
        License: Apache License 2.0
        Version: 200425
"""

# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import division

# GHPYTHON SDK IMPORTS ---------------------------------------------------------
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# ADDITIONAL RHINO IMPORTS -----------------------------------------------------
from scriptcontext import sticky as st

# GHENV COMPONENT SETTINGS -----------------------------------------------------
ghenv.Component.Name = "ParticlePlotter"
ghenv.Component.NickName ="PP"
ghenv.Component.Category = "COCKATOO"
ghenv.Component.SubCategory = "9 Utilities"

class ParticlePlotter(component):
    
    def RunScript(self, Particle, Mode, Run, Reset):
        
        # set mode if mode was not correctly provided
        if Mode < 0:
            Mode = 0
        elif Mode > 1:
            Mode = 1
        
        # handle missing particles
        if not Particle:
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml, "This Component lacks Particle input!")
            return
        
        # retrieve instance guid of component and set key for sticky
        IG = self.InstanceGuid
        PARTICLEKEY = str(IG) + "___PARTICLE_" + str(self.RunCount)
        if not PARTICLEKEY in st:
            st[PARTICLEKEY] = []
        
        # reset condition
        if Reset:
            oldkeys = []
            for key in st:
                if key.startswith(str(IG)):
                    oldkeys.append(key)
            for key in oldkeys:
                del st[key]
            # reset list in sticky
            st[PARTICLEKEY] = []
        
        # run condition
        if Particle and Run and not Reset:
            if len(st[PARTICLEKEY]):
                if Particle != st[PARTICLEKEY][-1]:
                    st[PARTICLEKEY].append(Particle)
            else:
                st[PARTICLEKEY].append(Particle)
        
        # construct plot based on stored particles in sticky
        if len(st[PARTICLEKEY]) > 1:
            if Mode == 0:
                PlottedCurve = Rhino.Geometry.Polyline()
                [PlottedCurve.Add(pt) for pt in st[PARTICLEKEY]]
                PlottedCurve = PlottedCurve.ToPolylineCurve()
            elif Mode == 1:
                PlottedCurve = Rhino.Geometry.Curve.CreateInterpolatedCurve(
                                                             st[PARTICLEKEY], 3)
        else:
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml,
                            "Curve cannot be plotted from a single particle!")
            return
        
        # return outputs if you have them; here I try it for you:
        return PlottedCurve