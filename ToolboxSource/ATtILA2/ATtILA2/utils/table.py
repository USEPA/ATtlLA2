''' Utilities specific to tables


    .. _arcpy: http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#/What_is_ArcPy/000v000000v7000000/
    .. _Table: 
'''
import os

import arcpy
#from pylet import utils
from .. import utils

from . import fields
from ATtILA2.constants import globalConstants

def createMetricOutputTable(outTable, outIdField, metricsBaseNameList, metricsFieldnameDict, metricFieldParams, 
                            qaCheckFlds=None, addAreaFldParams=None, additionalFields=None):
    """ Returns new empty table for ATtILA metric generation output with appropriate fields for selected metric
    
    **Description:**

        Creates an empty table with fields for the reporting unit id, all selected metrics with appropriate fieldname
        prefixes and suffixes (e.g. pUrb, rFor30), and any selected optional fields (e.g., LC_Overlap)
        
    **Arguments:**

        * *outTable* - file name including path for the ATtILA output table
        * *inReportingUnitFeature* - CatalogPath to the input reporting unit layer
        * *reportingUnitIdField* - fieldname for the input reporting unit id field
        * *metricsBaseNameList* - a list of metric BaseNames parsed from the 'Metrics to run' input 
                                    (e.g., [for, agt, shrb, devt] or [NITROGEN, IMPERVIOUS])
        * *metricsFieldnameDict* - a dictionary of class keys with modified field name and class name tuples as value
                        The tuple consists of the output fieldname and the modified class name
                        (e.g., "forest":("fore0_E2A7","fore0", "for":("pFor","for"))
        * *metricFieldParams* - list of parameters to generate the selected metric output field 
                        (i.e., [Fieldname_prefix, Fieldname_suffix, Field_type, Field_Precision, Field_scale])
        * *qaCheckFlds* - a list of filename parameter lists for one or more selected optional fields fieldname 
                        generation (e.g., optionalFlds = [["LC_Overlap","FLOAT",6,1]])
        * *addAreaFldParams* - a list of filename parameters for the optional Add Area Fields selection 
                        (e.g., ["_A","DOUBLE",15,0])
        
    **Returns:**

        * table (type unknown - string representation?)
        
    """
    outTablePath, outTableName = os.path.split(outTable)
        
    # need to strip the dbf extension if the outpath is a geodatabase; 
    # should control this in the validate step or with an arcpy.ValidateTableName call
    newTable = arcpy.CreateTable_management(outTablePath, outTableName)
    
    # Field objects in ArcGIS 10 service pack 0 have a type property that is incompatible with some of the AddField 
    # tool's Field Type keywords. This addresses that issue
    outIdFieldType = fields.convertFieldTypeKeyword(outIdField)
    
    arcpy.AddField_management(newTable, outIdField.name, outIdFieldType, outIdField.precision, outIdField.scale)
    
    # add metric fields to the output table.
    [arcpy.AddField_management(newTable, metricsFieldnameDict[mBaseName][0], metricFieldParams[2], metricFieldParams[3], 
                               metricFieldParams[4])for mBaseName in metricsBaseNameList]

    # add any metric specific additional fields to the output table
    if additionalFields:
        for aFldParams in additionalFields:
            [arcpy.AddField_management(newTable, aFldParams[0]+metricsFieldnameDict[mBaseName][1]+aFldParams[1], aFldParams[2], 
                                       aFldParams[3], aFldParams[4])for mBaseName in metricsBaseNameList]

    # add any optional fields to the output table
    if qaCheckFlds:
        [arcpy.AddField_management(newTable, qaFld[0], qaFld[1], qaFld[2]) for qaFld in qaCheckFlds]
        
    if addAreaFldParams:
        [arcpy.AddField_management(newTable, metricsFieldnameDict[mBaseName][0]+addAreaFldParams[0], addAreaFldParams[1], 
                                   addAreaFldParams[2], addAreaFldParams[3])for mBaseName in metricsBaseNameList]
         
    # delete the 'Field1' field if it exists in the new output table.
    fields.deleteFields(newTable, ["field1"])
    
        
    return newTable

