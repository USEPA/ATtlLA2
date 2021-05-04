""" Utilities specific to vectors

"""

import arcpy
#from .. import utils
from . import files
from . import messages
#from . import fields
from .messages import AddMsg
from .fields import valueDelimiter
from arcpy.sa.Functions import SetNull


def bufferFeaturesByID(inFeatures, repUnits, outFeatures, bufferDist, ruIDField, ruLinkField):
    """Returns a feature class that contains only those portions of each reporting unit that are within a buffered 
        distance of a layer - the buffered features may be any geometry
    **Description:**
        This tool intersects reporting units with buffered features that contain the reporting unit ID. The buffer size (in map 
        units) is determined by the user. A new feature class is created that can be used as a reporting unit theme to 
        calculate metrics near the features. It is useful for generating metrics near water quality sample points where 
        watersheds that drain to the sample point are available.
    **Arguments:**
        * *inFeatures* - feature class that will be buffered
        * *repUnits* - reporting units that will be used for the clip
        * *outFeatures* - a feature class (without full path) that will be created as the output of this tool
        * *bufferDist* - distance in the units of the spatial reference of the input data to buffer
        * *ruIDField* - a field that exists in repUnits that contains a unique identifier for the reporting units.  
        * *ruLinkField* - a field that exists in the inFeatures that contains reporting unit IDs, linking buffered features
                            to reporting units
        
    **Returns:**
        * *outFeatures* - output feature class 
    """
    try:
        # Get a unique name with full path for the output features - will default to current workspace:
        outFeatures = arcpy.CreateScratchName(outFeatures,"","FeatureClass")
        
        # First perform a buffer on all the points with the specified distance.  
        # By using the "LIST" option and the unit ID field, the output contains a single multipart feature for every 
        # reporting unit.  The output is written to the user's scratch workspace.
        AddMsg("Buffering input features...")
        bufferedFeatures = arcpy.Buffer_analysis(inFeatures,"in_memory/bFeats", bufferDist,"FULL","ROUND","LIST",ruLinkField)
        
        # If the input features are polygons, we need to erase the the input polyons from the buffer output
        inGeom = arcpy.Describe(inFeatures).shapeType
        if inGeom == "Polygon":
            AddMsg("Erasing polygon areas from buffer areas...")
            newBufferFeatures = arcpy.Erase_analysis(bufferedFeatures,inFeatures,"in_memory/bFeats2")
            arcpy.Delete_management(bufferedFeatures)
            bufferedFeatures = newBufferFeatures
        
        # The script will be iterating through reporting units and using a whereclause to select each feature, so it will 
        # improve performance if we set up the right syntax for the whereclauses ahead of time.
        buffUnitID = arcpy.AddFieldDelimiters(bufferedFeatures,ruLinkField)
        repUnitID = arcpy.AddFieldDelimiters(repUnits,ruIDField)
        
        # Similarly, the syntax for the whereclause depends on the type of the reporting unit ID field. 
        delimitBuffValues = valueDelimiter(arcpy.ListFields(bufferedFeatures,ruLinkField)[0].type)
        delimitRUValues = valueDelimiter(arcpy.ListFields(repUnits,ruIDField)[0].type)

        # Get a count of the number of reporting units to give an accurate progress estimate.
        n = int(arcpy.GetCount_management(bufferedFeatures).getOutput(0))
        # Initialize custom progress indicator
        loopProgress = messages.loopProgress(n)

        i = 0 # Flag used to create the outFeatures the first time through.
        # Create a Search cursor to iterate through the reporting units with buffered features.
        Rows = arcpy.SearchCursor(bufferedFeatures,"","",ruLinkField)
        AddMsg("Clipping buffered features to each reporting unit...")
        # For each reporting unit:
        for row in Rows:
            # Get the reporting unit ID
            rowID = row.getValue(ruLinkField)
            # Set up the whereclause for the buffered features and the reporting units to select one of each
            whereClausePts = buffUnitID + " = " + delimitBuffValues(rowID)
            whereClausePolys = repUnitID + " = " + delimitRUValues(rowID)
            
            # Create an in-memory Feature Layer with the whereclause.  This is analogous to creating a map layer with a 
            # definition expression.
            arcpy.MakeFeatureLayer_management(bufferedFeatures,"buff_lyr",whereClausePts)
            arcpy.MakeFeatureLayer_management(repUnits,"poly_lyr",whereClausePolys)
            if i == 0: # If it's the first time through
                # Clip the buffered points using the reporting unit boundaries, and save the output as the specified output
                # feature class.
                arcpy.Clip_analysis("buff_lyr","poly_lyr",outFeatures,"#")
                i = 1 # Toggle the flag.
            else: # If it's not the first time through and the output feature class already exists
                # Perform the clip, but output the result to memory rather than writing to disk
                clipResult = arcpy.Clip_analysis("buff_lyr","poly_lyr","in_memory/buff","#")
                # Append the in-memory result to the output feature class
                arcpy.Append_management(clipResult,outFeatures,"NO_TEST")
                # Delete the in-memory result to conserve system resources
                arcpy.Delete_management(clipResult)
            # Delete the in-memory Feature Layers.  
            arcpy.Delete_management("buff_lyr")
            arcpy.Delete_management("poly_lyr")
            loopProgress.update()
    
        return outFeatures
    
    finally:
        try:
            # Clean up the search cursor object
            del Rows
            # Delete the temporary buffered features layer from the scratch workspace.  
            arcpy.Delete_management(bufferedFeatures)
        except:
            pass
      

