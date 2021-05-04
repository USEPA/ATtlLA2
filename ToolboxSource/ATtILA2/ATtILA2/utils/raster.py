""" Utilities specific to rasters

"""
import arcpy
import os
from arcpy.sa import Con,EucDistance,Raster,Reclassify,RegionGroup,RemapValue,SetNull
from . import *
from .messages import AddMsg
## this is the code copied from pylet-master\pylet\arcpyutil\raster.py
import arcpy as _arcpy
def getRasterPointFromRowColumn(raster, row, column):
    """ Get an arcpy `Point`_ object from an arcpy `Raster`_ object and zero based row and column indexes.

        **Description:**
        
        The row and column are zero-based and start in the upper left corner.  The arcpy `Point`_ object returned has
        X and Y coordinates representing the cell identified by the specified row and column.
        
        
        **Arguments:**
        
        * *raster* - arcpy `Raster`_ object
        * *row* - integer representing the zero based index of the row
        * *column* - integer representing the zero based index of the column
        
        
        **Returns:** 
        
        * arcpy `Point`_ object 
        
        .. _Point: http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#/Point/000v000000mv000000/
        .. _Raster: http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#/Raster/000v000000wt000000/

        
    """    

    
    extent = raster.extent    
    upperLeftX = extent.XMin
    upperLeftY = extent.YMax

    xDistanceFromUpperLeft = column * raster.meanCellWidth
    yDistanceFromUpperLeft = row * raster.meanCellHeight
    
    x = upperLeftX + xDistanceFromUpperLeft
    y = upperLeftY - yDistanceFromUpperLeft

    point = _arcpy.Point(x,y)
    
    return point


def getRasterValues(inRaster):
    """Utility for creating a python list of values from a raster's VALUE field.
    
    ** Description: **
        
        This function will open a search cursor on the raster and iterate through all the rows
        and collect all values in a python list object. By design, values in the raster's VALUE
        field are unique.
    
    **Arguments:**
    
        * *raster* - any raster dataset with an attribute table.
   
    **Returns:**
    
        * *valuesList* - a python list of unique values
        
    """
    
    # warn user if input land cover grid has values not defined in LCC file
    rows = _arcpy.SearchCursor(inRaster) 

    valuesList = []
    for row in rows:
        valuesList.append(row.getValue("VALUE"))

    del row
    del rows
        
    return valuesList
## end of the code copied from pylet-master\pylet\arcpyutil\raster.py


def splitRasterYN(inRaster, maxSide):
    """Check if the raster is too large to perform a polygon conversion without first tiling the raster.
    
    ** Description: **
    
    **Arguments:**
    
        * *inRaster* - any raster dataset
        * *maxSide* - integer value
        
    **Returns:**
    
        * *boolean* - True, if the raster is too large
        * *list* - binary values indicating if number of raster columns and the number of raster rows exceed the specified maximum side 
    
    """
    splitYN = True
    columns = arcpy.GetRasterProperties_management(inRaster, 'COLUMNCOUNT').getOutput(0)
    xsplit = int(float(columns) / maxSide) + 1
    rows = arcpy.GetRasterProperties_management(inRaster, 'ROWCOUNT').getOutput(0)
    ysplit = int (float(rows) / maxSide) + 1
    xySplits = [xsplit, ysplit]
     
    if xsplit*ysplit == 1:
        splitYN = False
        
    return splitYN, xySplits


def clipGridByBuffer(inReportingUnitFeature,outName,inLandCoverGrid,inBufferDistance=None):
    if arcpy.Exists(outName):
        arcpy.Delete_management(outName)
        
    if inBufferDistance:
        # Buffering Reporting unit features...
        cellSize = Raster(inLandCoverGrid).meanCellWidth
        linearUnits = arcpy.Describe(inLandCoverGrid).spatialReference.linearUnitName
        bufferFloat = cellSize * (int(inBufferDistance)+1)
        bufferDistance = "%s %s" % (bufferFloat, linearUnits)
        arcpy.Buffer_analysis(inReportingUnitFeature, "in_memory/ru_buffer", bufferDistance, "#", "#", "ALL")
        
    # Clipping input grid to desired extent...
    if inBufferDistance:
        clippedGrid = arcpy.Clip_management(inLandCoverGrid, "#", outName,"in_memory/ru_buffer", "", "NONE")
        arcpy.Delete_management("in_memory")
    else:
        clippedGrid = arcpy.Clip_management(inLandCoverGrid, "#", outName, inReportingUnitFeature, "", "NONE")
    
    arcpy.BuildRasterAttributeTable_management(clippedGrid, "Overwrite")
    
    return clippedGrid
    