def fullNameTruncation(outputFldName, maxFieldNameSize, outputFieldNames):
    """ Truncates the metric field name from the xxxxField class attribute to fit field name size restrictions
    
    **Description:**

        Truncates the metric field name from the xxxxField class attribute in the LCC XML document to fit field name 
        size restrictions.
        
    **Arguments:**

        * *outFldName* - unadulterated field name either supplied from the xxxxField in the LCC XML document
        * *maxFieldNameSize* - size determined by the output table type (dBASE - 10, INFO - 16, or geodatabase - 64)
        * *outputFieldNames* - a set of used field names. Used to help make new field names unique
        
    **Returns:**

        * string - the modified output field name
        * string - the class name as modified
        
    """
    n = 1
    outputFldName = outputFldName[:maxFieldNameSize] # truncate field name to maximum allowable size
    outClassName = outputFldName[:maxFieldNameSize] 
    
    # if truncated field name is already used, truncate further and add a number to the end of the name to make unique
    while outputFldName in outputFieldNames:
        truncateTo = maxFieldNameSize - len(str(n))
        outputFldName = outputFldName[:truncateTo]+str(n)
        outClassName = outputFldName
        n = n + 1
        
    return outputFldName, outClassName

def baseNameTruncation(outputFldName, metricFieldParams, maxFieldNameSize, mBaseName, outputFieldNames):
    """ Truncates the metric base name to fit field name size restrictions
    
    **Description:**

        Truncates the metric base name to fit field name size restrictions
        
    **Arguments:**

        * *outFldName* - unadulterated field name as generated by ATtILA from the class id and the field suffixes and 
                        prefixes in the metric constants
        * *metricFieldParams* - list of parameters to generate the selected metric output field 
                        (i.e., [Fieldname_prefix, Fieldname_suffix, Field_type, Field_Precision, Field_scale])
        * *maxFieldNameSize* - size determined by the output table type (dBASE - 10, INFO - 16, or geodatabase - 64)
        * *mBaseName* - the class id from the LCC document (e.g., "for", "nat", "shrb", "agt")
        * *outputFieldNames* - a set of used field names. Used to help make new field names unique
        
    **Returns:**

        * string - the modified output field name
        * string - the class name as modified
        
    """
    prefixLen = len(metricFieldParams[0])
    suffixLen = len(metricFieldParams[1])
    maxBaseSize = maxFieldNameSize - prefixLen - suffixLen
    
    n = 1
    outputFldName = metricFieldParams[0] + mBaseName[:maxBaseSize] + metricFieldParams[1] # truncate field name to maximum allowable size 
    outClassName = mBaseName[:maxBaseSize]
    
    # if truncated field name is already used, truncate further and add a number to the end of the name to make unique
    while outputFldName in outputFieldNames:
        # shorten the field name and increment it
        truncateTo = maxBaseSize - len(str(n))
        outputFldName = metricFieldParams[0]+mBaseName[:truncateTo]+str(n)+metricFieldParams[1]
        outClassName = mBaseName[:truncateTo]+str(n)
        n = n + 1
   
    return outputFldName, outClassName