def bufferFeaturesByIntersect(inFeatures, repUnits, outFeatures, bufferDist, unitID, cleanupList):
    """Returns a feature class that contains only those portions of each reporting unit that are within a buffered 
        distance of a layer - the buffered features may be any geometry
    **Description:**
        This tool intersects reporting units with buffered features that fall within the reporting unit. The buffer size (in map 
        units) is determined by the user. A new feature class is created that can be used as a reporting unit theme to 
        calculate metrics with the buffered areas. It is useful for generating metrics near streams that fall within the
        reporting unit.
        
        This tool makes the assumption that there is no attribute that links the features to be buffered with the 
        reporting units.  Because of this, it cannot buffer all the features at once - it must iterate through each
        reporting unit, first clipping features to the reporting unit boundaries, then buffering only those features
        and then finally clipping the buffers again to the reporting unit.  If the features can be linked to reporting
        units via an attribute, it should be faster to use the bufferFeaturesByID tool instead.
    **Arguments:**
        * *inFeatures* - one or more feature class that will be buffered
        * *repUnits* - reporting units that will be used for the clip
        * *outFeatures* - a feature class (without full path) that will be created as the output of this tool
        * *bufferDist* - distance in the units of the spatial reference of the input data to buffer
        * *unitID* - a field that exists in repUnits that contains a unique identifier for the reporting units. 
        * *cleanupList* - a list object for tracking intermediate datasets for cleanup at the user's request. 
        
    **Returns:**
        * *outFeatures* - output feature class 
    """
    from arcpy import env
    import os
    
    try:
        toolShortName = outFeatures[:outFeatures.find("_")]
        outFeatures = files.nameIntermediateFile([outFeatures,"FeatureClass"], cleanupList)
        
        # The tool accepts a semicolon-delimited list of input features - convert this into a python list object
        # it appears that long directory paths in the multivalue input box causes the delimiter to be quote-semicolon-quote
        # instead of just semicolon
        if "';'" in inFeatures:
            inFeatures = inFeatures.replace("';'",";")    
        if '";"' in inFeatures:
            inFeatures = inFeatures.replace('";"',";")
            
        inFeaturesList = inFeatures.split(";")
        outputList = []
        # Initialize list of polygon features for erase
        eraseList = []        
        
        for inFC in inFeaturesList:
            inFCDesc = arcpy.Describe(inFC)
            inFCName = inFCDesc.baseName
            if inFCDesc.shapeType == "Polygon":
                eraseList.append(inFC)
            
            if inFCDesc.HasM or inFCDesc.HasZ:
                AddMsg("Creating a copy of "+inFCName+" without M or Z values")
                copyFCNameBase = toolShortName+"_"+inFCName
                copyFCName = files.nameIntermediateFile([copyFCNameBase,"FeatureClass"], cleanupList)
                inFC = arcpy.FeatureClassToFeatureClass_conversion(inFC, env.workspace, os.path.basename(copyFCName))
                inFCDesc = arcpy.Describe(inFC)
                inFCName = inFCDesc.baseName
            else:
                inFCName = toolShortName+"_"+inFCDesc.baseName
            
            # Start by intersecting the input features and the reporting units 
            AddMsg("Intersecting "+inFCDesc.baseName+" and reporting units")
            firstIntersectionName = files.nameIntermediateFile([inFCName+"_intersect","FeatureClass"], cleanupList)
            intersectResult = arcpy.Intersect_analysis([repUnits,inFC],firstIntersectionName,"ALL","","INPUT")
            
            # We are later going to perform a second intersection with the reporting units layer, which will cause
            # a name collision with the reporting unitID field - in anticipation of this, rename the unitID field.
            # This functionality is dependent on the intermediate dataset being in a geodatabase - no shapefiles allowed.
            # It is also only available starting in 10.2.1, so also check the version number before proceeding
            # IF AlterField isn't an option, revert to add/calculate field methodology - slower and more clunky, but it works.
            newUnitID = arcpy.ValidateFieldName("new"+unitID, intersectResult) 
            gdbTest = arcpy.Describe(intersectResult).dataType
            arcVersion = arcpy.GetInstallInfo()['Version']
            if gdbTest == "FeatureClass" and arcVersion >= '10.2.1':
                arcpy.AlterField_management(intersectResult,unitID,newUnitID,newUnitID)
            else:
                # Get the properties of the unitID field
                fromFieldObj = arcpy.ListFields(intersectResult,unitID)[0]
                # Add the new field to the output table with the appropriate properties and the valid name
                arcpy.AddField_management(intersectResult,newUnitID,fromFieldObj.type,fromFieldObj.precision,fromFieldObj.scale,
                          fromFieldObj.length,fromFieldObj.aliasName,fromFieldObj.isNullable,fromFieldObj.required,
                          fromFieldObj.domain)
                # Copy the field values from the old to the new field
                arcpy.CalculateField_management(intersectResult,newUnitID,arcpy.AddFieldDelimiters(intersectResult,unitID))

            # Buffer these in-memory selected features and merge the output into multipart features by reporting unit ID
            AddMsg("Buffering intersected features")
            bufferName = files.nameIntermediateFile([inFCName+"_buffer","FeatureClass"],cleanupList)
            
            # If the input features are polygons, we need to erase the the input polygons from the buffer output
            inGeom = inFCDesc.shapeType
            if inGeom == "Polygon":
                # When we buffer polygons, we want to exclude the area of the polygon itself.  This can be done using the 
                # "OUTSIDE_ONLY" option in the buffer tool, but that is only available with an advanced license.  Check for
                # the right license level, revert to buffer/erase option if it's not available.
                licenseLevel = arcpy.CheckProduct("ArcInfo")
                if licenseLevel in ["AlreadyInitialized","Available"]:
                    bufferResult = arcpy.Buffer_analysis(intersectResult,bufferName,bufferDist,"OUTSIDE_ONLY","ROUND","LIST",[newUnitID])
                    AddMsg("Repairing buffer areas for input areal features...")
                    arcpy.RepairGeometry_management (bufferResult)
                else:
                    bufferResult = arcpy.Buffer_analysis(intersectResult,bufferName,bufferDist,"FULL","ROUND","LIST",[newUnitID])
                    AddMsg("Repairing buffer areas for input areal features...")
                    arcpy.RepairGeometry_management (bufferResult)
                    AddMsg("Erasing polygon areas from buffer areas...")
                    bufferErase = files.nameIntermediateFile([inFCName+"_bufferErase","FeatureClass"],cleanupList)
                    newBufferFeatures = arcpy.Erase_analysis(bufferResult,inFC,bufferErase)
                    bufferResult = newBufferFeatures
            else:
                bufferResult = arcpy.Buffer_analysis(intersectResult,bufferName,bufferDist,"FULL","ROUND","LIST",[newUnitID])
                AddMsg("Repairing buffer areas for input linear features...")
                arcpy.RepairGeometry_management (bufferResult)
            
            
            # Intersect the buffers with the reporting units
            AddMsg("Intersecting buffer features and reporting units")
            secondIntersectionName = files.nameIntermediateFile([inFCName+"_2ndintersect","FeatureClass"],cleanupList)
            secondIntersectResult = arcpy.Intersect_analysis([repUnits,bufferResult],secondIntersectionName,"ALL","","INPUT")            

            # Select only those intersected features whose reporting unit IDs match 
            # This ensures that buffer areas that fall outside of the input feature's reporting unit are excluded
            AddMsg("Trimming buffer zones to reporting unit boundaries")
            whereClause = arcpy.AddFieldDelimiters(secondIntersectResult,unitID) + " = " + arcpy.AddFieldDelimiters(secondIntersectResult,newUnitID)
            matchingBuffers = arcpy.MakeFeatureLayer_management(secondIntersectResult,"matchingBuffers",whereClause)

            # Dissolve those by reporting Unit ID.  
            AddMsg("Dissolving second intersection by reporting unit")
            if len(inFeaturesList) > 1:
                finalOutputName = files.nameIntermediateFile([inFCName+"_finalOutput","FeatureClass"],cleanupList)
            else: 
                finalOutputName = outFeatures # If this is the only one, it's already named.
            finalOutput = arcpy.Dissolve_management(matchingBuffers,finalOutputName,unitID)
            
            # Clean up the feature layer selection for the next iteration.
            arcpy.Delete_management(matchingBuffers)
            
            # keep track of list of outputs.  
            outputList.append(finalOutput)
        
        # merge and dissolve buffer features from all input feature classes into a single feature class.
        if len(inFeaturesList) > 1:
            AddMsg("Merging buffer zones from all input Stream features")
            mergeName = files.nameIntermediateFile(["mergeOutput","FeatureClass"],cleanupList)
            mergeOutput = arcpy.Merge_management(outputList,mergeName)
            finalOutput = arcpy.Dissolve_management(mergeOutput,outFeatures,unitID)
            # If any of the input features are polygons, we need to perform a final erase of the interior of these polygons from the output.
            AddMsg("Removing interior waterbody areas from buffer result")
            if len(eraseList) > 0:
                #  Merge all eraseFeatures so we only have to do this once...
                eraseName = files.nameIntermediateFile(["erasePolygons","FeatureClass"],cleanupList)
                eraseFeatureClass = arcpy.Merge_management(eraseList,eraseName)
                # Rename the old final output so that it becomes an intermediate dataset
                oldfinalOutputName = files.nameIntermediateFile([outFeatures+"_preErase","FeatureClass"],cleanupList)
                preEraseOutput = arcpy.Rename_management(finalOutput, oldfinalOutputName, "FeatureClass")
                try:
                    finalOutput = arcpy.Erase_analysis(preEraseOutput,eraseFeatureClass,outFeatures)
                except:
                    badEraseFeatures = arcpy.FeatureClassToFeatureClass_conversion(eraseFeatureClass,"%scratchworkspace%","badEraseFeatures")
                    badBuffer = arcpy.FeatureClassToFeatureClass_conversion(preEraseOutput,"%scratchworkspace%","badBuffer")
                    # There is a small chance that this buffer operation will produce a feature class with invalid geometry.  Try a repair.
                    arcpy.RepairGeometry_management(badBuffer,"DELETE_NULL")
                    arcpy.RepairGeometry_management(badEraseFeatures,"DELETE_NULL")
                    finalOutput = arcpy.Erase_analysis(badBuffer,badEraseFeatures,outFeatures)
                    arcpy.Delete_management(badBuffer)
                    arcpy.Delete_management(badEraseFeatures)
        
        return finalOutput, cleanupList 
    finally:
        pass
    
