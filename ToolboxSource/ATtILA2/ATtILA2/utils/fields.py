""" This module contains utilities for tabular fields accessed using `arcpy`_, a Python package associated with ArcGIS. 

    .. _arcpy: http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#/What_is_ArcPy/000v000000v7000000/
    .. _FieldMappings: http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#/FieldMappings/000v0000008q000000/
    .. _arcpy.DeleteField_management: http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#//00170000004n000000
    .. _iterable: http://docs.python.org/glossary.html#term-iterable
"""

import os
import arcpy



def getSortedFieldMappings(tablePath, putTheseFirst):
    """ Get an alphabetically sorted arcpy `FieldMappings`_ object for the given table, with the specified fields up 
    front.

    **Description:**

        Given a path to a table or feature class, an arcpy `FieldMappings`_ object is returned with fields sorted
        alphabetically.  Fields specified in putTheseFirst list are put at the start in the same order specified.
        
        Example of usage::
        
            fieldMappings = fields.getSortedFieldMappings(inTablePath, putTheseFirst)
            arcpy.TableToTable_conversion(inTablePath, outWorkspace, outName, None, fieldMappings)        
        
    **Arguments:**
        
        * *tablePath* - path to a table or feature class with fields you wish to sort  
        * *putTheseFirst* - list of field names to put first; order of fields is matched  
        
        
    **Returns:** 
        
        * arcpy `FieldMappings`_ object 


        
    """
    
    fieldMappings = arcpy.FieldMappings()
    fieldMappings.addTable(tablePath)

    fieldMaps = [fieldMappings.getFieldMap(fieldIndex) for fieldIndex in range(0,fieldMappings.fieldCount)]
    fieldMaps.sort(key=lambda fmap: fmap.getInputFieldName(0).lower())

    if putTheseFirst:
        # Move those matching putTheseFirst to front of list
        for fieldMapsIndex, fieldMap in enumerate(fieldMaps):
            fieldName = fieldMap.getInputFieldName(0).lower()
            if fieldName in putTheseFirst:
                fieldMaps.insert(0, fieldMaps.pop(fieldMapsIndex))
                
        # Make order of those moved to front of list match putTheseFirst
        for putTheseFirstIndex, inFieldName in enumerate(putTheseFirst):
            for fieldMapsIndex, fieldMap in enumerate(fieldMaps):
                fieldName = fieldMap.getInputFieldName(0).lower()
                if inFieldName == fieldName:
                    if putTheseFirstIndex != fieldMapsIndex:
                        fieldMaps.insert(putTheseFirstIndex, fieldMaps.pop(fieldMapsIndex))
                    break

    fieldMappings.removeAll()
    
    # Assemble each fieldMap into FieldMappings object
    for fieldMap in fieldMaps:
        fieldMappings.addFieldMap(fieldMap)

    return fieldMappings


def getFieldNameSizeLimit(outTablePath, fixes=None):
    """ Return the maximum size of output field names based on the output location of the table being created.

    **Description:**
        
        The value returned is based on the output table's type.  The table's type is determined by parsing the full 
        path to the table and first looking at the suffix for the workspace and then for the file.  The values are 
        returned based on these rules:
        
        * 64  -  file and personal geodatabases(folder with .mdb or .gdb extension)
        * 10  -  dBASE tables (file with .dbf or .shp extension)
        * 16  -  INFO tables (default if previous identifiers were not found
        
        The length of *fixes* will be subtracted from this number.  The *fixes* argument can be a single string or
        a list of strings that might be added to a root field name for which you need the length.
        
        SDE databases are not unsupported.
        
    **Arguments:**
        
        * *outTablePath* - Full path to output table
        * *fixes* - A string or list of strings
        
    **Returns:** 
        
        * integer

    """

        
    outTablePath, outTableName = os.path.split(outTablePath)
    
    folderExtension = outTablePath[-3:].lower()
    fileExtension = outTableName[-3:].lower()
    
    if  folderExtension == "gdb" :
        maxFieldNameSize = 64 # ESRI maximum for File Geodatabases
    elif folderExtension == "mdb":
        maxFieldNameSize = 64 # ESRI maximum for Personal Geodatabases
    elif fileExtension == "dbf" or fileExtension == "shp":
        maxFieldNameSize = 10 # maximum for dBASE tables
    else:
        maxFieldNameSize = 16 # maximum for INFO tables
    
    extraLength = 0
    if fixes:
        #fixes is a list
        if isinstance(fixes, list):
            extraLength = sum((len(fix) for fix in fixes ))
        #fixes is a string
        else:
            extraLength = len(fixes)
        
    return maxFieldNameSize - extraLength


def deleteFields(inTable, fieldNames):
    """ In the given input table, delete all fields with the specified names.
    
    **Description:**
        

        The `arcpy.DeleteField_management`_ tool is used to delete each field name from the input table.  The field 
        name is not case sensitive.
        
    **Arguments:**
        
        * *inTable* - Object or string indicating the input table with fields that need to be deleted
        * *fieldNames* - An `iterable`_ containing field names to delete
        
    **Returns:** 
        
        * None
        
    """ 
    for fieldName in fieldNames:
        arcpy.DeleteField_management(inTable, fieldName)
        


def getFieldByName(inTable, fieldName):
    """ In the given table, return the arcpy `Field`_ object with the given name.

    **Description:**
        
        Fields in the input table are searched using arcpy.ListFields.  Names are converted to lowercase for the 
        comparison.
        
    **Arguments:**
        
        * *inTable* - input table or feature class to retrieve field object from
        * *fieldName* - the name of the field
        
    **Returns:** 
        
        * arcpy `Field`_ object 
        
        .. _Field: http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#/Field/000v00000071000000/
        
    """    
    
    idField = None
    
    for field in arcpy.ListFields(inTable):
        if str(field.name).lower() == str(fieldName).lower():
            idField = field
            break
        
    return idField

