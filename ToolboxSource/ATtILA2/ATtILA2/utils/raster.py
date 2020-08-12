""" Utilities specific to rasters

"""
import arcpy
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


def getEdgeCoreGrid(m, lccObj, lccClassesDict, inLandCoverGrid, PatchEdgeWidth_str, processingCellSize_str, timer, shortName):
    # Get the lccObj values dictionary to determine if a grid code is to be included in the effective reporting unit area calculation    
    lccValuesDict = lccObj.values
    landCoverValues = raster.getRasterValues(inLandCoverGrid)
    
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
                         processingCellSize_str, timer):
    # create a list of all the grid values in the selected landcover grid
    landCoverValues = raster.getRasterValues(inLandCoverGrid)
    
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