def getIntersectOfGrids(lccObj,inLandCoverGrid, inSlopeGrid, inSlopeThresholdValue, timer):
            
    # Generate the slope X land cover grid where areas below the threshold slope are
    # set to the value 'Maximum Land Cover Class Value + 1'.
    LCGrid = Raster(inLandCoverGrid)
    SLPGrid = Raster(inSlopeGrid)
    
    # find the highest value found in LCC XML file or land cover grid  
    lccValuesDict = lccObj.values
    maxValue = LCGrid.maximum
    xmlValues = lccObj.getUniqueValueIdsWithExcludes()
    for v in xmlValues:
        if v > maxValue:
            maxValue = v

    AddMsg(timer.split() + " Generating land cover above slope threshold grid...")    
    AreaBelowThresholdValue = int(maxValue + 1)
    delimitedVALUE = arcpy.AddFieldDelimiters(SLPGrid,"VALUE")
    whereClause = delimitedVALUE+" >= " + inSlopeThresholdValue
    SLPxLCGrid = Con(SLPGrid, LCGrid, AreaBelowThresholdValue, whereClause)
    
    # determine if a grid code is to be included in the effective reporting unit area calculation    
    # get the frozenset of excluded values (i.e., values not to use when calculating the reporting unit effective area)
    excludedValues = lccValuesDict.getExcludedValueIds()
        
    # if certain land cover codes are tagged as 'excluded = TRUE', generate grid where land cover codes are 
    # preserved for areas coincident with steep slopes, areas below the slope threshold are coded with the 
    # AreaBelowThresholdValue except for where the land cover code is included in the excluded values list.
    # In that case, the excluded land cover values are maintained in the low slope areas.
    if excludedValues:
        # build a whereClause string (e.g. "VALUE" = 11 or "VALUE" = 12") to identify where on the land cover grid excluded values occur
        AddMsg(timer.split() + " Inserting EXCLUDED values into areas below slope threshold...")
        stringStart = delimitedVALUE+" = "
        stringSep = " or "+delimitedVALUE+" = "
        whereExcludedClause = stringStart + stringSep.join([str(item) for item in excludedValues])
        SLPxLCGrid = Con(LCGrid, LCGrid, SLPxLCGrid, whereExcludedClause) 
    
    return SLPxLCGrid

def getNullSubstituteGrid(lccObj, inLandCoverGrid, inSubstituteGrid, nullValuesList, cleanupList, timer):
    # Set areas in the inSubstituteGrid to NODATA using the nullValuesList. For areas not in the nullValuesList, substitute
    # the grid values with those from the inLandCoverGrid
    LCGrid = Raster(inLandCoverGrid)
    subGrid = Raster(inSubstituteGrid)
    
    # find the highest value found in LCC XML file or land cover grid  
    lccValuesDict = lccObj.values
    maxValue = LCGrid.maximum
    xmlValues = lccObj.getUniqueValueIdsWithExcludes()
    for v in xmlValues:
        if v > maxValue:
            maxValue = v
    
    # Add 1 to the highest value and then add it to the list of values to exclude during metric calculations       
    valueToExclude = int(maxValue + 1)
    excludedValuesFrozen = lccValuesDict.getExcludedValueIds()
    excludedValues = [item for item in excludedValuesFrozen]
    excludedValues.append(valueToExclude)
    
    # build whereClause string (e.g. "VALUE" <> 11 or "VALUE" <> 12") to identify areas to substitute the valueToExclude
    delimitedVALUE = arcpy.AddFieldDelimiters(subGrid,"VALUE")
    stringStart = delimitedVALUE+" <> "
    stringSep = " or "+delimitedVALUE+" <> "
    whereClause = stringStart + stringSep.join([str(item) for item in nullValuesList])
    AddMsg(timer.split() + " Generating land cover in floodplain grid...") 
    nullSubstituteGrid = Con(subGrid, LCGrid, valueToExclude, whereClause)
    
    return nullSubstituteGrid, excludedValues