def tableWriterByClass(outTable, metricsBaseNameList, optionalGroupsList, metricConst, lccObj, outIdField, additionalFields=None):
    """ Processes tool dialog parameters and options for output table generation. Class metrics option.
        
    **Description:**

        Processes the input and output parameters and selected options from the ATtILA tool dialog for output table
        generation. After processing the data, this function calls the CreateMetricTableOutput function which
        creates an empty table with fields for the reporting unit id, all selected metrics with appropriate fieldname
        prefixes and suffixes (e.g. pUrb, rFor30), and any selected optional fields (e.g., LC_Overlap). 
        
        This function is used when the selected metrics are represented by the class nodes in the .lcc file
        
        Returns the created output table and a dictionary of the selected lcc classes and their generated fieldnames
        
    **Arguments:**

        * *outTable* - file name including path for the ATtILA output table

        * *metricsBaseNameList* - a list of metric BaseNames parsed from the 'Metrics to run' input 
                        (e.g., [for, agt, shrb, devt] or [NITROGEN, IMPERVIOUS])

        * *optionalGroupsList* - list of the selected options parsed from the 'Select options' input
                        (e.g., ["QAFIELDS", "AREAFIELDS", "INTERMEDIATES"])
        * *metricConst* - a class object with the variable constants for a particular metric family as attributes 
        * *lccObj* - a class object of the selected land cover classification file 
        * *outIdField* - the output id field. Generally a clone of the input id field except where the fieldtype = "OID"
        * *additionalFields* - a list of lists containing field parameters for additional metric fields to be generated
                        (e.g., [[CoreField],[EdgeField]] in the CAEM tool)
        
    **Returns:**

        * table (type unknown - string representation?)
        * dict - a dictionary of BaseName keys with field name values (e.g., "unat":"UINDEX", "for":"pFor", 
                        "NITROGEN":"N_Pload")
        
    """

    maxFieldNameSize = fields.getFieldNameSizeLimit(outTable) 
    metricFieldParams = metricConst.fieldParameters
    metricsFieldnameDict = {} # create a dictionary of ClassName keys with user supplied field names values
    outputFieldNames = set() # use this set to help make field names unique   
    # Parameterize optional QA fields, e.g., optionalFlds = [["LC_Overlap","FLOAT",6,1]]
    if globalConstants.qaCheckName in optionalGroupsList:
        qaCheckFlds = metricConst.qaCheckFieldParameters
    else:
        qaCheckFlds = None
        
    if additionalFields:
        # get the combined length of any provided field name prefix or suffix of the additional metric names
        psLengths = [len(aFldParams[0]) + len(aFldParams[1])for aFldParams in metricConst.additionalFields]
        # get the combined length of any provided field name prefix or suffix of the primary metric name
        prefixsuffixLen = len(metricFieldParams[0]) + len(metricFieldParams[1])
        # find the maximum length of all the prefix/suffix pairs  
        diff = max(psLengths) - prefixsuffixLen
        # determine the allowance needed in the field name for the prefixes and suffixes
        reduceBy = max([0, diff])
        # reduce the maximum field name size by the area needed by the prefixes and suffixes
        maxFieldNameSize = maxFieldNameSize - reduceBy
        

    # get the field name override key
    fieldOverrideKey = metricConst.fieldOverrideKey
    # get dictionary of LCC class attributes
    lccClassesDict = lccObj.classes
    # get the optional area field parameters if needed
    if globalConstants.metricAddName in optionalGroupsList:
        addAreaFldParams = globalConstants.areaFieldParameters
        maxFieldNameSize = maxFieldNameSize - len(addAreaFldParams[0])
    else:
        addAreaFldParams = None
    
    for mBaseName in metricsBaseNameList:
        outputFName = lccClassesDict[mBaseName].attributes.get(fieldOverrideKey,None)
        
        if outputFName: # a field name override exists
            outClassName = outputFName
            # see if the provided field name is too long for the output table type
            if len(outputFName) > maxFieldNameSize:
                # keep track of the originally provided field name
                defaultFieldName = outputFName 
                # truncate field name to maximum allowable size
                outputFName, outClassName = fullNameTruncation(outputFName, maxFieldNameSize, outputFieldNames)
                # alert the user to the new field name
                arcpy.AddWarning(globalConstants.metricNameTooLong.format(defaultFieldName, outputFName))
                
        else: # generate output field name
            outputFName = metricFieldParams[0] + mBaseName + metricFieldParams[1]
            outClassName = mBaseName
            # see if the provided field name is too long for the output table type
            if len(outputFName) > maxFieldNameSize:
                # keep track of the originally generated field name
                defaultFieldName = outputFName
                # truncate field name to maximum allowable size by shrinking the metrics base (class) name
                outputFName, outClassName = baseNameTruncation(outputFName, metricFieldParams, maxFieldNameSize, mBaseName, outputFieldNames)
                # alert the user to the new field name    
                arcpy.AddWarning(globalConstants.metricNameTooLong.format(defaultFieldName, outputFName))
        
        # keep track of output field names
        outputFieldNames.add(outputFName)
        # add output field name to dictionary
        metricsFieldnameDict[mBaseName] = [outputFName, outClassName]
            
    # create the specified output table
    newTable = createMetricOutputTable(outTable,outIdField,metricsBaseNameList,metricsFieldnameDict,metricFieldParams, 
                                       qaCheckFlds,addAreaFldParams,additionalFields)
    
    return newTable, metricsFieldnameDict


