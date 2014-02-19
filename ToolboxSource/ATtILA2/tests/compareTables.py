'''
Standalone ArcToolbox Script for comparing tables

begins by comparing fields, then all table values, if no differences, then validation is successful.

Created September 2013

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
            message += "The test table was missing these fields (" + ", ".join(missingFields) + ")\n"
        if extraFields:
            message += "The test table had these extra fields (" +  ", ".join(extraFields) + ")"
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
     
    return "Table validation was successful"    

if __name__ == '__main__':
    
    refFile = arcpy.GetParameterAsText(0)
    testFile = arcpy.GetParameterAsText(1)  
    
    try:
      
        arcpy.AddMessage(compare(refFile, testFile))

    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
        
    except Exception, e:
        # get the traceback object
        import sys
        import traceback
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        
        # Concatenate information together concerning the error into a message string
        
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
    
        # Return python error messages for use in script tool
        
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)               