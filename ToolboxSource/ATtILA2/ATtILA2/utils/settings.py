""" Tasks specific to checking and retrieving settings 
"""
from ..constants import globalConstants
#from pylet import utils
from . import fields
from . import raster
import arcpy


def getOutputLinearUnits(inputDataset):
    """ Determines the output coordinate system linear units name """
    # check for output coordinate system setting in the arc environment
    if arcpy.env.outputCoordinateSystem:
        # output coordinate system is set. get it's linear units to use for area conversions
        linearUnits = arcpy.env.outputCoordinateSystem.linearUnitName
    else:
        # no output coordinate system set. get the output linear units for the input reporting unit theme.
        # warning: only use this theme if it is the first theme specified in ensuing geoprocessing tools
        desc = arcpy.Describe(inputDataset)
        linearUnits = desc.spatialReference.linearUnitName
        
    return linearUnits

def getOutputSpatialReference(inputDataset):
    """ Determines the output Spatial Reference """
    # check for output coordinate system setting in the arc environment
    if arcpy.env.outputCoordinateSystem:
        # output coordinate system is set. pass info back to program
        outSpatialReference = arcpy.env.outputCoordinateSystem
    else:
        # no output coordinate system set. get the spatial reference for the input dataset.
        desc = arcpy.Describe(inputDataset)
        outSpatialReference = desc.spatialReference
        
    return outSpatialReference


def getIdOutField(inFeature, inField):
    """ Processes the InputField. If field is an OID type, alters the output field type and name """
    inField = fields.getFieldByName(inFeature, inField)
    
    if inField.type == "OID":
        newField = arcpy.Field()
        newField.type = "Integer" 
        newField.name = inField.name+"_ID"
        newField.precision = inField.precision
        newField.scale = inField.scale
    else:
        newField = inField
        
    return (newField)


def checkGridValuesInLCC(inLandCoverGrid, lccObj, ignoreHighest=False):
    """ Checks input grid values. Warns user if values are undefined in LCC XML file. """

    gridValuesList = raster.getRasterValues(inLandCoverGrid)
    
    if ignoreHighest:
        gridValuesList.sort()
        gridValuesList = gridValuesList[:-1]
    
    undefinedValues = [aVal for aVal in gridValuesList if aVal not in lccObj.getUniqueValueIdsWithExcludes()]     
    if undefinedValues:
        arcpy.AddWarning("LCC XML file: grid value(s) %s undefined in LCC XML file - Please refer to the %s documentation regarding undefined values." % 
                        (undefinedValues, globalConstants.titleATtILA))

def checkExcludedValuesInClass(metricsBaseNameList, lccObj, lccClassesDict):
    excludedValues = lccObj.values.getExcludedValueIds()
    
    for mBaseName in metricsBaseNameList: 
        # get the grid codes for this specified class.
        try:
            # will FAIL for non-class based metrics (i.e. coefficient metrics that use all grid values) 
            classGridCodesList = lccClassesDict[mBaseName].uniqueValueIds
        except KeyError:
            pass
        else:
            excludedClassValues = [aVal for aVal in classGridCodesList if aVal in excludedValues]
            if excludedClassValues:
                arcpy.AddWarning("LCC XML file: excluded value(s) %s in class %s definition - Please refer to the %s documentation regarding excluded values." % 
                                (excludedClassValues, mBaseName.upper(), globalConstants.titleATtILA))
    
    
def checkGridCellDimensions(inLandCoverGrid):
    """ Checks input raster cell dimensions. Warns user if the x and y values are different. """
    XBand = arcpy.GetRasterProperties_management(inLandCoverGrid, "CELLSIZEX" )
    YBand = arcpy.GetRasterProperties_management(inLandCoverGrid, "CELLSIZEY")
    #Check to make sure the grid size are square if it is not generate an error
    if int(float(str(XBand))) == int(float(str(YBand))):
        pass
    else:
        arcpy.AddWarning(inLandCoverGrid+" is not square. Output calculations will be based on Processing Cell Size.")
        
        
def processUIDField(inReportingUnitFeature, reportingUnitIdField):
    """ This function checks to see whether the UID field is a text field, and if not, adds a new text field and copies
    the ID values to it, and returns the properties of the new field.  If the field is not found, it is assumed that
    the original field was an object ID field that was lost in a format conversion, and the code switches to the new
    objectID field."""
    uIDFields = arcpy.ListFields(inReportingUnitFeature,reportingUnitIdField)
    if uIDFields == []: # If the list is empty, grab the field of type OID
        uIDFields = arcpy.ListFields(inReportingUnitFeature,"",'OID')
    uIDField = uIDFields[0] # This is an arcpy field object
    if (uIDField.type != "String"): # unit IDs that are not in string format can cause problems.  
        # Create a unit ID with a string format
        reportingUnitIdField = fields.makeTextID(uIDField,inReportingUnitFeature)
        # Obtain a field object from the new field.
        uIDField = arcpy.ListFields(inReportingUnitFeature,reportingUnitIdField)[0]
    # Convert the field properties from the default ArcPy field object into inputs for the AddField object.    
    uIDField = fields.updateFieldProps(uIDField)
    return uIDField