def getEdgeCoreGrid(m, lccObj, lccClassesDict, inLandCoverGrid, PatchEdgeWidth_str, processingCellSize_str, timer, shortName, scratchNameReference):
    # Get the lccObj values dictionary to determine if a grid code is to be included in the effective reporting unit area calculation    
    lccValuesDict = lccObj.values
    #landCoverValues = raster.getRasterValues(inLandCoverGrid)
    landCoverValues = getRasterValues(inLandCoverGrid)
    
    # get the grid codes for this specified metric
    ClassValuesList = lccClassesDict[m].uniqueValueIds.intersection(landCoverValues)
    
    # get the frozenset of excluded values (i.e., values not to use when calculating the reporting unit effective area)
    ExcludedValueList = lccValuesDict.getExcludedValueIds().intersection(landCoverValues)

    # create grid where cover type of interest (e.g., forest) is coded 3, excluded values are coded 1, everything else is coded 2
    reclassPairs = []
    for val in landCoverValues:
        oldValNewVal = []
        oldValNewVal.append(val)
        if val in ClassValuesList:
            oldValNewVal.append(3)
            reclassPairs.append(oldValNewVal)
        elif val in ExcludedValueList:
            oldValNewVal.append(1)
            reclassPairs.append(oldValNewVal)
        else:
            oldValNewVal.append(2)
            reclassPairs.append(oldValNewVal)
            
    AddMsg(timer.split() + " Step 1 of 4: Reclassing land cover grid to Class = 3, Other = 2, and Excluded = 1...")
    reclassGrid = Reclassify(inLandCoverGrid,"VALUE", RemapValue(reclassPairs))
    
    AddMsg(timer.split() + " Step 2 of 4: Setting Class areas to Null...")
    delimitedVALUE = arcpy.AddFieldDelimiters(reclassGrid,"VALUE")
    otherGrid = SetNull(reclassGrid, 1, delimitedVALUE+" = 3")
    
    AddMsg(timer.split() + " Step 3 of 4: Finding distance from Other...")
    distGrid = EucDistance(otherGrid)
    
    AddMsg(timer.split() + " Step 4 of 4: Delimiting Class areas to Edge = 3 and Core = 4...")
    edgeDist = round(float(PatchEdgeWidth_str) * float(processingCellSize_str)) 

    zonesGrid = Con((distGrid >= edgeDist) & reclassGrid, 4, reclassGrid)
    
    # it appears that ArcGIS cannot process the BuildRasterAttributeTable request without first saving the raster.
    # This step wasn't the case earlier. Either ESRI changed things, or I altered something in ATtILA that unwittingly caused this. -DE
    namePrefix = shortName+"_"+"Raster"+m+PatchEdgeWidth_str
    scratchName = arcpy.CreateScratchName(namePrefix, "", "RasterDataset")
    scratchNameReference[0] = scratchName
    zonesGrid.save(scratchName)
            
    arcpy.BuildRasterAttributeTable_management(zonesGrid, "Overwrite")  

    arcpy.AddField_management(zonesGrid, "CATEGORY", "TEXT", "#", "#", "10")
    updateCoreEdgeCategoryLabels(zonesGrid)
            
    return zonesGrid

def updateCoreEdgeCategoryLabels(Raster):
    #Updates the CATEGORY field in the ForestCoreEdge with "Core" and "Edge" values
    rows = arcpy.UpdateCursor(Raster)
    row = rows.next()
    
    while row:
        #VALUE = 1 indicates a Core cell, Value = 3 is an Edge cell
        v = row.getValue("Value")
        if v == 4:
            row.CATEGORY = "Core"
        elif v == 3:
            row.CATEGORY = "Edge"
        elif v == 2:
            row.CATEGORY = "Other"
        elif v == 1:
            row.CATEGORY = "Excluded"
        rows.updateRow(row)
        row = rows.next()  
    
    