def bufferFeaturesWithoutBorders(inFeatures, repUnits, outFeatures, bufferDist, unitID, cleanupList):
    """Returns a feature class that contains the area of each reporting unit that is within a buffered distance of a 
        layer - the buffered features may be any geometry.
    **Description:**
        This tool buffers features and identifies the reporting unit that the buffered areas fall within. The buffer 
        size (in linear units) is determined by the user. A new feature class is created that can be used as a reporting 
        unit theme to calculate metrics with the buffered areas. It is useful for generating metrics near streams that 
        fall within the reporting unit.
        
        This tool ignores the boundaries between reporting units when creating buffers. If buffered areas should be
        restricted to the reporting unit where the input feature is located and not extend into nearby reporting units,
        the bufferFreaturesByIntersect should be used instead.
    **Arguments:**
        * *inFeatures* - one or more feature class that will be buffered
        * *repUnits* - reporting units that will be used for the clip
        * *outFeatures* - a feature class (without full path) that will be created as the output of this tool
        * *bufferDist* - distance in the units of the spatial reference of the input data to buffer
        * *unitID* - a field that exists in repUnits that contains a unique identifier for the reporting units. 
        * *cleanupList* - a list object for tracking intermediate datasets for cleanup at the user's request. 
        
    **Returns:**
        * *outFeatures* - output feature class 
    """
    from arcpy import env
    import os
    
    try:
        toolShortName = outFeatures[:outFeatures.find("_")]
        outFeatures = files.nameIntermediateFile([outFeatures,"FeatureClass"], cleanupList) 
        
        # The tool accepts a semicolon-delimited list of input features - convert this into a python list object
        # it appears that long directory paths in the multivalue input box causes the delimiter to be quote-semicolon-quote
        # instead of just semicolon
        if "';'" in inFeatures:
            inFeatures = inFeatures.replace("';'",";")    
        if '";"' in inFeatures:
            inFeatures = inFeatures.replace('";"',";")
            
        inFeaturesList = inFeatures.split(";") 
        outputList = []
        # Initialize list of polygon features for erase
        eraseList = []        
        
        for inFC in inFeaturesList:
            inFCDesc = arcpy.Describe(inFC)
            inFCName = inFCDesc.baseName 
            if inFCDesc.shapeType == "Polygon":
                eraseList.append(inFC)
            
            if inFCDesc.HasM or inFCDesc.HasZ: 
                AddMsg("Creating a copy of "+inFCName+" without M or Z values")
                copyFCNameBase = toolShortName+"_"+inFCName
                copyFCName = files.nameIntermediateFile([copyFCNameBase,"FeatureClass"], cleanupList)
                inFC = arcpy.FeatureClassToFeatureClass_conversion(inFC, env.workspace, os.path.basename(copyFCName))
                inFCDesc = arcpy.Describe(inFC)
                inFCName = inFCDesc.baseName
            else:
                inFCName = toolShortName+"_"+inFCDesc.baseName 
            
            ## Start by intersecting the input features and the reporting units 
            AddMsg("Intersecting "+inFCDesc.baseName+" and reporting units")
            firstIntersectionName = files.nameIntermediateFile([inFCName+"_intersect","FeatureClass"], cleanupList)
            intersectResult = arcpy.Intersect_analysis([repUnits,inFC],firstIntersectionName,"ALL","","INPUT") 

            ## We are later going to perform a second intersection with the reporting units layer, which will cause
            ## a name collision with the reporting unitID field - in anticipation of this, rename the unitID field.
            ## This functionality is dependent on the intermediate dataset being in a geodatabase - no shapefiles allowed.
            ## It is also only available starting in 10.2.1, so also check the version number before proceeding
            ## IF AlterField isn't an option, revert to add/calculate field methodology - slower and more clunky, but it works.
            newUnitID = arcpy.ValidateFieldName("new"+unitID, intersectResult)
            gdbTest = arcpy.Describe(intersectResult).dataType 
            arcVersion = arcpy.GetInstallInfo()['Version']
            if gdbTest == "FeatureClass" and arcVersion >= '10.2.1':
                arcpy.AlterField_management(intersectResult,unitID,newUnitID,newUnitID)
            else:
                # Get the properties of the unitID field
                fromFieldObj = arcpy.ListFields(intersectResult,unitID)[0]
                # Add the new field to the output table with the appropriate properties and the valid name
                arcpy.AddField_management(intersectResult,newUnitID,fromFieldObj.type,fromFieldObj.precision,fromFieldObj.scale,
                          fromFieldObj.length,fromFieldObj.aliasName,fromFieldObj.isNullable,fromFieldObj.required,
                          fromFieldObj.domain)
                # Copy the field values from the old to the new field
                arcpy.CalculateField_management(intersectResult,newUnitID,arcpy.AddFieldDelimiters(intersectResult,unitID))

            # Buffer these in-memory selected features and merge the output into multipart features by reporting unit ID
            AddMsg("Buffering intersected features")
            bufferName = files.nameIntermediateFile([inFCName+"_buffer","FeatureClass"],cleanupList)
            
            # If the input features are polygons, we need to erase the the input polygons from the buffer output
            inGeom = inFCDesc.shapeType
            if inGeom == "Polygon":
                # When we buffer polygons, we want to exclude the area of the polygon itself.  This can be done using the 
                # "OUTSIDE_ONLY" option in the buffer tool, but that is only available with an advanced license.  Check for
                # the right license level, revert to buffer/erase option if it's not available.
                licenseLevel = arcpy.CheckProduct("ArcInfo")
                if licenseLevel in ["AlreadyInitialized","Available"]:
                    bufferResult = arcpy.Buffer_analysis(intersectResult,bufferName,bufferDist,"OUTSIDE_ONLY","ROUND","LIST",[newUnitID])
                    AddMsg("Repairing buffer areas for input areal features...")
                    arcpy.RepairGeometry_management (bufferResult)
                else:
                    bufferResult = arcpy.Buffer_analysis(intersectResult,bufferName,bufferDist,"FULL","ROUND","LIST",[newUnitID])
                    AddMsg("Repairing buffer areas for input areal features...")
                    arcpy.RepairGeometry_management (bufferResult)
                    AddMsg("Erasing polygon areas from buffer areas...")
                    bufferErase = files.nameIntermediateFile([inFCName+"_bufferErase","FeatureClass"],cleanupList)
                    newBufferFeatures = arcpy.Erase_analysis(bufferResult,inFC,bufferErase)
                    bufferResult = newBufferFeatures
            else:
                bufferResult = arcpy.Buffer_analysis(intersectResult,bufferName,bufferDist,"FULL","ROUND","LIST",[newUnitID])
                AddMsg("Repairing buffer areas for input linear features...")
                arcpy.RepairGeometry_management (bufferResult)
            
            
            # Intersect the buffers with the reporting units
            AddMsg("Intersecting buffer features and reporting units")
            secondIntersectionName = files.nameIntermediateFile([inFCName+"_2ndintersect","FeatureClass"],cleanupList)
            secondIntersectResult = arcpy.Intersect_analysis([repUnits,bufferResult],secondIntersectionName,"ALL","","INPUT")            

            ## Select only those intersected features whose reporting unit IDs match 
            ## This ensures that buffer areas that fall outside of the input feature's reporting unit are excluded
            #AddMsg("Trimming buffer zones to reporting unit boundaries")
            #whereClause = arcpy.AddFieldDelimiters(secondIntersectResult,unitID) + " = " + arcpy.AddFieldDelimiters(secondIntersectResult,newUnitID)
            #matchingBuffers = arcpy.MakeFeatureLayer_management(secondIntersectResult,"matchingBuffers",whereClause)

            # Select all features no matter whether it falls outside of the input feature's reporting unit. 
            # This step is just to generate layer matchingBuffers which will be used later
            matchingBuffers = arcpy.MakeFeatureLayer_management(secondIntersectResult,"matchingBuffers","1 = 1")

            # Dissolve those by reporting Unit ID.  
            AddMsg("Dissolving second intersection by reporting unit")
            if len(inFeaturesList) > 1:
                finalOutputName = files.nameIntermediateFile([inFCName+"_finalOutput","FeatureClass"],cleanupList)
            else: 
                finalOutputName = outFeatures # If this is the only one, it's already named.
            finalOutput = arcpy.Dissolve_management(matchingBuffers,finalOutputName,unitID)
            
            # Clean up the feature layer selection for the next iteration.
            arcpy.Delete_management(matchingBuffers)
            
            # keep track of list of outputs.  
            outputList.append(finalOutput)
        
        # merge and dissolve buffer features from all input feature classes into a single feature class.
        if len(inFeaturesList) > 1:
            AddMsg("Merging buffer zones from all input Stream features")
            mergeName = files.nameIntermediateFile(["mergeOutput","FeatureClass"],cleanupList)
            mergeOutput = arcpy.Merge_management(outputList,mergeName)
            finalOutput = arcpy.Dissolve_management(mergeOutput,outFeatures,unitID)
            # If any of the input features are polygons, we need to perform a final erase of the interior of these polygons from the output.
            AddMsg("Removing interior waterbody areas from buffer result")
            if len(eraseList) > 0:
                #  Merge all eraseFeatures so we only have to do this once...
                eraseName = files.nameIntermediateFile(["erasePolygons","FeatureClass"],cleanupList)
                eraseFeatureClass = arcpy.Merge_management(eraseList,eraseName)
                # Rename the old final output so that it becomes an intermediate dataset
                oldfinalOutputName = files.nameIntermediateFile([outFeatures+"_preErase","FeatureClass"],cleanupList)
                preEraseOutput = arcpy.Rename_management(finalOutput, oldfinalOutputName, "FeatureClass")
                try:
                    finalOutput = arcpy.Erase_analysis(preEraseOutput,eraseFeatureClass,outFeatures)
                except:
                    badEraseFeatures = arcpy.FeatureClassToFeatureClass_conversion(eraseFeatureClass,"%scratchworkspace%","badEraseFeatures")
                    badBuffer = arcpy.FeatureClassToFeatureClass_conversion(preEraseOutput,"%scratchworkspace%","badBuffer")
                    # There is a small chance that this buffer operation will produce a feature class with invalid geometry.  Try a repair.
                    arcpy.RepairGeometry_management(badBuffer,"DELETE_NULL")
                    arcpy.RepairGeometry_management(badEraseFeatures,"DELETE_NULL")
                    finalOutput = arcpy.Erase_analysis(badBuffer,badEraseFeatures,outFeatures)
                    arcpy.Delete_management(badBuffer)
                    arcpy.Delete_management(badEraseFeatures)
        
        return finalOutput, cleanupList 
    finally:
        pass


