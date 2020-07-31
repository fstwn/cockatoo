"""
Provides some statistical data for a KnitNetwork. Used to check how closely
the edges of the KnitNetwork match a given CourseHeight and StitchWidth.
    Inputs:
        KnitNetwork: A KnitNetwork for analysis of edge lengths.
                     {item, KnitNetwork}
        CourseHeight: CourseHeight for comparison.
                      {item, float}
        StitchWidth: StitchWidth for comparison.
                     {item, float}
    Output:
        SummaryText: A textual summary of the statistical data.
                     NOTE: Values are rounded and always displayed in
                     millimeters, regardless of model unit settings!
                     {item, Text}
        EdgeDeviation: Signed length deviation for all edges of the KnitNetwork
                       in model units.
                       {list, float}
        EdgeDeviationFactor: Signed length deviation factor for all edges of the
                             KnitNetwork.
                             {list, float}
        MinDeviation: Absolute minimum deviation in model units.
                      {item, float}
        MaxDeviation: Absolute maximum deviation in model units.
                      {item, float}
        AverageDeviation: Absolute average deviation in model units.
                          {item, float}
        Variance: Absolute variance in model units.
                  {item, float}
        StandardDeviation: Absolute standard deviation in model units.
                           {item, float}
    Remarks:
        Author: Max Eschenbach
        License: MIT License
        Version: 200719
"""

# PYTHON STANDARD LIBRARY IMPORTS
from __future__ import division
from __future__ import print_function
import math

# GHPYTHON SDK IMPORTS
from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# GHENV COMPONENT SETTINGS
ghenv.Component.Name = "KnitNetworkStatistics"
ghenv.Component.NickName ="KNS"
ghenv.Component.Category = "Cockatoo"
ghenv.Component.SubCategory = "06 KnitNetwork"

# LOCAL MODULE IMPORTS
try:
    import cockatoo
except ImportError:
    errMsg = "The Cockatoo python module seems to be not correctly " + \
             "installed! Please make sure the module is in you search " + \
             "path, see README for instructions!."
    raise ImportError(errMsg)

