import arcpy
from arcpy.sa import *
from arcpy import env
import sys
import os

#Turn on the overwrite option
env.overwriteOutput = True

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")
AnalysisChoice = sys.argv[1]
ReportingUnitFeature = sys.argv[2]
ReportingUnitField = sys.argv[3]
Landcovergrid = sys.argv[4]
ForestValues = sys.argv[5]
outSpace = sys.argv[6]
MaxSeperation = int(sys.argv[7])
MinPatchSize = int(sys.argv[8])
SearchRadius = sys.argv[9]

#LandUse Value List:
ForestValueList = []
ForestValueList = ForestValues.split(";")

AnalysisList = []
AnalysisList = AnalysisChoice.split(";")
arcpy.AddMessage(AnalysisList)

def convertList(inList, outList):
    for l in inList:
        outList.append(int(l))

def getLinearUnit(ReportingUnitFeature):
    dsc = arcpy.Describe(ReportingUnitFeature)
    linearunit = dsc.spatialReference.linearUnitName
    return linearunit

def getRasterGridSize(Landcovergrid):
    #Get the cell size for the land use grid
    XBand = arcpy.GetRasterProperties_management(Landcovergrid, "CELLSIZEX" )
    YBand = arcpy.GetRasterProperties_management(Landcovergrid, "CELLSIZEY")
    #Check to make sure the grid size are square if it is not generate an error
    if int(float(str(XBand))) == int(float(str(YBand))):
        return int(float(str(XBand)))
    else:
        arcpy.AddError("Uh oh the grids are not square!!! X Band Value will only be used")

def main(_argv):
    env.workspace = outSpace
    rlist = []
    rlist = arcpy.ListRasters()
    if "FinalPatches" in rlist:
        arcpy.AddMessage("Raster found")
        #Patch Raster already exists therefore get analysis list and run the chosen analyses  
        #if length of the list is 2 then both analyses were chosen, check to see if the results table
        #already exists, if so then a warning message is generated and the code stops
        if len(AnalysisList) == 2:
            arcpy.AddMessage("two analyses chosen")
            tlist = []
            tlist = arcpy.ListTables()
            if "PatchResults" not in tlist:
                tabulatePatchMetrics("FinalPatches")
                tabulateMDCP("FinalPatches")
            else:
                arcpy.AddError("The Results have already been generated")
                sys.exit()
        else:
            arcpy.AddMessage("one analysis chosen")
        #Otherwise run the chosen analysis
            if "PatchMetrics" in AnalysisList:
                tabulatePatchMetrics("FinalPatches")
            elif "MDCP" in AnalysisList:
                tabulateMDCP("FinalPatches")
    else:
        arcpy.AddMessage("Raster not found")
        #if Patch raster does not already exist create it and then run the analysis.
        createPatchRaster()
        
def createPatchRaster():
    #Extract Forested or User Categories from Landuse grid
    env.workspace = os.path.dirname(Landcovergrid)
    inputLC = os.path.basename(Landcovergrid)
    outputgrid = "ExtractForest"

    #Set up the values for the sql expression
    values = ",".join(ForestValueList)
    #Extract the user selected categories from the Landuse grid
    attExtract = ExtractByAttributes(inputLC, "VALUE IN (" + values + ")")
    attExtract.save(os.path.join(outSpace,outputgrid))

    #reset workspace to user defined output space (this is necessary because ArcGIS looks for the input landcover in
    #the workspace even if another path is called).
    env.workspace = outSpace

    #Create new Forest with a single value for forest(intermediate layer)
    intForestValueList = []
    #Convert Forest Value List into a list of integers
    convertList(ForestValueList, intForestValueList)

    ForRemapRange = RemapRange([[min(intForestValueList), max(intForestValueList), 1]])
    ForestSingle = Reclassify("ExtractForest", "Value", ForRemapRange)

    #Check to see if Maximum Separation > 0 if it is then skip to regions group analysis otherwise run
    #Euclidean distance
    if MaxSeperation == 0:
        #Run Regions group then run TabArea_FeatureLayer
        ForSingleRegionGroup = RegionGroup(ForestSingle,"EIGHT","CROSS","ADD_LINK","")
        if MinPatchSize > 1:
            FinalPatchRas = ExtractByAttributes(ForSingleRegionGroup, "COUNT >" + str(MinPatchSize -1))
            FinalPatchRas.save("FinalPatches")
##            tabulatePatchMetrics("FinalPatches")
        else:
            ForSingleRegionGroup.save("FinalPatches")