def getIntersectOfPolygons(repUnits, uIDField, secondPoly, outFeatures, cleanupList, timer):
    '''This function performs an intersection and dissolve function on a set of polygon features.
    **Description:**
        This function intersects the representative units with a second polygon feature, splitting the second polygon at unit 
        boundaries and giving unit attributes to the split polygons.  The split polygons are then dissolved by the unit IDs.
    **Arguments:**
        * *repUnits* - the input representative areal units feature class that will be used to split the lines
        * *uIDField* - the ID field of the representative areal units feature class.  Each dissolved line feature will be assigned the respective uID
        * *secondPoly* - the second polygon feature class
        * *outFeatures* - name of the output feature class.
    **Returns:**
        * *outFeatures* - name of the output feature class.
    '''
     
    # Get a unique name with full path for the output features - will default to current workspace:
    toolShortName = outFeatures[:outFeatures.find("_")]
    
    desc1 = arcpy.Describe(repUnits)
    desc2 = arcpy.Describe(secondPoly)
    
    # Intersect the reporting unit features with the floodplain features
    AddMsg(timer.split() + " Intersecting %s with %s..." % (desc1.basename, desc2.basename)) 
    intersectFeatures = files.nameIntermediateFile([toolShortName+"_Intersect","FeatureClass"], cleanupList)
    intersection = arcpy.Intersect_analysis([repUnits, secondPoly],intersectFeatures,"ALL","","INPUT")
     
    # Dissolve the intersected lines on the unit ID fields.
    outFeatures = files.nameIntermediateFile([outFeatures,"FeatureClass"], cleanupList)
    #dissolveFields = uIDField.name
    dissolveFields = uIDField
    AddMsg(timer.split() + " Dissolving %s zone features..." % (desc2.basename))  
    arcpy.Dissolve_management(intersection,outFeatures,dissolveFields,"","MULTI_PART","DISSOLVE_LINES")
    
    # Delete following intermediate datasets in order to reduce clutter if Intermediates are to be saved
    #arcpy.Delete_management(intersection)
 
    return outFeatures, cleanupList