def tableWriterByCoefficient(outTable, metricsBaseNameList, optionalGroupsList, metricConst, lccObj, outIdField):
    """ Processes tool dialog parameters and options for output table generation. Coefficient metrics option.
        
    **Description:**

        Processes the input and output parameters and selected options from the ATtILA tool dialog for output table
        generation. After processing the data, this function calls the CreateMetricTableOutput function which
        creates an empty table with fields for the reporting unit id, all selected metrics with appropriate fieldname
        prefixes and suffixes (e.g. pUrb, rFor30), and any selected optional fields (e.g., LC_Overlap). 
        
        This function is used when the selected metrics are represented by the coefficient node in the .lcc file
        
        Returns the created output table and a dictionary of the selected lcc coefficients and their generated fieldnames
        
    **Arguments:**

        * *outTable* - file name including path for the ATtILA output table

        * *metricsBaseNameList* - a list of metric BaseNames parsed from the 'Metrics to run' input 
                        (e.g., [for, agt, shrb, devt] or [NITROGEN, IMPERVIOUS])

        * *optionalGroupsList* - list of the selected options parsed from the 'Select options' input
                        (e.g., ["QAFIELDS", "AREAFIELDS", "INTERMEDIATES"])
        * *metricConst* - a class object with the variable constants for a particular metric family as attributes 
        * *lccObj* - a class object of the selected land cover classification file 
        * *outIdField* - the output id field. Generally a clone of the input id field except where the fieldtype = "OID"
        
    **Returns:**

        * table (type unknown - string representation?)
        * dict - a dictionary of BaseName keys with field name values (e.g., "unat":"UINDEX", "for":"pFor", 
                        "NITROGEN":"N_Pload")
        
    """
    
    #maxFieldNameSize = fields.getFieldNameSizeLimit(outTable)

    maxFieldNameSize = fields.getFieldNameSizeLimit(outTable)
    metricFieldParams = metricConst.fieldParameters
    metricsFieldnameDict = {} # create a dictionary of ClassName keys with user supplied field names values
    outputFieldNames = set() # use this set to help make field names unique       
    # Parameterize optional QA fields, e.g., optionalFlds = [["LC_Overlap","FLOAT",6,1]]
    if globalConstants.qaCheckName in optionalGroupsList:
        qaCheckFields = metricConst.qaCheckFieldParameters
    else:
        qaCheckFields = None
    
    for mBaseName in metricsBaseNameList:
        outputFName = lccObj.coefficients[mBaseName].fieldName
        outClassName = outputFName
        
        # see if the provided field name is too long for the output table type
        if len(outputFName) > maxFieldNameSize:
            defaultFieldName = outputFName # keep track of the originally provided field name
            # truncate field name to maximum allowable size
            outputFName, outClassName = fullNameTruncation(outputFName, maxFieldNameSize, outputFieldNames)
            # alert the user to the new field name    
            arcpy.AddWarning(globalConstants.metricNameTooLong.format(defaultFieldName, outputFName))
            
        # keep track of output field names    
        outputFieldNames.add(outputFName)
        # add output field name to dictionary
        metricsFieldnameDict[mBaseName] = [outputFName, outClassName]
              
    # create the specified output table
    newTable = createMetricOutputTable(outTable,outIdField,metricsBaseNameList,metricsFieldnameDict, 
                                                           metricFieldParams, qaCheckFields)
    
    return newTable, metricsFieldnameDict


