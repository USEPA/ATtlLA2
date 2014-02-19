import arcpy
import os
from arcpy import env
from arcpy.sa import *
import sys

#Turn on the overwrite option
env.overwriteOutput = True

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

#Input Variables
ReportingUnitFeature = sys.argv[1]
ReportingUnitField = sys.argv[2]
Landcovergrid = sys.argv[3]
##LandCoverScheme = sys.argv[4]
##LandCoverClassificationFile = sys.argv[5]  #place holder
##OutputTable = sys.argv[6]
##ProcessingCellSize = sys.argv[7] #Optional
##SnapRaster = sys.argv[8] #Optional
PatchEdgeWidth = int(sys.argv[4])

# Get Forested  and Water Categories or User Categories from user input
ForestValues = sys.argv[5]
WaterValues = sys.argv[6]
outputSpace = sys.argv[7]

#LandUse Value List:
ForestValueList = []
WaterValueList = []
OtherValueList = []

ValuesDictionary = {}
ValuesDictionary["Forest"] = ForestValues
ValuesDictionary["Water"] = WaterValues

#Count the number of ";" to check if there is more than one value selected by the user
countValues = ForestValues.count(";")

ForestValueList = []
#Count the number of ";" to check if there is more than one value selected by the user
for k in ValuesDictionary.keys():
    countValues = ValuesDictionary[k].count(";")
    if countValues > 0:
        if k == "Forest":
            ForestValueList = ValuesDictionary[k].split(";")
        elif k == "Water":
            WaterValueList = ValuesDictionary[k].split(";")
    else:
        if k == "Forest":
            ForestValueList.append(ValuesDictionary[k])
        elif k == "Water":
            WaterValueList.append(ValuesDictionary[k])

def convertList(inList, outList):
    for l in inList:
        outList.append(int(l))
        
def getRasterGridSize(Landcovergrid):
    #Get the cell size for the land use grid
    XBand = arcpy.GetRasterProperties_management(Landcovergrid, "CELLSIZEX" )
    YBand = arcpy.GetRasterProperties_management(Landcovergrid, "CELLSIZEY")
    #Check to make sure the grid size are square if it is not generate an error
    if int(float(str(XBand))) == int(float(str(YBand))):
        return int(float(str(XBand)))
    else:
        arcpy.AddError("Uh oh the grids are not square!!! X Band Value will only be used")
        
def updateTableWshed(ReportingUnitFeature,ReportingUnitField,datalayer):
    #Updates the watershed area to the ForestCoreEdge_Areas table
    AreaDict = {}
    
    # Get the watershed area from the user's Reporting Unit Feature
    rows = arcpy.SearchCursor(ReportingUnitFeature)
    row = rows.next()
    
    #Find the field in the Reporting  Unit Feature that holds the shape field
    shapeName = arcpy.Describe(ReportingUnitFeature).shapeFieldName

    #Populate the AreaDict with ReportingUnitField and Area - AreaDict[ReportingUnitField] = Area    
    while row:
        RUF = row.getValue(ReportingUnitField)
        feat = row.getValue(shapeName)
        Area = feat.area
        AreaDict[RUF] = Area
        row = rows.next()

    #Update watershed area field in the result table using the AreaDict[] populated above
    rows = arcpy.UpdateCursor(datalayer)
    row = rows.next()
    while row:
        RUF = row.getValue(ReportingUnitField)
        row.WshedArea = AreaDict[RUF]
        rows.updateRow(row)
        row = rows.next()
    del row, rows

def updateValuestoRaster(Raster):
    #Updates the POS field in the ForestCoreEdge with "Core" and "Edge" values
    rows = arcpy.UpdateCursor(Raster)
    row = rows.next()
    while row:
        #VALUE = 1 indicates a Core cell, Value = 3 is an Edge cell
        v = row.getValue("Value")
        if v == 1:
            row.POS = "Core"
        elif v == 3:
            row.POS = "Edge"
        elif v == 2:
            row.POS = "Water"
        elif v == 4:
            row.POS = "Other"
        rows.updateRow(row)
        row = rows.next()