def splitDissolveMerge(lines,repUnits,uIDField,mergedLines,inLengthField,lineClass=''):
    '''This function performs a intersection and dissolve function on a set of line features.
    **Description:**
        This function intersects the representative units with line features, clipping lines at unit boundaries and 
        giving unit attributes to each line.  The lines are then dissolved by the unit IDs (and a line class, if desired) 
    **Arguments:**
        * *lines* - the input line feature class
        * *repUnits* - the input representative areal units feature class that will be used to split the lines
        * *uIDField* - the ID field of the representative areal units feature class.  Each dissolved line feature will be assigned the respective uID
        * *inLengthField* - desired fieldname base for output length field
        * *lineClass* - optional field containing class values for the line feature class.  these classes are preserved through the split/dissolve/merge process
        * *mergedLines* - name of the output feature class.
    **Returns:**
        * *mergedLines* - name of the output feature class.
        * *lengthFieldName* - validated name of the field in the output feature class containing length values
    '''
    # Intersect the lines and the areal units
    # intersection = arcpy.Intersect_analysis([repUnits, lines],r"in_memory/intersect","ALL","","INPUT")
    # using previous technique of an output layer stored in memory is not dependable for large input datasets

    # Get a unique name with full path for the output features - will default to current workspace:
    intersectFeatures = arcpy.CreateScratchName("tmpIntersect","","FeatureClass")
    intersection = arcpy.Intersect_analysis([repUnits, lines],intersectFeatures,"ALL","","INPUT")
    dissolveFields = uIDField.name
    if lineClass != '':
        dissolveFields = [uIDField.name, lineClass]
    
    # Dissolve the intersected lines on the unit ID (and optional line class) fields. 
    arcpy.Dissolve_management(intersection,mergedLines,dissolveFields,"","MULTI_PART","DISSOLVE_LINES")
    
    arcpy.Delete_management(intersection)
    ## Add and calculate a length field for the new shapefile
    lengthFieldName = addLengthField(mergedLines,inLengthField)
    return mergedLines, lengthFieldName

