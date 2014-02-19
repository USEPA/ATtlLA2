''' Tasks specific to error handling
'''

from ATtILA2.constants import errorConstants

import arcpy
import sys
import traceback

class attilaException(Exception):
    """ Custom exception """

def getErrorComments(e):
    """"""
    errorMsg = str(e)
    
    for lookup, response in errorConstants.errorLookup.iteritems():
        if lookup in errorMsg:
            return response

    return errorConstants.errorUnknown


def standardErrorHandling(exception):
    
    errorComments = ''
    
    if isinstance(exception, attilaException):
        
        arcpy.AddError()
        errorComments = str(exception) 
    else:
        errorComments = getErrorComments(exception)
    
        
    # get the traceback object
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[-1].strip()
    
    # Concatenate information together concerning the error into a message string
    if errorComments:
        msg = errorConstants.errorCommentPrefix + errorComments + "\n" + errorConstants.errorDetailsPrefix + tbinfo
    else:
        msg = errorConstants.errorDetailsPrefix + tbinfo
        
    # Return python error messages for use in script tool
    arcpy.AddError(msg)
    
    # From ESRI's example, maybe this will return scripting errors?
    if not arcpy.GetMessages(2) == "":
        arcpy.AddError(arcpy.GetMessages(2))
    
    print msg  # To ensure message is printed to command line if run as standalone.
    raise(exception)