def tableWriterNoLcc(outTable, metricsBaseNameList, optionalGroupsList, metricConst, outIdField):
    """ Processes tool dialog parameters and options for output table generation. Non LCC metrics option.
        
    **Description:**

        Processes the input and output parameters and selected options from the ATtILA tool dialog for output table
        generation. After processing the data, this function calls the CreateMetricTableOutput function which
        creates an empty table with fields for the reporting unit id, all selected metrics with appropriate fieldname
        prefixes and suffixes (e.g. pUrb, rFor30), and any selected optional fields (e.g., LC_Overlap). 
        
        This function is used when the selected metrics are independent of an .lcc file
        
        Returns the created output table and a dictionary of the selected metrics and their generated fieldnames
        
    **Arguments:**

        * *outTable* - file name including path for the ATtILA output table

        * *metricsBaseNameList* - a list of metric BaseNames parsed from the 'Metrics to run' input 
                        (e.g., [for, agt, shrb, devt] or [NITROGEN, IMPERVIOUS])

        * *optionalGroupsList* - list of the selected options parsed from the 'Select options' input
                        (e.g., ["QAFIELDS", "AREAFIELDS", "INTERMEDIATES"])
        * *metricConst* - a class object with the variable constants for a particular metric family as attributes 
        * *outIdField* - the output id field. Generally a clone of the input id field except where the fieldtype = "OID"
        
    **Returns:**

        * table (type unknown - string representation?)
        * dict - a dictionary of BaseName keys with field name values (e.g., "unat":"UINDEX", "for":"pFor", 
                        "NITROGEN":"N_Pload")
        
    """

    maxFieldNameSize = fields.getFieldNameSizeLimit(outTable) 
    metricFieldParams = metricConst.fieldParameters
    metricsFieldnameDict = {} # create a dictionary of ClassName keys with user supplied field names values
    outputFieldNames = set() # use this set to help make field names unique 
    # Parameterize optional QA fields, e.g., optionalFlds = [["LC_Overlap","FLOAT",6,1]]
    if globalConstants.qaCheckName in optionalGroupsList:
        qaCheckFlds = metricConst.qaCheckFieldParameters
    else:
        qaCheckFlds = None
                
    if globalConstants.metricAddName in optionalGroupsList:
        addAreaFldParams = globalConstants.areaFieldParameters
        maxFieldNameSize = maxFieldNameSize - len(addAreaFldParams[0])
    else:
        addAreaFldParams = None  
    
    for mBaseName in metricsBaseNameList:
        outputFName = metricFieldParams[0] + mBaseName + metricFieldParams[1]
        outClassName = outputFName
        
        # see if the provided field name is too long for the output table type
        if len(outputFName) > maxFieldNameSize:
            # keep track of the originally generated field name
            defaultFieldName = outputFName
            # truncate field name to maximum allowable size by shrinking the metrics base (class) name
            outputFName, outClassName = baseNameTruncation(outputFName, metricFieldParams, maxFieldNameSize, mBaseName, outputFieldNames)
            # alert the user to the new field name    
            arcpy.AddWarning(globalConstants.metricNameTooLong.format(defaultFieldName, outputFName))
            
        # keep track of output field names
        outputFieldNames.add(outputFName)
        # add output field name to dictionary
        metricsFieldnameDict[mBaseName] = [outputFName, outClassName]
                
    # create the specified output table
    newTable = createMetricOutputTable(outTable,outIdField,metricsBaseNameList,metricsFieldnameDict, 
                                                           metricFieldParams, qaCheckFlds, addAreaFldParams)
    
    return newTable, metricsFieldnameDict