##            tabulatePatchMetrics("FinalPatches")
        if len(AnalysisList) == 2:
            tabulatePatchMetrics("FinalPatches")
            tabulateMDCP("FinalPatches")
        else:
            if "PatchMetrics" in AnalysisList:
                tabulatePatchMetrics("FinalPatches")
            elif "MDCP" in AnalysisList:
                tabulateMDCP("FinalPatches")
    else:
        #Calclulate Euclidean Distance based on max separation value
        gridcellsize = getRasterGridSize(ForestSingle)
        maxSep = MaxSeperation * gridcellsize
        outEucDistance = EucDistance(ForestSingle, maxSep, str(gridcellsize))

        #Extract only the max seperation value from the Euclidean distance
        EucDistanceExtract = ExtractByAttributes(outEucDistance, "VALUE = " + str(maxSep))
        EucDistanceExtract.save("EucDistance_MaxSep")

        #Reclassify Euclid distance so that NoData = 0
        EucDistReMapRange = RemapRange([[maxSep, maxSep, maxSep],["noData", "noData", 0]])
        EucDistReClass = Reclassify("EucDistance_MaxSep", "VALUE", EucDistReMapRange)

        #Reclassify  Single Forest so that NoData = 0
        ForestReMapRange = RemapRange([[1,1,1], ["noData", "noData", 0]])
        ForestReClass = Reclassify(ForestSingle, "VALUE", ForestReMapRange)

        #Add (sum) ForestReclass and EucDistanceReclass
        ForEuclidPlus = Plus(ForestReClass, EucDistReClass)

        #Run Region Group analysis on ForEuclidPlus, ignores 0/NoData values
        ForEuclidRegionGroup = RegionGroup(ForEuclidPlus,"EIGHT","CROSS","ADD_LINK","0")

        #Reclass Euclid Reclass to -99999
        EucRcReMapRange = RemapRange([[maxSep, maxSep, -99999],[0, 0, 0]])
        EucReClass999 =Reclassify(EucDistReClass,"VALUE", EucRcReMapRange)

        #Add (sum) regions result to EucReClass999 result
        RegionEucPlus = Plus(ForEuclidRegionGroup,EucReClass999)

        #Extract by Attribute Values greater than one to maintain the orginal boundaries of each patch
        RegionPatches = ExtractByAttributes(RegionEucPlus, "VALUE > 0")
        if MinPatchSize > 1:
            FinalPatchRas = ExtractByAttributes(RegionPatches, "COUNT >" + str(MinPatchSize -1))
            FinalPatchRas.save("FinalPatches")
##            tabulatePatchMetrics("FinalPatches")
        else:
            RegionPatches.save("FinalPatches")
##            tabulatePatchMetrics("FinalPatches")
##        arcpy.AddMessage(AnalysisList)
        if len(AnalysisList) == 2:
            tabulatePatchMetrics("FinalPatches")
            tabulateMDCP("FinalPatches")
        else:
            if "PatchMetrics" in AnalysisList:
                tabulatePatchMetrics("FinalPatches")
            elif "MDCP" in AnalysisList:
                tabulateMDCP("FinalPatches")
                
def tabulatePatchMetrics(PatchLURaster):
    env.workspace = outSpace
    arcpy.env.snapRaster = PatchLURaster
    arcpy.env.cellSize  = "MINOF"
    #Get the cell size from the Patch Landuse Raster
    gridcellsize = getRasterGridSize(PatchLURaster)

    #Create a table to store result
    tlist = []
    tlist = arcpy.ListTables()
    if "PatchResults" not in tlist:
        arcpy.CreateTable_management(env.workspace, "PatchResults")
        ResultFldsList = ["id", "TotalPatchArea","NumPatches", "LargestPatch", "AvePatchSize", "PatchDensity", "PLGP"]
        newtable = "Yes"
    else:
        ResultFldsList = ["TotalPatchArea","NumPatches", "LargestPatch", "AvePatchSize", "PatchDensity", "PLGP"]
        newtable = "No"
    #Add Fields to the new table
