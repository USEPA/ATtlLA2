''' Tasks specific to setting up and restoring environments.
'''
import arcpy
from arcpy import env
from pylet import arcpyutil

from ATtILA2.constants import globalConstants

_tempEnvironment0 = ""
_tempEnvironment1 = ""
_tempEnvironment2 = ""
_tempEnvironment3 = ""
_tempEnvironment4 = ""
_tempEnvironment5 = ""


def standardSetup(snapRaster, processingCellSize, fallBackDirectory, itemDescriptionPairList=[]):
    """ Standard setup for executing metrics. """
    
    # Check out any necessary licenses
    arcpy.CheckOutExtension("spatial")
    
    # get current snap environment to restore at end of script
    _tempEnvironment0 = env.snapRaster
    _tempEnvironment1 = env.workspace
    _tempEnvironment2 = env.cellSize
    _tempEnvironment3 = env.extent
    _tempEnvironment4 = env.outputMFlag
    _tempEnvironment5 = env.outputZFlag

    env.workspace = arcpyutil.environment.getWorkspaceForIntermediates(globalConstants.scratchGDBFilename, fallBackDirectory)
    
    # set the raster environments so the rasterized polygon theme aligns with land cover grid cell boundaries
    if snapRaster:
        env.snapRaster = snapRaster        
    if processingCellSize:
        env.cellSize = processingCellSize
    
    itemTuples = []
    for itemDescriptionPair in itemDescriptionPairList:
        processed = arcpyutil.parameters.splitItemsAndStripDescriptions(itemDescriptionPair, globalConstants.descriptionDelim)
        itemTuples.append(processed)
        
        if globalConstants.intermediateName in processed:
            msg = "\nIntermediates are stored in this directory: {0}\n"
            arcpy.AddMessage(msg.format(env.workspace))    
    
    # Streams and road crossings script fails in certain circumstances when M (linear referencing dimension) is enabled.
    # Disable for the duration of the tool.
    env.outputMFlag = "Disabled"
    
    return itemTuples

    
def standardRestore():
    """ Standard restore for executing metrics. """
    
    # restore the environments
    env.snapRaster = _tempEnvironment0
    env.workspace = _tempEnvironment1
    env.cellSize = _tempEnvironment2
    env.extent = _tempEnvironment3
    env.outputMFlag = _tempEnvironment4
    env.outputZFlag = _tempEnvironment5
    
    # return the spatial analyst license    
    try:
        arcpy.CheckInExtension("spatial")
    except:
        pass
    