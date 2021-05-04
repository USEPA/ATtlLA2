""" Identify Overlapping Polygons

    This script is associated with an ArcToolbox script tool.
"""

import sys
import arcpy
arcpy.env.overwriteOutput = "True"
from ATtILA2.utils import parameters
from ATtILA2.utils import polygons
overlaplist = []
flist = []
nonoverlapGroupDict = {}
inputArguments = parameters.getParametersAsText([0])
# arcpy.AddMessage(inputArguments)
inputLayer = inputArguments[0]
outputLoc = inputArguments[1]
checkOnly = inputArguments[2]

def checkOutputType(outputLoc):
    odsc = arcpy.Describe(outputLoc)
    # if output location is a folder then create a shapefile otherwise it will be a feature layer
    if odsc.DataType == "Folder":
        ext = ".shp"
    else:
        ext = ""
    return ext

def main(_argv):
    #Script arguments

    result, OID, overlapDict = polygons.findOverlaps(inputLayer)
    overlapList = result
    #If there are overlaps the find unique groups of non-overlapping polygons
    if result:
        arcpy.AddWarning("Warning your layer includes overlapping polygons! Calculating split")
        #Find groups of polygons that don't overlap
        nonoverlapGroupDict = polygons.findNonOverlapGroups(overlapDict)
        
        #if createOutput box is check only box is checked report number of layers need to create otherwise move
        #on to create the data layers
        #Check to see if there are only any non overlapping polygons
        strlist = []
        for r in result:
            strlist.append(str(r))
        values = ",".join(strlist)
        arcpy.MakeFeatureLayer_management(inputLayer, "No Polygons Overlap",OID + " NOT IN (" + values + ")")
        totallyrs = str(len(nonoverlapGroupDict.keys()))
        arcpy.AddWarning(totallyrs + " layers will be required to be created to ensure no overlaps")
        if checkOnly == "false":
#        if not checkOnly:
            #If overlaps exists create new layers with no overlaps(creates new intermediate layer)
            ext = checkOutputType(outputLoc)
            arcpy.AddMessage("Creating non overlapping layers")
            polygons.createNonOverlapLayers(overlapList, nonoverlapGroupDict, OID, inputLayer, outputLoc, ext)

    else:
        arcpy.AddMessage("No overlaps Found")

   
if __name__ == "__main__":
    main(sys.argv)