##    ResultFldsList = ["id", "TotalPatchArea","NumPatches", "LargestPatch", "AvePatchSize", "PatchDensity", "PLGP"]
    for rf in ResultFldsList:
        if rf <> "id":
            arcpy.AddField_management(env.workspace+"//" + "PatchResults", rf, "DOUBLE", "15", "8")
        else:
            arcpy.AddField_management(env.workspace +"//" + "PatchResults", rf, "TEXT", "", "", "50" )

    #Find the field in the Reporting  Unit Feature that holds the shape field
    shapeName = arcpy.Describe(ReportingUnitFeature).shapeFieldName

    #Generate list of Reporting Unit ids
    idlist = []
    AreaDict ={}
    rows = arcpy.SearchCursor(ReportingUnitFeature)
    row = rows.next()
    while row:
        id = row.getValue(ReportingUnitField)
        idlist.append(id)
        feat = row.getValue(shapeName)
        Area = feat.area
        AreaDict[id] = Area
        row = rows.next()
    del row, rows

    #For each Reporting Unit id run Tabulate Area Analysis and add the results to a dictionary
    resultsdict={}
    for i in idlist:
        squery = ReportingUnitField +"='" + i + "'"
        #Create a feature layer of the single reporting unit
        arcpy.MakeFeatureLayer_management(ReportingUnitFeature,"subwatersheds_Layer",squery,"#")
        temptable = "temptable"
        #Tabulate areas of patches within single reporting unit
        arcpy.sa.TabulateArea("subwatersheds_Layer",ReportingUnitField,PatchLURaster,"Value",temptable,gridcellsize)

        #Loop through each row in the table and calculate number of patches (numpatch), total area,
        #largest patch area(lrgpatch), average patch area (avepatch), and the proportion of largest patch area to
        #total patch area (proportion)
        
        rows = arcpy.SearchCursor(temptable)
        row = rows.next()

        while row:
            fldlist = []
            arealist = []
            flds = arcpy.ListFields(temptable)
            for f in flds:
                fldlist.append(f.name)
            for fld in fldlist:
                if "VALUE" in fld:
                    area = row.getValue(fld)
                    arealist.append(area)

            numpatch = len(arealist)
            totalarea = sum(arealist)
            lrgpatch = max(arealist)
            avepatch = totalarea/numpatch
            proportion = (lrgpatch/totalarea) * 100
            wshedarea = AreaDict[i]
            #get linear unit of watershed
            unit = getLinearUnit(ReportingUnitFeature)
            if unit == "Meter":
                wshedareaK = wshedarea* 0.000001
            elif "Foot" in unit:
                wshedareaK = wshedarea * 0.00000009290304
            patchdensity = numpatch/wshedareaK

            resultsdict[i] = (str(numpatch) + "," + str(lrgpatch) + "," + str(avepatch) + "," + str(proportion) + "," \
                              + str(totalarea) + "," + str(patchdensity))
            #print resultsdict[i]
            row = rows.next()

    #Add the results gathered above into the output table
    if newtable == "Yes":
        #if Results table does not already exists
        rows = arcpy.InsertCursor("PatchResults")
        row = rows.next()
        rownum = len(idlist)
        for k in resultsdict.keys():
            num, lrg, ave, prop, tarea, density = resultsdict[k].split(",")
            row = rows.newRow()
            row.id = k
            row.NumPatches = num
            row.LargestPatch = lrg
            row.AvePatchSize = ave
            row.PLGP = prop
            row.TotalPatchArea = tarea
            row.PatchDensity = density
            rows.insertRow(row)
        del row, rows
    elif newtable == "No":
        #if Results table already exists
        for k in resultsdict.keys():
            rows = arcpy.UpdateCursor("PatchResults", "ID = '" + k + "'")
            row = rows.next()
            while row:
                num, lrg, ave, prop, tarea, density = resultsdict[k].split(",")
##                row.id = k
                row.NumPatches = num
                row.LargestPatch = lrg
                row.AvePatchSize = ave
                row.PLGP = prop
                row.TotalPatchArea = tarea
                row.PatchDensity = density
                rows.updateRow(row)
                row = rows.next()
            del row, rows
                

def tabulateMDCP(PatchLURaster):
    resultDict = {}
    #Convert Final Patch Raster to polygon