def transferField(fromTable,toTable,fromFields,toFields,joinField,classField="#",classValues=[]):
    '''This function transfers a series of fields from one table to another, and, if a class field is specified, pivots
       the metric fields for those class values into a new field for each class.
    **Description:**
        For each field specified, this function transfers the values from the source table to the destination table. 
        If no class field is specified, this is accomplished by the addJoinCalculateField function - a simple join based
        on reporting unit ID
        If a class field is specified, this function uses a search cursor and update cursor to pivot the metrics to 
        an output table with one row per reporting unit and a metric field for each class.
    **Arguments:**
        * *fromTable* - the source table
        * *toTable* - the destination table
        * *fromFields* - a python list of source fieldnames
        * *toFields* - a python list of desired ouptut fieldnames in the same order as the fromFields list
        * *joinField* - the field common to both tables on which to base the join.  it is assumed that in this context 
                        the fields have the same name in both tables - if this is not a safe assumption, this function 
                        may need to be modified in the future.
        * *classField* - optional field with class values that will be pivoted to output fields
        * *classValues* - a python list of unique values from the classField
    '''
    # Create a zipped list of fields to be transferred - packing and unpacking by using tuples is a little more elegant
    transferFields = zip(fromFields,toFields)
    # Start with the simple case, where no class field is specified.
    if not classField: 
        # Iterate through the field list and run the addJoinCalculateField function
        for (fromField,toField) in transferFields:
            addJoinCalculateField(fromTable,toTable,fromField,toField,joinField)
    else:
        # Now the tougher case - pivoting class values.
        # Create a dictionary that will link class values to tuples matching source fieldnames and valid destination fieldnames
        transferClassFields = {}
        # Sort the class values just so the output table fields are in a less random order
        classValues.sort()
        # For each combo of source and destination fields in the transferFields list
        for (fromField,toField) in transferFields:
            # For each class value in the class values list
            for classValue in classValues:
                # if the dictionary doesn't already have an element with this value as the key 
                if not transferClassFields.has_key(classValue):
                    # Add a new empty list to the dictionary with this classValue as key
                    transferClassFields[classValue] = []
                # Obtain a valid output fieldname that combines the desired output fieldname with this class value
                classToField = getClassFieldName(toField,classValue,toTable)
                # Save this combination of source and destination fieldnames to the list keyed to this class value in the dictionary
                transferClassFields[classValue].append((fromField,classToField))
                # Get the properties of the source field
                fromFieldObj = arcpy.ListFields(fromTable,fromField)[0]
                # Add the new field to the output table with the appropriate properties and the valid name
                arcpy.AddField_management(toTable,classToField,fromFieldObj.type,fromFieldObj.precision,fromFieldObj.scale,
                          fromFieldObj.length,fromFieldObj.aliasName,fromFieldObj.isNullable,fromFieldObj.required,
                          fromFieldObj.domain) 
        # In preparation for the upcoming whereclause, add the appropriate delimiters to the join field
        joinFieldDelim = arcpy.AddFieldDelimiters(fromTable,joinField)
        # In preparation for the upcoming whereclause, set up the appropriate delimiter function for the join value
        delimitJoinValues = fields.valueDelimiter(arcpy.ListFields(fromTable,joinField)[0].type)
        # Initialize an update cursor on the output table
        updateCursor = arcpy.UpdateCursor(toTable)
        # For each row in the output table (each reporting unit)
        for updateRow in updateCursor:
            # Grab the reporting unit ID
            joinID = updateRow.getValue(joinField)
            # Create a whereclause for selecting the corresponding rows in the source table
            whereClause = joinFieldDelim + " = " + delimitJoinValues(joinID)
            # Initialize a search cursor on the source table for this reporting unit
            fetchCursor = arcpy.SearchCursor(fromTable,whereClause)
            # For each row in the source table (which should correspond to each class in this reporting unit)
            for fetchRow in fetchCursor:
                # obtain the class value that will link us to the correct output field
                classValue = fetchRow.getValue(classField)
                # for each desired output metric (which we have saved in a list of tuples with the input and valid output fieldnames)
                for (fromField,toField) in transferClassFields[classValue]:
                    # Set the output field value equal to the correct source value
                    updateRow.setValue(toField,fetchRow.getValue(fromField))
                # Clean up our row element for memory management and to remove locks
                del fetchRow
            # Clean up our row element for memory management and to remove locks
            del fetchCursor
            # Persist all of the updates for this row.
            updateCursor.updateRow(updateRow)
            # Clean up our row element for memory management and to remove locks
            del updateRow
        # Clean up our row element for memory management and to remove locks
        del updateCursor
            