def convertFieldTypeKeyword(inField):
    """ Field objects in ArcGIS 10 SP 0 have a type property that is incompatible with some of the AddField tool's Field Type keywords.
    
    **Description:**
    
        Field objects in ArcGIS 10 service pack 0 have a type property that is incompatible with some of the AddField 
        tool's Field Type keywords. This addresses that issue by converting the field.type return string to the acceptable
        Field Type keyword.
        
        * String  ->  TEXT
        * Integer  ->  LONG
        * Smallinteger  ->  SHORT
        
    **Arguments:**
    
        * *inField* - input field to check/convert field type string from
        
    **Returns:**
    
        * outFieldType string
        
    """
    
    outFieldType = inField.type.lower()
    
    if outFieldType == "string":
        outFieldType = "TEXT"
    elif outFieldType == "integer":
        outFieldType = "LONG"
    elif outFieldType == "smallinteger":
        outFieldType = "SHORT"
        
    return outFieldType


def updateFieldProps(field):
    ''' This function translates the properties returned by the field describe function into the 
        parameters expected by the AddField tool
        
    ** Description: **
        
        Field objects in ArcPy have certain properties (type, nullable, and required) that don't match the expected
        input parameters for the Add Field tool.  This tool maps properties to expected inputs.
    
    **Arguments:**
    
        * *field* - input arcpy field object
    
    **Returns:**
    
        * field - modified field object that can be used as input to Add Field tool.
        
    '''
    
    typeDictionary = {"SmallInteger":"SHORT","Integer":"LONG","Single":"FLOAT","Double":"DOUBLE","String":"TEXT",
                      "Date":"DATE","OID":"GUID","Blob":"BLOB"}
    field.type = typeDictionary[field.type]
    nullDictionary = {True:"NULLABLE",False:"NON_NULLABLE"}
    field.isNullable = nullDictionary[field.isNullable]
    requiredDictionary = {True:"REQUIRED",False:"NON_REQUIRED"}
    field.required = requiredDictionary[field.required]
    return field

def makeTextID(field,table):
    ''' This function creates a copy of an existing field with the String format.
        
    ** Description: **
        
        Certain types of fields cause problems when performing joins, and Strings are generally the most reliable.
        This function creates a new field with string format of length 30 and copies all data from the problem field.
    
    **Arguments:**
    
        * *field* - input arcpy field object
        * *table* - name with full path of input table to be modified)
    
    **Returns:**
    
        * *textFieldName* - validated field name of added field.
        
    '''
    # Obtain valid fieldname
    textFieldName = arcpy.ValidateFieldName("txt" + field.name, table)
    # Test for Schema Lock
    if arcpy.TestSchemaLock(table):
        # Add the output text field
        arcpy.AddField_management(table,textFieldName,"TEXT","#","#","30") 
    else: 
        arcpy.AddMessage("Unable to acquire the necessary schema lock to add the new field")
    # Calculate the field values
    arcpy.CalculateField_management(table, textFieldName,'!'+ field.name +'!',"PYTHON")
    # Since this field will be used in joins, index the field.
    arcpy.AddIndex_management(table, textFieldName, "idIDX", "UNIQUE")
    return textFieldName

def valueDelimiter(fieldType):
    '''Utility for adding the appropriate delimiter to a value in a whereclause.
    ** Description: **
        
        If the field is a string type, the values must be enclosed in single quotes.  If the field is not a string,
        the value itself needs to be converted to a python string to be safely concatenated.
    
    **Arguments:**
    
        * *fieldType* - arcpy FieldType value 
    
    **Returns:**
    
        * *delimitValue* - a function that will either enclose a string in quotes or convert to python string object.
    '''
    if fieldType == 'String':
        # If the field type is string, enclose the value in single quotes
        def delimitValue(value):
            if value: # is not a NoneType
                value = value.replace("'", "''") # handles the condition where an apostrophe is found in the value string
                return "'" + value + "'"
            else: # value is a NoneType
                return "''"
    else:
        # Otherwise the string is numeric, just convert it to a Python string type for concatenation with no quotes.
        def delimitValue(value):
            return str(value)
    return delimitValue

def getUniqueValues(table,field):
    '''Utility for creating a python list of unique values from a specific field in a table.
    ** Description: **
        
        This function will open a search cursor on the field in the specified table and iterate through all the rows
        in the table and collect all unique field values in a python list object.
    
    **Arguments:**
    
        * *table* - any dataset with a table.
        * *field* - the field name from which to collect unique values    
    **Returns:**
    
        * *valueList* - a python list of unique values
    '''
    valueList = []
    rows = arcpy.SearchCursor(table,"","",field)
    for row in rows:
        value = row.getValue(field)
        if value not in valueList:
            valueList.append(value)
        del row
    del rows
    return valueList

def checkForDuplicateValues(inFeatures, inField):
    """Returns True if duplicate values are found in input field
    
    **Description:**

    **Arguments:**
        * *inFeatures* - feature class containing the field to be checked
        * *inField* - input field to check for duplicate values
        
    **Returns:**
        * *boolean* - True if duplicates are found
    """
    try:
        # Get a count of the number of reporting units to give an accurate progress estimate.
        n = int(arcpy.GetCount_management(inFeatures).getOutput(0))
        uniqueValues = set()
        Rows = arcpy.SearchCursor(inFeatures,"","",inField)
        # For each reporting unit:
        for row in Rows:
            # Get the reporting unit ID
            uniqueValues.add(row.getValue(inField))

        if n > len(uniqueValues):
            return True
    
    finally:
        try:
            # Clean up the search cursor object
            del Rows
            
        except:
            pass