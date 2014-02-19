'''
Output validation module
begins by comparing fields, then all table values, if no differences, then validation is successful.

Created July 2012

@author: thultgren
'''

import arcpy

def compare(refFile, testFile):
    refDesc = arcpy.Describe(refFile)
    testDesc = arcpy.Describe(testFile)
    refFieldNames = [x.name for x in refDesc.fields]
    testFieldNames = [x.name for x in testDesc.fields]
    extraFields = [x for x in testFieldNames if x not in refFieldNames]
    missingFields = [y for y in refFieldNames if y not in testFieldNames]
    # Test to see if all the fields match
    if missingFields or extraFields:
        message = "Validation failed, "
        if missingFields: 
            message += "Output was missing these fields (" + ", ".join(missingFields) + ")\n"
        if extraFields:
            message += "Output had these extra fields (" +  ", ".join(extraFields) + ")"
        return message
    else:
        refCur = arcpy.SearchCursor(refFile)
        testCur = arcpy.SearchCursor(testFile)
        # Start testing table values, break on first difference
        for refRow in refCur:
            testRow = testCur.next()
            for field in refDesc.fields:
                if not refRow.getValue(field.name) == testRow.getValue(field.name):
                    return "Validation failed, an error was found in row: " + \
                        str(refRow.getValue(refDesc.OIDFieldName)) + ", column: " + field.name + \
                        "Expected: " + str(refRow.getValue(field.name)) + ", actual: " + \
                        str(testRow.getValue(field.name))
     
    return "Validation was successful"                   