class KnitNetworkStatistics(component):
    
    def RunScript(self, KnitNetwork, CourseHeight, StitchWidth):
        
        EdgeDeviation = []
        EdgeDeviationFactor = []
        AbsoluteDeviation = []
        AbsoluteDeviationFactor = []
        
        if not KnitNetwork:
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml,
                                   "No KnitNetwork input!")
            return (Grasshopper.DataTree[object](),
                    Grasshopper.DataTree[object](),
                    Grasshopper.DataTree[object](),
                    Grasshopper.DataTree[object](),
                    Grasshopper.DataTree[object](),
                    Grasshopper.DataTree[object](),
                    Grasshopper.DataTree[object](),
                    Grasshopper.DataTree[object]())
        
        for i, edge in enumerate(KnitNetwork.edges_iter(data=True)):
            edgedata = edge[2]
            if edgedata["warp"]:
                el = edgedata["geo"].Length
                # compute real deviation
                dev = el - CourseHeight
                EdgeDeviation.append(dev)
                AbsoluteDeviation.append(abs(dev))
                # compute percentage
                devperc = dev / CourseHeight
                EdgeDeviationFactor.append(devperc)
                AbsoluteDeviationFactor.append(abs(devperc))
            elif edgedata["weft"]:
                el = edgedata["geo"].Length
                # compute real deviation
                dev = el - StitchWidth
                EdgeDeviation.append(dev)
                AbsoluteDeviation.append(abs(dev))
                # compute percentage
                devperc = dev / StitchWidth
                EdgeDeviationFactor.append(devperc)
                AbsoluteDeviationFactor.append(abs(devperc))
        
        # compute number of edges from deviation list
        numedges = len(EdgeDeviation)
        
        if numedges == 0:
            rml = self.RuntimeMessageLevel.Warning
            self.AddRuntimeMessage(rml,
                                   "Input KnitNetwork has no edges!")
            return (Grasshopper.DataTree[object](),
                    Grasshopper.DataTree[object](),
                    Grasshopper.DataTree[object](),
                    Grasshopper.DataTree[object](),
                    Grasshopper.DataTree[object](),
                    Grasshopper.DataTree[object](),
                    Grasshopper.DataTree[object](),
                    Grasshopper.DataTree[object]())
        
        # compute +- 1 % deviation amount
        pm_one = [d for d in EdgeDeviationFactor if d > -0.01 and d <= 0.01]
        pm_one_perc = round((len(pm_one) / numedges) * 100, 2)
        
        # compute +- 5 % deviation amount
        pm_ofive = [d for d in EdgeDeviationFactor if d >= -0.05 and d <= 0.05]
        pm_ofive_perc = round((len(pm_ofive) / numedges) * 100, 2)
        
        # compute +- 10 % deviation amount
        pm_ten = [d for d in EdgeDeviationFactor if d >= -0.1 and d <= 0.1]
        pm_ten_perc = round((len(pm_ten) / numedges) * 100, 2)
        
        # compute +- 20 % deviation amount
        pm_twen = [d for d in EdgeDeviationFactor if d >= -0.2 and d <= 0.2]
        pm_twen_perc = round((len(pm_twen) / numedges) * 100, 2)
        
        # compute +- 30 % deviation amount
        pm_thir = [d for d in EdgeDeviationFactor if d >= -0.3 and d <= 0.3]
        pm_thir_perc = round((len(pm_thir) / numedges) * 100, 2)
        
        # compute +- 40 % deviation amount
        pm_four = [d for d in EdgeDeviationFactor if d >= -0.4 and d <= 0.4]
        pm_four_perc = round((len(pm_four) / numedges) * 100, 2)
        
        # compute +- 50 % deviation amount
        pm_five = [d for d in EdgeDeviationFactor if d >= -0.5 and d <= 0.5]
        pm_five_perc = round((len(pm_five) / numedges) * 100, 2)
        
        # compute +- 60 % deviation amount
        pm_six = [d for d in EdgeDeviationFactor if d >= -0.6 and d <= 0.6]
        pm_six_perc = round((len(pm_six) / numedges) * 100, 2)
        
        # compute +- 70 % deviation amount
        pm_seven = [d for d in EdgeDeviationFactor if d >= -0.7 and d <= 0.7]
        pm_seven_perc = round((len(pm_seven) / numedges) * 100, 2)
        
        # compute +- 80 % deviation amount
        pm_eight = [d for d in EdgeDeviationFactor if d >= -0.8 and d <= 0.8]
        pm_eight_perc = round((len(pm_eight) / numedges) * 100, 2)
        
        # compute +- 90 % deviation amount
        pm_nine = [d for d in EdgeDeviationFactor if d >= -0.9 and d <= 0.9]
        pm_nine_perc = round((len(pm_nine) / numedges) * 100, 2)
        
        # compute +- 100 % deviation amount
        pm_hund = [d for d in EdgeDeviationFactor if d >= -1 and d <= 1]
        pm_hund_perc = round((len(pm_hund) / numedges) * 100, 2)
        
        # compute average, variance and standard deviation
        AverageDeviation = (sum(AbsoluteDeviation)
                             / len(AbsoluteDeviation))
        Variance = (sum([((ed - AverageDeviation) ** 2)
                         for ed in AbsoluteDeviation])
                    / len(AbsoluteDeviation))
        StandardDeviation = math.sqrt(Variance)
        
        # compute percentages
        AveragePercentage = (sum(AbsoluteDeviationFactor)
                             / len(AbsoluteDeviationFactor))
        VariancePercentage = (sum([((ed - AveragePercentage) ** 2)
                                   for ed in AbsoluteDeviationFactor])
                              / len(AbsoluteDeviationFactor))
        StandardPercentage = math.sqrt(VariancePercentage)
        
        # convert deviations to millimeters for readability
        musys = Rhino.RhinoDoc.ActiveDoc.ModelUnitSystem
        modelscale = Rhino.RhinoMath.UnitScale(musys,
                                               Rhino.UnitSystem.Millimeters)
        avg_mm = AverageDeviation * modelscale
        var_mm = Variance * modelscale
        sdev_mm = StandardDeviation * modelscale
        
        # compute minimum and maximum deviation
        MinDeviation = min(AbsoluteDeviation)
        MinPercentage = min(AbsoluteDeviationFactor)
        MaxDeviation = max(AbsoluteDeviation)
        MaxPercentage = max(AbsoluteDeviationFactor)
        
        # compile textual summary
        Summary = []
        txtsum_string = "{} edges ({} %) are within +- {} % deviation."
        Summary.append("KnitNetwork contains {} edges.".format(numedges))
        Summary.append(txtsum_string.format(len(pm_one), pm_one_perc, "1"))
        Summary.append(txtsum_string.format(len(pm_ofive), pm_ofive_perc, "5"))
        Summary.append(txtsum_string.format(len(pm_ten), pm_ten_perc, "10"))
        Summary.append(txtsum_string.format(len(pm_twen), pm_twen_perc, "20"))
        Summary.append(txtsum_string.format(len(pm_thir), pm_thir_perc, "30"))
        Summary.append(txtsum_string.format(len(pm_four), pm_four_perc, "40"))
        Summary.append(txtsum_string.format(len(pm_five), pm_five_perc, "50"))
        Summary.append(txtsum_string.format(len(pm_six), pm_six_perc, "60"))
        Summary.append(txtsum_string.format(len(pm_seven), pm_seven_perc, "70"))
        Summary.append(txtsum_string.format(len(pm_eight), pm_eight_perc, "80"))
        Summary.append(txtsum_string.format(len(pm_nine), pm_nine_perc, "90"))
        Summary.append(txtsum_string.format(len(pm_hund), pm_hund_perc, "100"))
        
        Summary.append(
            "The minimum deviation is {} millimeters ({} %)".format(
                                            round(MinDeviation * modelscale, 2),
                                            round(MinPercentage * 100, 2)))
                                                    
        Summary.append(
            "The maximum deviation is {} millimeters ({} %)".format(
                                            round(MaxDeviation * modelscale, 2),
                                            round(MaxPercentage * 100, 2)))
        Summary.append(
            "The average deviation is {} millimeters ({} %)".format(
                                            round(avg_mm, 2),
                                            round(AveragePercentage * 100, 2)))
        Summary.append(
            "The variance is {} millimeters ({} %)".format(
                                            round(var_mm, 2),
                                            round(VariancePercentage * 100, 2)))
        Summary.append(
            "The standard deviation is {} millimeters ({} %)".format(
                                            round(sdev_mm, 2),
                                            round(StandardPercentage * 100, 2)))
        
        # return outputs if you have them; here I try it for you:
        return (Summary,
                EdgeDeviation,
                EdgeDeviationFactor,
                MinDeviation,
                MaxDeviation,
                AverageDeviation,
                Variance,
                StandardDeviation)