def createPatchRaster(m,lccObj, lccClassesDict, inLandCoverGrid, metricConst, maxSeparation, minPatchSize, 
                         processingCellSize_str, timer, scratchNameReference):
    # create a list of all the grid values in the selected landcover grid
    #landCoverValues = raster.getRasterValues(inLandCoverGrid)
    landCoverValues = getRasterValues(inLandCoverGrid)
    
    # for the selected land cover class, get the class codes found in the input landcover grid
    lccValuesDict = lccObj.values
    classValuesList = lccClassesDict[m].uniqueValueIds.intersection(landCoverValues)
    
    # get the frozenset of excluded values (i.e., values not to use when calculating the reporting unit effective area)
    excludedValuesList = lccValuesDict.getExcludedValueIds().intersection(landCoverValues)
    
    # create class (value = 3) / other (value = 0) / excluded grid (value = -9999) raster
    # define the reclass values
    classValue = metricConst.classValue
    excludedValue = metricConst.excludedValue
    otherValue = metricConst.otherValue
    newValuesList = [classValue, excludedValue, otherValue]
    
    # generate a reclass list where each item in the list is a two item list: the original grid value, and the reclass value
    reclassPairs = getInOutOtherReclassPairs(landCoverValues, classValuesList, excludedValuesList, newValuesList)
            
    AddMsg(timer.split() + " Reclassing land cover to Class:"+m+" = "+str(classValue)+", Other = "+str(otherValue)+
           ", and Excluded = "+str(excludedValue)+"...")
    reclassGrid = Reclassify(inLandCoverGrid,"VALUE", RemapValue(reclassPairs))
     
    # create patch raster where:
    #    clusters of cells within the input threshold distance are considered a single patch
    #    and patches below the input minimum size have been discarded
    
    # Ensure all parameter inputs are the appropriate number type
    intMaxSeparation = int(maxSeparation)
    intMinPatchSize = int(minPatchSize)
    
    # Check if Maximum Separation > 0 if it is then skip to regions group analysis otherwise run Euclidean distance
    if intMaxSeparation == 0:
        AddMsg(timer.split() + " Assigning unique numbers to each unconnected cluster of Class:"+m+"...")
        regionOther = RegionGroup(reclassGrid == classValue,"EIGHT","CROSS","ADD_LINK","0")
    else:
        AddMsg(timer.split() + " Connecting clusters of Class:"+m+" within maximum separation distance...")
        fltProcessingCellSize = float(processingCellSize_str)
        maxSep = intMaxSeparation * float(processingCellSize_str)
        delimitedVALUE = arcpy.AddFieldDelimiters(reclassGrid,"VALUE")
        whereClause = delimitedVALUE+" < " + str(classValue)
        classRaster = SetNull(reclassGrid, 1, whereClause)
        eucDistanceRaster = EucDistance(classRaster, maxSep, fltProcessingCellSize)

        # Run Region Group analysis on UserEuclidPlus, ignores 0/NoData values
        AddMsg(timer.split() + " Assigning unique numbers to each unconnected cluster of Class:"+m+"...")
        UserEuclidRegionGroup = RegionGroup(eucDistanceRaster >= 0,"EIGHT","CROSS","ADD_LINK","0")

        # Maintain the original boundaries of each patch
        regionOther = Con(reclassGrid == classValue,UserEuclidRegionGroup, reclassGrid)

    if intMinPatchSize > 1:
        AddMsg(timer.split() + " Eliminating clusters below minimum patch size...")
        delimitedCOUNT = arcpy.AddFieldDelimiters(regionOther,"COUNT")
        whereClause = delimitedCOUNT+" < " + str(intMinPatchSize)
        regionOtherFinal = Con(regionOther, otherValue, regionOther, whereClause)
    else:
        regionOtherFinal = regionOther

    # add the excluded class areas back to the raster if present
    if excludedValuesList:
        regionOtherExcluded = Con(reclassGrid == excludedValue, reclassGrid, regionOtherFinal)
    else:
        regionOtherExcluded = regionOtherFinal

    # The Patch Metrics tool appears to have trouble calculating its metrics when the raster area is large and the
    # regionOtherExcluded grid is treated as a raster object in memory and not saved as a raster on disk
    namePrefix = metricConst.shortName+"_"+m+"_PatchRast"
    scratchName = arcpy.CreateScratchName(namePrefix, "", "RasterDataset")
    regionOtherExcluded.save(scratchName)
    desc = arcpy.Describe(regionOtherExcluded)
    scratchNameReference[0] = desc.catalogPath
    
    return regionOtherExcluded

    