##    arcpy.AddMessage("Updated POS Values")

def main(_argv):


    #Set up the Other Landuse Category                
    rows = arcpy.SearchCursor(Landcovergrid)
    row = rows.next()

    #Get a list of all values in the landcovergrid
    while row:
        thevalue = row.getValue("VALUE")
        OtherValueList.append(str(thevalue))
        row =rows.next()

    #Remove the forested landuse
    for f in ForestValueList:
        if f in OtherValueList:
            OtherValueList.remove(f)
            
    #Remove the water landuse
    for w in WaterValueList:
        if w in OtherValueList:
            OtherValueList.remove(w)

    
    #Extract Forested or User Categories from Landuse grid
    env.workspace = os.path.dirname(Landcovergrid)
    inputLC = os.path.basename(Landcovergrid)
    outputgrid = "ExtractForest"
    
    #Set up the values for the sql expression
    values = ",".join(ForestValueList)
    #Extract the user selected categories from the Landuse grid
    attExtract = ExtractByAttributes(inputLC, "VALUE IN (" + values + ")")
    attExtract.save(os.path.join(outputSpace,outputgrid))
    
    #Extract Non Forested or Non User Categories from Landuse grid
    outputNFgrid = "ExtractNonForest"
    attExtract = ExtractByAttributes(inputLC, "VALUE NOT IN (" + values + ")")
    attExtract.save(os.path.join(outputSpace,outputNFgrid))

    #Extract Water Categories from Landuse grid
    outputWatergrid = "ExtractWater"
    #Set up the values for the sql expression
    values = ",".join(WaterValueList)
    #Extract the user selected categories from the Landuse grid
    attExtract = ExtractByAttributes(inputLC, "VALUE IN (" + values + ")")
    attExtract.save(os.path.join(outputSpace,outputWatergrid))
    
    #Extract Other Categories from Landuse grid
    outputOthergrid = "ExtractOther"
    #Set up the values for the sql expression
    values = ",".join(OtherValueList)
    #Extract the user selected categories from the Landuse grid
    attExtract = ExtractByAttributes(inputLC, "VALUE IN (" + values + ")")
    attExtract.save(os.path.join(outputSpace,outputOthergrid))
    
    env.workspace = outputSpace
    #Calculate the Euclidean distance using the NonForest -- Note this will need to be adjusted to use User categories
    #(intermediate layer)
    
    gridcellsize = getRasterGridSize(outputNFgrid)
    maxdist = PatchEdgeWidth * gridcellsize
    outEucDistance = EucDistance(outputNFgrid, maxdist, str(gridcellsize))

    #Create new Forest with a single value for forest(intermediate layer)
    intForestValueList = []
    #Convert Forest Value List into a list of integers
    convertList(ForestValueList, intForestValueList)
    
    ForRemapRange = RemapRange([[min(intForestValueList), max(intForestValueList), 1]])
    ForSingleReclass = Reclassify("ExtractForest", "Value", ForRemapRange)
    
   #Create new Euclidean distance raster with a single value and NoData converted to 0(intermediate layer)
    EucRemapRange = RemapRange([[0, maxdist, 2], ["noData", "noData", 0]])
    EucReclass = Reclassify(outEucDistance, "VALUE", EucRemapRange)
    
    #Run Add Euclidean_Con and ForestSingle together - result: Value 1 = Core, Value 3 = Edge
    outPlus = Plus(ForSingleReclass, EucReclass)
    outPlus.save("ForestCoreEdge")

    #Add Pos field to ForestCoreEdge raster and populate it
    arcpy.AddField_management(os.path.join(env.workspace, "ForestCoreEdge"),"POS","TEXT","#","#","10","#","NULLABLE",
                              "NON_REQUIRED","#")
    updateValuestoRaster("ForestCoreEdge")

    #Change NoData to 0 in ForestCoreEdge raster in prep for final output raster (intermediate layer)
    ForRemapRange = RemapRange([[1,1,1],[3,3,3],["NoData","NoData", 0]])
    ForZeroedForCE = Reclassify("ForestCoreEdge", "Value", ForRemapRange)

    #Create new Water with a single value for water (intermediate layer)
    intWaterValueList = []
    convertList(WaterValueList, intWaterValueList)

    ForRemapRange = RemapRange([[min(intWaterValueList), max(intWaterValueList), 2],["noData", "noData", 0]])
    H20SingleReclass = Reclassify("ExtractWater", "Value", ForRemapRange)

    #Create new Other with a single value for other(intermediate layer)
    intOtherValueList = []
    convertList(OtherValueList, intOtherValueList)

    ForRemapRange = RemapRange([[min(intOtherValueList), max(intOtherValueList), 4],["noData", "noData", 0]])
    OtherSingleReclass = Reclassify("ExtractOther", "Value", ForRemapRange)
 
    #Create Final Output Raster
    FinalOutputRas = CellStatistics([ForZeroedForCE, H20SingleReclass, OtherSingleReclass], "SUM", "DATA")
    ForRemapRange = RemapRange([[1,1,1],[2,2,2],[3,3,3],[4,4,4],[0,0,"NoData"]])
    FinalRaster = Reclassify(FinalOutputRas, "Value", ForRemapRange)
    FinalRaster.save("ForestCoreEdge_Final")
    
    arcpy.AddField_management(os.path.join(env.workspace, "ForestCoreEdge_Final"),"POS","TEXT","#","#","10","#",
                              "NULLABLE","NON_REQUIRED","#")
    updateValuestoRaster("ForestCoreEdge_Final")
                               
    
    #Run Tabulate area on ForestCoreEdge Raster by reporting unit
    arcpy.sa.TabulateArea(ReportingUnitFeature, ReportingUnitField, os.path.join(env.workspace, "ForestCoreEdge"), "POS"
                          ,os.path.join(env.workspace, "ForestCoreEdge_Areas"), str(getRasterGridSize(Landcovergrid)))
    
    #Add Watershed Area to ForestCoreEdge_areas table
    x = 10
    while x <= 60:
        #This code looks for a schema lock (I was having random schema lock issues which were hard to test for since
        #they were occuring randomly)
        if arcpy.TestSchemaLock(os.path.join(env.workspace, "ForestCoreEdge_Areas")):
                    arcpy.AddField_management(os.path.join(env.workspace, "ForestCoreEdge_Areas"), "WshedArea", "Double"
                                              , "15", "8","")
                    updateTableWshed(ReportingUnitFeature,ReportingUnitField,os.path.join(env.workspace,
                                                                                          "ForestCoreEdge_Areas"))
                    break
        else:
            time.sleep(x)
            x = x + 10
        if x >=60:
            arcpy.AddMessage("Unable to acquire the necessary schema lock to add WshedArea Field")

    #Add FEdge, FCore, and F_E2A fields to table
    FieldList = ["FEdge", "FCore", "F_E2A"]

    for f in FieldList:
        x = 10
        while x <= 60:
        #This code looks for a schema lock before implementing script
            if arcpy.TestSchemaLock(os.path.join(env.workspace, "ForestCoreEdge_Areas")):
                arcpy.AddField_management("ForestCoreEdge_Areas", f, "Double", "15", "8", "")
                break
            else:
                time.sleep(x)
                x = x + 10
            if x >=60:
                arcpy.AddMessage("Unable to acquire the necessary schema lock to add " + f)
        

    #Populate the fields
    rows = arcpy.UpdateCursor("ForestCoreEdge_Areas")
    row = rows.next()
    while row:
        EdgeValue = row.getValue("Edge")
        CoreValue = row.getValue("Core")
        WshedArea = row.getValue("WshedArea")
        row.FEdge = (EdgeValue/WshedArea)*100
        row.FCore = (CoreValue/WshedArea)*100
        row.F_E2A = (EdgeValue/(EdgeValue + CoreValue)) *100
        rows.updateRow(row)
        row = rows.next()
                       
if __name__ == "__main__":
    main(sys.argv)