##    env.workspace = os.path.dirname(PatchLURaster)
    arcpy.RasterToPolygon_conversion(PatchLURaster, outSpace + "\\FinalPatch_polygon", "NO_Simplify", "VALUE")

    #Convert Final Patch Raster to points to get the cell centroids
    arcpy.RasterToPoint_conversion(PatchLURaster, outSpace + "\\FinalPatch_centroids", "VALUE")

    env.workspace = outSpace
    #Dissolve the polygons on Value Field to make sure each patch is represented by a single polygon.
    arcpy.Dissolve_management("FinalPatch_polygon", "FinalPatch_poly_diss","grid_code","#",
                              "MULTI_PART","DISSOLVE_LINES")
    #Get a list of Reporting Unit Feature ids
    idlist = []
    rows = arcpy.SearchCursor(ReportingUnitFeature)
    row = rows.next()

    while row:
        id = row.getValue(ReportingUnitField)
        idlist.append(id)
        row =rows.next()
    del row, rows

    #Select the Reporting Unit and the intersecting polygons in FinalPatch_poly_diss
    for i in idlist:
        squery = ReportingUnitField + "='" + i + "'"
        print i
        #Create a feature layer of the single reporting unit
        arcpy.MakeFeatureLayer_management(ReportingUnitFeature,"subwatersheds_Layer",squery,"#")

        #Create a feature layer of the FinalPatch_poly_diss
        arcpy.MakeFeatureLayer_management("FinalPatch_poly_diss", "FinalPatch_diss_Layer")

        #Create a feature layer of the FinalPatch_centroids
        arcpy.MakeFeatureLayer_management("FinalPatch_centroids", "FinalPatch_centroids_Layer")

        #Select the centroids that are in the "subwatersheds_Layer"
        arcpy.SelectLayerByLocation_management("FinalPatch_centroids_Layer","INTERSECT","subwatersheds_Layer")
     
        #Get a list of centroids with in the selected Reporting Unit (this is necessary to match the raster processing
        #selection which selects only grid cells whose center is within the reporting unit).
        rows = arcpy.SearchCursor("FinalPatch_centroids_Layer")
        row = rows.next()
        centroidList = []
        while row:
            gridid = row.getValue("Grid_Code")
            if str(gridid) not in centroidList:
                centroidList.append(str(gridid))
            row = rows.next()
        totalnumPatches = len(centroidList)
        del row, rows

       # Select the patches that have centroids within the "subwatershed_Layer" using the centroid list

        values = ",".join(centroidList)
        arcpy.SelectLayerByAttribute_management("FinalPatch_diss_Layer", "NEW_SELECTION", "GRID_CODE IN(" + values + ")")


        #Calculate Near Distances for each watershed
        
        arcpy.GenerateNearTable_analysis("FinalPatch_diss_Layer",["FinalPatch_diss_Layer"], "neartable",
                                         SearchRadius,"NO_LOCATION","NO_ANGLE","CLOSEST","0")

        #Get total number of patches with neighbors and calculate the mean distance
        rows = arcpy.SearchCursor("neartable")
        row = rows.next()
        distlist = []
        while row:
            distance = row.getValue("NEAR_DIST")
            distlist.append(distance)
            row = rows.next()
        del row, rows
        pwnCount = len(distlist)
        totalArea = sum(distlist)
        averageDist = totalArea/pwnCount
        pwonCount = totalnumPatches - pwnCount
        
        resultDict[i] = str(pwnCount) +  "," + str(pwonCount) +"," + str(averageDist)
    print resultDict
    #Check for Patch Results table in workspace
    tlist = []
    tlist = arcpy.ListTables()
    if "PatchResults" not in tlist:
        #Create a table to store result
        arcpy.CreateTable_management(env.workspace, "PatchResults")
        ResultFldsList = ["id", "MDCP", "PWON", "PWN"]
        for rf in ResultFldsList:
            if rf <> "id":
                arcpy.AddField_management(env.workspace+"//" + "PatchResults", rf, "DOUBLE", "15", "8")
            else:
                arcpy.AddField_management(env.workspace +"//" + "PatchResults", rf, "TEXT", "", "", "50" )
            
        #Add the results to the output table
        rows = arcpy.InsertCursor("PatchResults")
        row = rows.next()
        for k in resultDict.keys():
            pwn, pwon, mdcp = resultDict[k].split(",")
            row = rows.newRow() 
            row.id = k
            row.MDCP = mdcp
            row.PWON = pwon
            row.PWN = pwn
            rows.insertRow(row)
        del row, rows
    else:
        ResultFldsList = ["MDCP", "PWON", "PWN"]
        #Add fields to "PatchResults" table
        for rf in ResultFldsList:
            arcpy.AddField_management(env.workspace +"//" + "PatchResults", rf, "TEXT", "", "", "50" )

        #Add the results to the output table
        for k in resultDict.keys():
            rows = arcpy.UpdateCursor("PatchResults",  "ID ='" + k + "'")
            row = rows.next()
            while row:
                pwn, pwon, mdcp = resultDict[k].split(",")
##                row.id = k
                row.MDCP = mdcp
                row.PWON = pwon
                row.PWN = pwn
                rows.updateRow(row)
                row = rows.next()
            del row, rows
            
if __name__ == "__main__":
    main(sys.argv)