def getInOutOtherReclassPairs(allRasterValues, selectedValuesList, excludedValuesList, newValuesList):
    # Generate a reclass list where each item in the list is a two item list: the original grid value, and the reclass value
    # Three reclass categories are defined:
    #     first value in the newValuesList is the new code for all values in the selected Class
    #     second value in the newValuesList is the code for any values tagged excluded in the LCC XML
    #     third value in the newvaluesList is the new code for everything else
    
    newIncludedValue = newValuesList[0]
    newExcludedValue = newValuesList[1]
    newOtherValue = newValuesList[2]
    reclassPairs = []
    for val in allRasterValues:
        oldValNewValPair = []
        oldValNewValPair.append(val)
        if val in selectedValuesList:
            oldValNewValPair.append(newIncludedValue)
        elif val in excludedValuesList:
            oldValNewValPair.append(newExcludedValue)
        else:
            oldValNewValPair.append(newOtherValue)
            
        reclassPairs.append(oldValNewValPair)
            
    return reclassPairs

def getRemapBinsByPercentStep(maxValue, pctStep):
    # Generate a reclass list to use in a RemapRange operation
    # The reclass list is comprised of a collection of three item lists (the bin)
    # The three items include:
    #    1) the start value of the reclass range,
    #    2) the end value of the reclass range, 
    #    3) and the new reclass value
    # The number of bins produced equals the maxValue divided by the pctStep
    # The pctStep should be a value between 1 and 100

    breakPnts = [i*(maxValue/100) for i in range(0, 100, pctStep)]
    reclassBins = []
    newValue = pctStep

    i = 1
    for n in range(len(breakPnts)):
        valuesStartStopNew = []
        # start of range
        valuesStartStopNew.append(breakPnts[n]) 
        if n+1 < len(breakPnts):
            # end of range
            valuesStartStopNew.append(breakPnts[n+1])
            # new grid value for values in range
            valuesStartStopNew.append(newValue*i)
        else:
            # end of last bin
            valuesStartStopNew.append(maxValue)
            valuesStartStopNew.append(100)
            
        reclassBins.append(valuesStartStopNew)

        i += 1
    
    return reclassBins

def getProximityWithBurnInGrid(classValuesList,excludedValuesList,inLandCoverGrid,landCoverValues,neighborhoodSize_str,
                     burnIn,burnInGrid,timer,rngRemap):

    # create class (value = 1) / other (value = 0) / excluded grid (value = 0) raster
    # define the reclass values
    classValue = 1
    excludedValue = 0
    otherValue = 0
    newValuesList = [classValue, excludedValue, otherValue]
    
    # generate a reclass list where each item in the list is a two item list: the original grid value, and the reclass value
    reclassPairs = getInOutOtherReclassPairs(landCoverValues, classValuesList, excludedValuesList, newValuesList)
      
    AddMsg(("{0} Reclassifying selected land cover class to 1. All other values = 0...").format(timer.split()))
    reclassGrid = Reclassify(inLandCoverGrid,"VALUE", RemapValue(reclassPairs))
    
    AddMsg(("{0} Performing focal SUM on reclassified raster using {1} x {1} cell neighborhood...").format(timer.split(), neighborhoodSize_str))
    neighborhood = arcpy.sa.NbrRectangle(int(neighborhoodSize_str), int(neighborhoodSize_str), "CELL")
    focalGrid = arcpy.sa.FocalStatistics(reclassGrid == classValue, neighborhood, "SUM")
    
    AddMsg(("{0} Reclassifying focal SUM results into 20% breaks...").format(timer.split()))
    proximityGrid = Reclassify(focalGrid, "VALUE", rngRemap)

    if burnIn == "true":
        AddMsg(("{0} Burning excluded areas into proximity grid...").format(timer.split()))
        delimitedVALUE = arcpy.AddFieldDelimiters(burnInGrid,"VALUE")
        whereClause = delimitedVALUE+" = 0"
        proximityGrid = Con(burnInGrid, proximityGrid, burnInGrid, whereClause)
           
    return proximityGrid