def findIntersections(mergedRoads,inStreamFeature,mergedStreams,ruID,roadStreamMultiPoints,roadStreamIntersects,roadStreamSummary,
                      streamLengthFieldName,xingsPerKMFieldName,roadClass=""):
    '''This function performs an intersection analysis on two input line feature classes.  The desired output is 
    a count of the number of intersections per reporting unit ID (both line feature classes already contain this ID).  
    To obtain this cout the intersection output is first converted to singlepart features (from the default of multipart
    and then a frequency analysis performed.
    '''

    # Intersect the roads and the streams - the output is a multipoint feature class with one feature per combination 
    # of road class and streams per reporting unit
    arcpy.Intersect_analysis([mergedRoads,inStreamFeature],roadStreamMultiPoints,"ALL","#","POINT")
    
    # Because we want a count of individual intersection features, break apart the multipoints into single points
    arcpy.MultipartToSinglepart_management(roadStreamMultiPoints,roadStreamIntersects)
    
    # Perform a frequency analysis to get a count of the number of crossings per class per reporting unit
    fieldList = [ruID.name]
    if roadClass:
        fieldList.append(roadClass)
    arcpy.Frequency_analysis(roadStreamIntersects,roadStreamSummary,fieldList)
    
    # Lastly, calculate the number of stream crossings per kilometer of streams.
    # Join the stream layer to the summary table
    arcpy.JoinField_management(roadStreamSummary, ruID.name, mergedStreams, ruID.name, [streamLengthFieldName])
    # Set up a calculation expression for crossings per kilometer.
    calcExpression = "!FREQUENCY!/!" + streamLengthFieldName + "!"    
    addCalculateField(roadStreamSummary,xingsPerKMFieldName,calcExpression)

def roadsNearStreams(inStreamFeature,mergedStreams,bufferDist,inRoadFeature,inReportingUnitFeature,streamLengthFieldName,ruID,streamBuffer,
                     tmp1RdsNearStrms,tmp2RdsNearStrms,roadsNearStreams,rnsFieldName,inLengthField,roadClass=""):
    '''This function calculates roads near streams by first buffering a streams layer by the desired distance
    and then intersecting that buffer with a roads feature class.  This metric measures the total 
    length of roads within the buffer distance divided by the total length of stream in the reporting unit, both lengths 
    are measured in map units (e.g., m of road/m of stream).
    '''
    # For RNS metric, first buffer all the streams by the desired distance
    AddMsg("Buffering stream features...")
    arcpy.Buffer_analysis(inStreamFeature,streamBuffer,bufferDist,"FULL","ROUND","ALL","#")
    # Intersect the stream buffers with the input road layer to find road segments in the buffer zone
    AddMsg("Intersecting road features with stream buffers...")
    intersect1 = arcpy.Intersect_analysis([inRoadFeature, streamBuffer],tmp1RdsNearStrms,"ALL","#","INPUT")
    # Intersect the roads in the buffer zones with the reporting unit feature to assign RU Id values to road segments
    AddMsg("Assigning reporting unit feature ID values to road segments...")
    intersect2 = arcpy.Intersect_analysis([intersect1, inReportingUnitFeature],tmp2RdsNearStrms,"ALL","#","INPUT")
    
    # if overlapping polygons exist in reporting unit theme, the above intersection may result in several rows of data for a given reporting unit.
    # perform a dissolve to get a 1 to 1 relationship with input to output. Include the class field if provided.
    arcpy.AddMessage("Dissolving intersection result and calculating values...")
    dissolveFields = ruID.name
    if roadClass != '':
        dissolveFields = [ruID.name, roadClass] 
    # Dissolve the intersected lines on the unit ID (and optional line class) fields.
    arcpy.Dissolve_management(intersect2,roadsNearStreams,dissolveFields, "#","MULTI_PART","DISSOLVE_LINES")
    
    arcpy.Delete_management(intersect1)
    arcpy.Delete_management(intersect2)
    
    # Add and calculate a length field for the new shapefile
    roadLengthFieldName = addLengthField(roadsNearStreams,inLengthField)
    
    # Next join the merged streams layer to the roads/streambuffer intersection layer
    arcpy.JoinField_management(roadsNearStreams, ruID.name, mergedStreams, ruID.name, [streamLengthFieldName])
    # Set up a calculation expression for the roads near streams fraction
    calcExpression = "!" + roadLengthFieldName + "!/!" + streamLengthFieldName + "!"
    # Add a field for the roads near streams fraction
    rnsFieldName = addCalculateField(roadsNearStreams,rnsFieldName,calcExpression)