def addJoinCalculateField(fromTable,toTable,fromField,toField,joinField):
    '''This function transfers one field to another via a simple JoinField operation, but also allows for a field to be 
       renamed as part of the transfer.
    **Description:**
        The arcpy.JoinField function permanently joins a specified field to an output table, but does not allow that
        field to be renamed.  This function facilitates that renaming by first adding and populating the desired field
        to the source table, then joining the renamed field to the output table, then cleaning up the renamed field
        from the source table.  
    **Arguments:**
        * *fromTable* - the source table
        * *toTable* - the destination table
        * *fromField* - the source fieldname
        * *toField* - the desired output fieldname
        * *joinField* - the field common to both tables on which to base the join.  it is assumed that in this context 
                        the fields have the same name in both tables - if this is not a safe assumption, this function 
                        may need to be modified in the future.
    '''
    # If renaming is required, add a temp field to the fromtable with the new name
    if fromField != toField:
        # Get the properties of the from field for transfer
        fromField = arcpy.ListFields(fromTable,fromField)[0]
        # Add the new field with the new name
        arcpy.AddField_management(fromTable,toField,fromField.type,fromField.precision,fromField.scale,
                              fromField.length,fromField.aliasName,fromField.isNullable,fromField.required,
                              fromField.domain)        
        # Calculate the field
        arcpy.CalculateField_management(fromTable,toField,'!'+ fromField.name +'!',"PYTHON")
    # Perform the joinfield
    """ If the joinField field is not found in toTable, it is assumed that
    the joinField was an object ID field that was lost in a format conversion"""
    uIDFields = arcpy.ListFields(toTable,joinField)
    if uIDFields == []: # If the list is empty, grab the field of type OID
        uIDFields = arcpy.ListFields(toTable,"",'OID')
    uIDField = uIDFields[0] # This is an arcpy field object
    joinField_In_toTable = uIDField.name    
    #arcpy.JoinField_management(toTable,joinField,fromTable,joinField,toField)
    arcpy.JoinField_management(toTable,joinField_In_toTable,fromTable,joinField,toField)
    # If we added a temp field
    if fromField != toField:
        arcpy.DeleteField_management(fromTable,toField)
    
def getClassFieldName(fieldName,classVal,table):
    '''This function generates a valid fieldname based on the combination of a desired fieldname and a class value
    **Description:**
        The expectation for the ATtILA output table is one field per metric per class value, if a class is specified.
        A simple concatenation of metric fieldname and class value has the potential to be trimmed, depending on the
        limits of the output table format (i.e. 10 characters for dbf files).  This function thus concatenates the
        desired fieldname with the specified class value, tries the arcpy field validation, and if the concatenated
        fieldname gets shortened, trims the desired fieldname by the appropriate amount so that the class value is 
        always the final characters of the fieldname string.  
    **Arguments:**
        * *fieldName* - the desired metric fieldname to which the class value will be appended
        * *classVal* - the class value 
        * *table* - the table to which the field will be added 
    **Returns:**
        * *validFieldName* - validated fieldname 
    '''
    # Ensure we have a string value for the class
    classVal = str(classVal)
    # Build a test fieldname
    testFieldName = fieldName + classVal
    # Run the test fieldname through ESRI's fieldname validator
    validFieldName = arcpy.ValidateFieldName(testFieldName, arcpy.Describe(table).path)
    # if the validator shortened the field
    if len(testFieldName)>len(validFieldName):
        # figure out how much needs to be trimmed
        trim = len(validFieldName) - len(testFieldName)
        # Trim this from the intended fieldname, so the class value isn't lost
        testFieldName = fieldName[:trim] + classVal
        # Revalidate - to ensure there aren't duplicate fields.
        validFieldName = arcpy.ValidateFieldName(testFieldName, table)
    return validFieldName