def getViewGrid(classValuesList, excludedValuesList, inLandCoverGrid, landCoverValues, viewRadius, conValues, timer):
    # create class (value = 1) / other (value = 0) / excluded grid (value = 0) raster
    # define the reclass values
    classValue = 1
    excludedValue = 0
    otherValue = 0
    newValuesList = [classValue, excludedValue, otherValue]
    
    # generate a reclass list where each item in the list is a two item list: the original grid value, and the reclass value
    reclassPairs = getInOutOtherReclassPairs(landCoverValues, classValuesList, excludedValuesList, newValuesList)
      
    AddMsg(("{0} Reclassifying selected land cover class to 1. All other values = 0...").format(timer.split()))
    reclassGrid = Reclassify(inLandCoverGrid,"VALUE", RemapValue(reclassPairs))
    
    AddMsg(("{0} Performing focal SUM on reclassified raster using {1} cell radius neighborhood...").format(timer.split(), viewRadius))
    neighborhood = arcpy.sa.NbrCircle(int(viewRadius), "CELL")
    focalGrid = arcpy.sa.FocalStatistics(reclassGrid == classValue, neighborhood, "SUM")
    
    AddMsg(("{0} Reclassifying focal SUM results into view = 0 and no-view = 1 binary raster...").format(timer.split()))
#    delimitedVALUE = arcpy.AddFieldDelimiters(focalGrid,"VALUE")
#    whereClause = delimitedVALUE+" = 0"
#    viewGrid = Con(focalGrid, 1, 0, whereClause)
    whereValue = conValues[0]
    trueValue = conValues[1]
    viewGrid = Con(Raster(focalGrid) == whereValue, trueValue)
    return viewGrid

def getLargePatchViewGrid(classValuesList, excludedValuesList, inLandCoverGrid, landCoverValues, viewRadius, conValues, minimumPatchSize, timer, saveIntermediates, metricConst):
    # create class (value = 1) / other (value = 0) / excluded grid (value = 0) raster
    # define the reclass values
    classValue = 1
    excludedValue = 0
    otherValue = 0
    newValuesList = [classValue, excludedValue, otherValue]
    
    # generate a reclass list where each item in the list is a two item list: the original grid value, and the reclass value
    reclassPairs = getInOutOtherReclassPairs(landCoverValues, classValuesList, excludedValuesList, newValuesList)


      
    AddMsg(("{0} Reclassifying selected land cover class to 1. All other values = 0...").format(timer.split()))
    reclassGrid = Reclassify(inLandCoverGrid,"VALUE", RemapValue(reclassPairs))
 
    ##calculate the big patches for LandCover
                
    AddMsg(("{0} Calculating size of excluded area patches...").format(timer.split()))
    regionGrid = RegionGroup(reclassGrid,"EIGHT","WITHIN","ADD_LINK")
                
    AddMsg(("{0} Assigning {1} to patches >= minimum size threshold...").format(timer.split(), "1"))
    delimitedCOUNT = arcpy.AddFieldDelimiters(regionGrid,"COUNT")
    whereClause = delimitedCOUNT+" >= " + minimumPatchSize + " AND LINK = 1"
    burnInGrid = Con(regionGrid, classValue, 0, whereClause)
                
    # save the intermediate raster if save intermediates option has been chosen
    if saveIntermediates: 
        namePrefix = metricConst.burnInGridName
        scratchName = arcpy.CreateScratchName(namePrefix, "", "RasterDataset")
        burnInGrid.save(scratchName)
        AddMsg(timer.split() + " Save intermediate grid complete: "+os.path.basename(scratchName))

    ##end of calculating the big patches for LandCover    


    AddMsg(("{0} Performing focal SUM on reclassified raster with big patches using {1} cell radius neighborhood...").format(timer.split(), viewRadius))
    neighborhood = arcpy.sa.NbrCircle(int(viewRadius), "CELL")
    #focalGrid = arcpy.sa.FocalStatistics(reclassGrid == classValue, neighborhood, "SUM")
    focalGrid = arcpy.sa.FocalStatistics(burnInGrid == classValue, neighborhood, "SUM")
    
    AddMsg(("{0} Reclassifying focal SUM results into view = 1 and no-view = 0 binary raster...").format(timer.split()))
#    delimitedVALUE = arcpy.AddFieldDelimiters(focalGrid,"VALUE")
#    whereClause = delimitedVALUE+" = 0"
#    viewGrid = Con(focalGrid, 1, 0, whereClause)
    whereValue = conValues[0]
    trueValue = conValues[1]
    viewGrid = Con(Raster(focalGrid) > whereValue, trueValue)
    return viewGrid