def addAreaField(inAreaFeatures, areaFieldName):
    '''This function checks for the existence of a field containing polygon area in square kilometers and if it does
        not exist, adds and populates it appropriate.
    **Description:**
        This function checks for the existence of a field containing polygon area in square kilometers and if it does
        not exist, adds and populates it appropriate.
    **Arguments:**
        * *inAreaFeatures* - the input feature class that will receive the field.      
    **Returns:**
        * *areaFieldName* - validated fieldname      
    '''
    # Set up the calculation expression for area in square kilometers
    shapeFieldName = arcpy.Describe(inAreaFeatures).shapeFieldName
    calcExpression = "!{0}.AREA@SQUAREKILOMETERS!".format(shapeFieldName)
    areaFieldName = addCalculateField(inAreaFeatures,areaFieldName,calcExpression)
    return areaFieldName    

def addLengthField(inLineFeatures,lengthFieldName):
    '''This function adds and populates a length field for the input line feature class
    **Description:**
        This function checks for the existence of a field containing line area in kilometers and if it does
        not exist, adds and populates it appropriate.
    **Arguments:**
        * *inLineFeatures* - the input feature class that will receive the field. 
        * *lengthFieldName* - the desired fieldname base for the output field    
    **Returns:**
        * *lengthFieldName* - validated fieldname      
    '''
    # Get a describe object
    lineDescription = arcpy.Describe(inLineFeatures)
    # Set a default for the length fieldName
    #lengthFieldName = "LenKM" + lineDescription.baseName
    
    # Set up the calculation expression for length in kilometers
    calcExpression = "!{0}.LENGTH@KILOMETERS!".format(lineDescription.shapeFieldName)
    lengthFieldName = addCalculateField(inLineFeatures,lengthFieldName,calcExpression)
    return lengthFieldName

def addCalculateField(inFeatures,fieldName,calcExpression,codeBlock='#'):
    '''This function checks for the existence of the desired field, and if it does not exist, adds and populates it
    using the given calculation expression
    **Description:**
        This function checks for the existence of the specified field and if it does
        not exist, adds and populates it as appropriate.  The output field is assumed to be of type double.
    **Arguments:**
        * *inFeatures* - the input feature class that will receive the field.
        * *fieldName* - field name string
        * *calcExpression* - string calculation expression in python 
        * *codeBlock* - optional python code block expression       
    **Returns:**
        * *fieldName* - validated fieldname      
    '''
    # Validate the desired field name for the dataset
    fieldName = arcpy.ValidateFieldName(fieldName, arcpy.Describe(inFeatures).path)
    
    # Check for existence of field.
    fieldList = arcpy.ListFields(inFeatures,fieldName)
    if not fieldList: # if the list of fields that exactly match the validated fieldname is empty, then add the field
        arcpy.AddField_management(inFeatures,fieldName,"DOUBLE")
    else: # Otherwise warn the user that the field will be recalculated.
        AddMsg("The field {0} already exists in {1}, its values will be recalculated.".format(fieldName,inFeatures))
    arcpy.CalculateField_management(inFeatures,fieldName,calcExpression,"PYTHON",codeBlock)
    return fieldName      
def addCalculateFieldInteger(inFeatures,fieldName,calcExpression,codeBlock='#'):
    '''This function checks for the existence of the desired field, and if it does not exist, adds and populates it
    using the given calculation expression
    **Description:**
        This function checks for the existence of the specified field and if it does
        not exist, adds and populates it as appropriate.  The output field is assumed to be of type double.
    **Arguments:**
        * *inFeatures* - the input feature class that will receive the field.
        * *fieldName* - field name string
        * *calcExpression* - string calculation expression in python 
        * *codeBlock* - optional python code block expression       
    **Returns:**
        * *fieldName* - validated fieldname      
    '''
    # Validate the desired field name for the dataset
    fieldName = arcpy.ValidateFieldName(fieldName, arcpy.Describe(inFeatures).path)
    
    # Check for existence of field.
    fieldList = arcpy.ListFields(inFeatures,fieldName)
    if not fieldList: # if the list of fields that exactly match the validated fieldname is empty, then add the field
        arcpy.AddField_management(inFeatures,fieldName,"SHORT")
    else: # Otherwise warn the user that the field will be recalculated.
        AddMsg("The field {0} already exists in {1}, its values will be recalculated.".format(fieldName,inFeatures))
    arcpy.CalculateField_management(inFeatures,fieldName,calcExpression,"PYTHON",codeBlock)
    return fieldName      

def tabulateMDCP(inPatchRaster, inReportingUnitFeature, reportingUnitIdField, rastoPolyFeature, patchCentroidsFeature, 
                 patchDissolvedFeature, nearPatchTable, zoneAreaDict, timer, pmResultsDict):
    #from pylet import utils
    #from . import calculate, conversion, environment, fields, files, messages, parameters, polygons, raster, settings, tabarea, table, vector
    resultDict = {}
    
    # put the proper field delimiters around the ID field name for SQL expressions
    delimitedField = arcpy.AddFieldDelimiters(inReportingUnitFeature, reportingUnitIdField)
    
    #Convert Final Patch Raster to polygon
    AddMsg(timer.split() + " Converting raster patches to polygons...")
    patchOnlyRaster = SetNull(inPatchRaster, inPatchRaster, "VALUE <= 0")
    arcpy.RasterToPolygon_conversion(patchOnlyRaster, rastoPolyFeature, "NO_Simplify", "VALUE")
    
    #Dissolve the polygons on Value Field to make sure each patch is represented by a single polygon.
    AddMsg(timer.split() + " Dissolving patch polygons by value field...")
    arcpy.Dissolve_management(rastoPolyFeature, patchDissolvedFeature,"gridcode","#", "MULTI_PART","DISSOLVE_LINES")
      
    #Create a feature layer of the FinalPatch_poly_diss
    patchDissolvedLayer = arcpy.MakeFeatureLayer_management(patchDissolvedFeature, "patchDissolvedLayer")
     
    #Convert Final Patch Raster to points to get the cell centroids
    AddMsg(timer.split() + " Converting raster patch cells to centroid points...")
    arcpy.RasterToPoint_conversion(patchOnlyRaster, patchCentroidsFeature, "VALUE")
     
    #Create a feature layer of the FinalPatch_centroids
    patchCentroidsLayer = arcpy.MakeFeatureLayer_management(patchCentroidsFeature, "patchCentroidsLayer")
    
    # Initialize custom progress indicator
    totalRUs = len(zoneAreaDict)
    mdcpLoopProgress = messages.loopProgress(totalRUs)
    
    noPatches = 0
    singlePatch = 0
   
    #Select the Reporting Unit and the intersecting polygons in FinalPatch_poly_diss
    AddMsg(timer.split() + " Analyzing MDCP by reporting unit...")
    for aZone in zoneAreaDict.keys():
        pwnCount = 0
        pwonCount = 0
        meanDist = 0
            
        if isinstance(aZone, int): # reporting unit id is an integer - convert to string for SQL expression
            squery = "%s = %s" % (delimitedField, str(aZone))
        else: # reporting unit id is a string - enclose it in single quotes for SQL expression
            squery = "%s = '%s'" % (delimitedField, str(aZone))
        
        #Create a feature layer of the single reporting unit
        aReportingUnitLayer = arcpy.MakeFeatureLayer_management(inReportingUnitFeature,"aReportingUnitLayer",squery,"#")
        
        #Select the centroids that are in the "subwatersheds_Layer"
        arcpy.SelectLayerByLocation_management(patchCentroidsLayer,"INTERSECT", aReportingUnitLayer)

        centroidCount = int(arcpy.GetCount_management(patchCentroidsLayer).getOutput(0))
        
        # Check to see if any patches exist within reporting unit
        if centroidCount == 0:
            # arcpy.AddWarning("No patches found in %s. MDCP set to -9999" % (str(aZone)))
            meanDist = -9999
            pwnCount = -9999
            pwonCount = -9999
            noPatches += 1
        
        else:
            # Select the patches that have selected centroids within them
            arcpy.SelectLayerByLocation_management(patchDissolvedLayer, "INTERSECT", patchCentroidsLayer)
            
            # Clip the selected patches to the reporting unit boundary
            # clipPolyDissFeature = arcpy.Clip_analysis(patchDissolvedLayer, aReportingUnitLayer, clipPolyDiss)
            clipPolyDissFeature = arcpy.Clip_analysis(patchDissolvedLayer, aReportingUnitLayer, "in_memory/clipPolyDiss")

            # Determine the number of patches found in this reporting unit using this script's methodology
            totalNumPatches = int(arcpy.GetCount_management(clipPolyDissFeature).getOutput(0))
            
            # Get the number of patches found in this reporting unit from the Patch Metric methodology
            pmPatches = pmResultsDict[aZone][1]
            
            if totalNumPatches == pmPatches:
                #Calculate Near Distances for each watershed
                arcpy.GenerateNearTable_analysis(clipPolyDissFeature,[clipPolyDissFeature], nearPatchTable,
                                             "","NO_LOCATION","NO_ANGLE","CLOSEST","0")
            
            else:
                # Disagreement in patch numbers possibly caused by imperfect dissolve operation. 
                # Try to correct with a second dissolve using only the clipped polygons within the reporting unit
                
                #Dissolve the polygons on Value Field to make sure each patch is represented by a single polygon.
                arcpy.Dissolve_management(clipPolyDissFeature, "in_memory/wshed_Polygons_Diss","gridcode","#", "MULTI_PART","DISSOLVE_LINES")
                 
                #Create a feature layer of the newly dissolved patches
                arcpy.MakeFeatureLayer_management("in_memory/wshed_Polygons_Diss", "FinalPatch_diss_Layer")
                
                # Re-evaluate the number of patches within the reporting unit
                totalNumPatches = int(arcpy.GetCount_management("FinalPatch_diss_Layer").getOutput(0))
                
                # Generate the Near Distance table for newly dissolved patches
                arcpy.GenerateNearTable_analysis("FinalPatch_diss_Layer",["FinalPatch_diss_Layer"], nearPatchTable,
                                                 "","NO_LOCATION","NO_ANGLE","CLOSEST","0")
                
                if totalNumPatches != pmPatches:
                    # Alert the user that the problem was not corrected
                    arcpy.AddWarning("Possible error in the number of patches foud in " + str(aZone) +" \n" + \
                                     "Calculated value for MDCP for this reporting unit is suspect")
             
            #Get total number of patches and calculate the mean distance
            try:
                # see if only one patch exists in reporting unit
                if totalNumPatches == 1:
                    # arcpy.AddWarning("Single patch in %s. MDCP = 0" % (str(aZone)))
                    pwonCount = totalNumPatches
                    meanDist = 0
                    singlePatch += 1
                     
                else: # found neighboring patches
                    rows = arcpy.SearchCursor(nearPatchTable)
                    distlist = []
                    for row in rows:
                        distance = row.getValue("NEAR_DIST")
                        distlist.append(distance)
                    del row, rows
                    
                    pwnCount = len(distlist)
                    totalDist = sum(distlist)
                    meanDist = totalDist/pwnCount
                    pwonCount = totalNumPatches - pwnCount
                 
            except:
                arcpy.AddWarning("Near Distance routine failed in %s" % (str(aZone)))
                meanDist = -9999
                pwnCount = -9999
                pwonCount = -9999
                
            finally:
                arcpy.Delete_management(nearPatchTable)

                              
        resultDict[aZone] = str(pwnCount) +  "," + str(pwonCount) +"," + str(meanDist)
        
        mdcpLoopProgress.update()
        
    if noPatches > 0:
        arcpy.AddWarning("%s reporting units contained no patches. MDCP was set to -9999 for these units." % (str(noPatches)))
    
    if singlePatch > 0:
        arcpy.AddWarning("%s reporting units contained a single patch. MDCP was set to 0 for these units." % (str(singlePatch)))
        
    arcpy.Delete_management(patchCentroidsLayer)
              
    return resultDict
