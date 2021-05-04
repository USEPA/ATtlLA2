''' Interface for running specific metrics

'''
import os
import arcpy
import time
from . import errors
from . import setupAndRestore
#from pylet import lcc
from .utils import lcc
from .utils import polygons
from .utils import fields
from .utils import table
from .utils import calculate
from .utils import settings
from .utils import files
from .utils import vector
from .utils import environment
from .utils import parameters
from .utils import raster
from .utils import conversion
from .utils.messages import AddMsg
from .datetimeutil import DateTimer
from .constants import metricConstants
from .constants import globalConstants
from .constants import errorConstants
from . import utils
from .utils.tabarea import TabulateAreaTable
from arcpy.sa.Functions import ZonalStatisticsAsTable
#from sympy.logic.boolalg import false

class metricCalc:
    """ This class contains the basic steps to perform a land cover metric calculation.

    **Description:**

        The long metric calculation process only varies slightly from metric to metric.  By embedding the series of
        calculation steps and parameters in a class object, we can make any step that might need to be altered for
        a particular calculation into a separate function that can be overridden.  This cuts down on duplicate code and
        eases maintenance.  Each metric calculation need only instantiate a subclass of metricCalc, override the
        necessary functions, and then run the main 'run' function - all other code will be inherited from the main
        class.  If a new step needs to be pulled out of the main 'run' function so that it can be altered, it can be
        done without affecting any existing code.

    """

    # Initialization
    def __init__(self, inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, lccFilePath,
              metricsToRun, outTable, processingCellSize, snapRaster, optionalFieldGroups, metricConst, ignoreHighest=False):
        self.timer = DateTimer()
        AddMsg(self.timer.start() + " Setting up environment variables")
        
        # Run the setup
        self.metricsBaseNameList, self.optionalGroupsList = setupAndRestore.standardSetup(snapRaster, processingCellSize,
                                                                                 os.path.dirname(outTable),
                                                                                 [metricsToRun,optionalFieldGroups] )

        # XML Land Cover Coding file loaded into memory
        self.lccObj = lcc.LandCoverClassification(lccFilePath)
        # get the dictionary with the LCC CLASSES attributes
        self.lccClassesDict = self.lccObj.classes

        # If the user has checked the Intermediates option, name the tabulateArea table. This will cause it to be saved.
        self.tableName = None
        self.saveIntermediates = globalConstants.intermediateName in self.optionalGroupsList
        if self.saveIntermediates:
            self.tableName = metricConst.shortName + globalConstants.tabulateAreaTableAbbv

        # Save other input parameters as class attributes
        self.outTable = outTable
        self.inReportingUnitFeature = inReportingUnitFeature
        self.reportingUnitIdField = reportingUnitIdField
        self.metricConst = metricConst
        self.inLandCoverGrid = inLandCoverGrid
        self.ignoreHighest = ignoreHighest
        self.scratchNameToBeDeleted =  ""

    def _replaceLCGrid(self):
        # Placeholder for internal function to replace the landcover grid.  Several metric Calculations require this step, but others skip it.
        pass

    def _replaceRUFeatures(self):
        # Placeholder for internal function for buffer calculations - most calculations don't require this step.
        pass

    def _housekeeping(self):
        # Perform additional housekeeping steps - this must occur after any LCGrid or inRUFeature replacement

        # alert user if the LCC XML document has any values within a class definition that are also tagged as 'excluded' in the values node.
        settings.checkExcludedValuesInClass(self.metricsBaseNameList, self.lccObj, self.lccClassesDict)
        # alert user if the land cover grid has values undefined in the LCC XML file
        settings.checkGridValuesInLCC(self.inLandCoverGrid, self.lccObj, self.ignoreHighest)
        # alert user if the land cover grid cells are not square (default to size along x axis)
        settings.checkGridCellDimensions(self.inLandCoverGrid)
        # if an OID type field is used for the Id field, create a new field; type integer. Otherwise copy the Id field
        self.outIdField = settings.getIdOutField(self.inReportingUnitFeature, self.reportingUnitIdField)

        # If QAFIELDS option is checked, compile a dictionary with key:value pair of ZoneId:ZoneArea
        self.zoneAreaDict = None
        if globalConstants.qaCheckName in self.optionalGroupsList:
            # Check to see if an outputGeorgraphicCoordinate system is set in the environments. If one is not specified
            # return the spatial reference for the land cover grid. Use the returned spatial reference to calculate the
            # area of the reporting unit's polygon features to store in the zoneAreaDict
            self.outputSpatialRef = settings.getOutputSpatialReference(self.inLandCoverGrid)
            self.zoneAreaDict = polygons.getMultiPartIdAreaDict(self.inReportingUnitFeature, self.reportingUnitIdField, self.outputSpatialRef)


    def _makeAttilaOutTable(self):
        AddMsg(self.timer.split() + " Constructing the ATtILA metric output table")
        # Internal function to construct the ATtILA metric output table
        self.newTable, self.metricsFieldnameDict = table.tableWriterByClass(self.outTable,
                                                                                  self.metricsBaseNameList,
                                                                                  self.optionalGroupsList,
                                                                                  self.metricConst, self.lccObj,
                                                                                  self.outIdField)
    def _makeTabAreaTable(self):
        AddMsg(self.timer.split() + " Generating a zonal tabulate area table")
        # Internal function to generate a zonal tabulate area table
        self.tabAreaTable = TabulateAreaTable(self.inReportingUnitFeature, self.reportingUnitIdField,
                                              self.inLandCoverGrid, self.tableName, self.lccObj)

    def _calculateMetrics(self):
        AddMsg(self.timer.split() + " Processing the tabulate area table and computing metric values")
        # Internal function to process the tabulate area table and compute metric values. Use values to populate the ATtILA output table
        # Default calculation is land cover proportions.  this may be overridden by some metrics.
        calculate.landCoverProportions(self.lccClassesDict, self.metricsBaseNameList, self.optionalGroupsList,
                                             self.metricConst, self.outIdField, self.newTable, self.tabAreaTable,
                                             self.metricsFieldnameDict, self.zoneAreaDict)

    # Function to run all the steps in the calculation process
    def run(self):
        # Replace LandCover Grid, if necessary
        self._replaceLCGrid()

        # Replace Reporting Unit features, if necessary
        self._replaceRUFeatures()

        # Perform additional housekeeping
        self._housekeeping()

        # Make Output Tables
        self._makeAttilaOutTable()

        # Generate Tabulation tables
        self._makeTabAreaTable()

        # Run final metric calculation
        self._calculateMetrics()
        
        # ensure cleanup occurs.
        if self.tabAreaTable != None:
            del self.tabAreaTable


def runLandCoverProportions(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, _lccName, lccFilePath,
                            metricsToRun, outTable, processingCellSize, snapRaster, optionalFieldGroups):
    """ Interface for script executing Land Cover Proportion Metrics """

    
    try:
        # retrieve the attribute constants associated with this metric
        metricConst = metricConstants.lcpConstants()
        # Create new instance of metricCalc class to contain parameters
        lcpCalc = metricCalc(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, lccFilePath,
                             metricsToRun, outTable, processingCellSize, snapRaster, optionalFieldGroups, metricConst)
        # Run Calculation
        lcpCalc.run()
    except Exception as e:
        errors.standardErrorHandling(e)

    finally:
        setupAndRestore.standardRestore()


def runLandCoverProportionsPerCapita(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, _lccName, lccFilePath,
                                     metricsToRun, outTable, perCapitaYN, inCensusDataset, inPopField, processingCellSize, 
                                     snapRaster, optionalFieldGroups):
    """ Interface for script executing Population Density Metrics """
    
    try:
        # retrieve the attribute constants associated with this metric
        metricConst = metricConstants.lcppcConstants()
        
        # Create new subclass of metric calculation
        class metricCalcLCPPC(metricCalc):        
        
            def _makeAttilaOutTable(self):
                AddMsg(self.timer.split() + " Constructing the ATtILA metric output table")
                # Internal function to construct the ATtILA metric output table
                if perCapitaYN == "true":     
                    self.newTable, self.metricsFieldnameDict = table.tableWriterByClass(self.outTable, 
                                                                                        self.metricsBaseNameList,
                                                                                        self.optionalGroupsList, 
                                                                                        self.metricConst, 
                                                                                        self.lccObj, 
                                                                                        self.outIdField, 
                                                                                        self.metricConst.additionalFields)
                else:
                    self.newTable, self.metricsFieldnameDict = table.tableWriterByClass(self.outTable,
                                                                                        self.metricsBaseNameList,
                                                                                        self.optionalGroupsList,
                                                                                        self.metricConst, 
                                                                                        self.lccObj,
                                                                                        self.outIdField)     
        
            def _calculateMetrics(self):
                # Initiate our flexible cleanuplist
                if lcppcCalc.saveIntermediates:
                    lcppcCalc.cleanupList.append("KeepIntermediates")  # add this string as the first item in the cleanupList to prevent cleanups
                else:
                    lcppcCalc.cleanupList.append((arcpy.AddMessage,("Cleaning up intermediate datasets",)))
                    
                self.zonePopulationDict = None
                if perCapitaYN == "true":
                    self.index = 0
                    
                    # Generate name for reporting unit population count table.
                    self.popTable = files.nameIntermediateFile([metricConst.valueCountTableName,'Dataset'],self.cleanupList)

                    # Generate table with population counts by reporting unit
                    AddMsg(self.timer.split() + " Calculating population within each reporting unit") 
                    self.populationTable, self.populationField = table.createPolygonValueCountTable(self.inReportingUnitFeature,
                                                                         self.reportingUnitIdField,
                                                                         self.inCensusDataset,
                                                                         self.inPopField,
                                                                         self.popTable,
                                                                         self.metricConst,
                                                                         self.index,
                                                                         self.cleanupList)
                    
                    # Assemble dictionary with the reporting unit's ID as key, and the area-weighted population as the value
                    self.zonePopulationDict = table.getIdValueDict(self.populationTable, 
                                                                   self.reportingUnitIdField, 
                                                                   self.populationField)

                
                AddMsg(self.timer.split() + " Processing the tabulate area table and computing metric values")
                # Internal function to process the tabulate area table and compute metric values. Use values to populate the ATtILA output table
                # Default calculation is land cover proportions.  this may be overridden by some metrics.
                calculate.landCoverProportions(self.lccClassesDict, self.metricsBaseNameList, self.optionalGroupsList,
                                               self.metricConst, self.outIdField, self.newTable, self.tabAreaTable,
                                               self.metricsFieldnameDict, self.zoneAreaDict, self.zonePopulationDict,
                                               self.conversionFactor)

        
        # Create new instance of metricCalc class to contain parameters
        lcppcCalc = metricCalcLCPPC(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, lccFilePath,
                             metricsToRun, outTable, processingCellSize, snapRaster, optionalFieldGroups, metricConst)
        
        # Assign class attributes unique to this module.
        lcppcCalc.perCapitaYN = perCapitaYN
        lcppcCalc.inCensusDataset = inCensusDataset
        lcppcCalc.inPopField = inPopField
        lcppcCalc.cleanupList = [] # This is an empty list object that will contain tuples of the form (function, arguments) as needed for cleanup

        # see what linear units are used in the tabulate area table
        outputLinearUnits = settings.getOutputLinearUnits(inLandCoverGrid)

        # using the output linear units, get the conversion factor to convert the tabulateArea area measures to square meters
        try:
            conversionFactor = conversion.getSqMeterConversionFactor(outputLinearUnits)
        except:
            raise errors.attilaException(errorConstants.linearUnitConversionError)

        # Set the conversion factor as a class attribute
        lcppcCalc.conversionFactor = conversionFactor        
        
        # Run Calculation
        lcppcCalc.run()
    except Exception as e:
        errors.standardErrorHandling(e)

    finally:
        if not lcppcCalc.cleanupList[0] == "KeepIntermediates":
            for (function,arguments) in lcppcCalc.cleanupList:
                # Flexibly executes any functions added to cleanup array.
                function(*arguments)
        setupAndRestore.standardRestore()
        

def runLandCoverOnSlopeProportions(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, _lccName, lccFilePath,
                                   metricsToRun, inSlopeGrid, inSlopeThresholdValue, outTable, processingCellSize,
                                   snapRaster, optionalFieldGroups, clipLCGrid):
    """ Interface for script executing Land Cover on Slope Proportions (Land Cover Slope Overlap)"""

    try:
        # retrieve the attribute constants associated with this metric
        metricConst = metricConstants.lcospConstants()
        # append the slope threshold value to the field suffix
        metricConst.fieldParameters[1] = metricConst.fieldSuffix + inSlopeThresholdValue
        
        #If clipLCGrid is selected, clip the input raster to the extent of the reporting unit theme or the to the extent
        #of the selected reporting unit(s). If the metric is susceptible to edge-effects (e.g., core and edge metrics, 
        #patch metrics) extend the clip envelope an adequate distance.       
        
        from arcpy import env        
        _tempEnvironment1 = env.workspace
        env.workspace = environment.getWorkspaceForIntermediates(globalConstants.scratchGDBFilename, os.path.dirname(outTable))

        if clipLCGrid == "true":
            timer = DateTimer()
            AddMsg(timer.start() + " Reducing input Land cover grid to smallest recommended size...")
            pathRoot = os.path.splitext(inLandCoverGrid)[0]
            namePrefix = "%s_%s" % (metricConst.shortName, os.path.basename(pathRoot))
            scratchName = arcpy.CreateScratchName(namePrefix,"","RasterDataset")
            inLandCoverGrid = raster.clipGridByBuffer(inReportingUnitFeature, scratchName, inLandCoverGrid)
            AddMsg(timer.split() + " Reduction complete")

        
        # Create new subclass of metric calculation
        class metricCalcLCOSP(metricCalc):
            # Subclass that overrides specific functions for the LandCoverOnSlopeProportions calculation
            def _replaceLCGrid(self):
                # replace the inLandCoverGrid
                self.inLandCoverGrid = raster.getIntersectOfGrids(self.lccObj, self.inLandCoverGrid, self.inSlopeGrid,
                                                                   self.inSlopeThresholdValue,self.timer)

                if self.saveIntermediates:
                    self.namePrefix = self.metricConst.shortName+"_"+"Raster"+metricConst.fieldParameters[1]
                    self.scratchName = arcpy.CreateScratchName(self.namePrefix, "", "RasterDataset")
                    self.inLandCoverGrid.save(self.scratchName)
                    #arcpy.CopyRaster_management(self.inLandCoverGrid, self.scratchName)
                    AddMsg(self.timer.split() + " Save intermediate grid complete: "+os.path.basename(self.scratchName))
                    
        # Set toogle to ignore 'below slope threshold' marker in slope/land cover hybrid grid when checking for undefined values
        ignoreHighest = True
        
        # Create new instance of metricCalc class to contain parameters
        lcspCalc = metricCalcLCOSP(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, lccFilePath,
                      metricsToRun, outTable, processingCellSize, snapRaster, optionalFieldGroups, metricConst, ignoreHighest)

        lcspCalc.inSlopeGrid = inSlopeGrid
        lcspCalc.inSlopeThresholdValue = inSlopeThresholdValue

        # Run Calculation
        lcspCalc.run()
        
        if clipLCGrid == "true":
            arcpy.Delete_management(scratchName) 

    except Exception as e:
        errors.standardErrorHandling(e)

    finally:
        setupAndRestore.standardRestore()
        env.workspace = _tempEnvironment1
        
        
def runFloodplainLandCoverProportions(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, _lccName, lccFilePath,
                                   metricsToRun, inFloodplainGeodataset, outTable, processingCellSize, snapRaster, 
                                   optionalFieldGroups, clipLCGrid):
    """ Interface for script executing Land Cover on Slope Proportions (Land Cover Slope Overlap)"""
        
    try:
        # retrieve the attribute constants associated with this metric
        metricConst = metricConstants.flcpConstants()
          
        #If clipLCGrid is selected, clip the input raster to the extent of the reporting unit theme or the to the extent
        #of the selected reporting unit(s). If the metric is susceptible to edge-effects (e.g., core and edge metrics, 
        #patch metrics) extend the clip envelope an adequate distance.       
          
        from arcpy import env        
        _tempEnvironment1 = env.workspace
        env.workspace = environment.getWorkspaceForIntermediates(globalConstants.scratchGDBFilename, os.path.dirname(outTable))
  
        if clipLCGrid == "true":
            timer = DateTimer()
            AddMsg(timer.start() + " Reducing input Land cover grid to smallest recommended size...")
            pathRoot = os.path.splitext(inLandCoverGrid)[0]
            namePrefix = "%s_%s" % (metricConst.shortName, os.path.basename(pathRoot))
            scratchName = arcpy.CreateScratchName(namePrefix,"","RasterDataset")
            inLandCoverGrid = raster.clipGridByBuffer(inReportingUnitFeature, scratchName, inLandCoverGrid)
            AddMsg(timer.split() + " Reduction complete")
  
          
        # Create new subclass of metric calculation
        class metricCalcFLCPRaster(metricCalc):
            # Subclass that overrides specific functions for the FloodplainLandCoverProportions calculation
            def _replaceLCGrid(self):
                # Initiate our flexible cleanuplist
                if flcpCalc.saveIntermediates:
                    flcpCalc.cleanupList.append("KeepIntermediates")  # add this string as the first item in the cleanupList to prevent cleanups
                else:
                    flcpCalc.cleanupList.append((arcpy.AddMessage,("Cleaning up intermediate datasets",)))
                # replace the inLandCoverGrid and get a list of values to override the standard excludedValues frozenset.
                self.inLandCoverGrid, self.excludedValues = raster.getNullSubstituteGrid(self.lccObj, self.inLandCoverGrid, self.inFloodplainGeodataset,
                                                                    self.nullValuesList, self.cleanupList, self.timer)

                if self.saveIntermediates:
                    self.namePrefix = self.metricConst.shortName+"_"+"Raster"+metricConst.fieldParameters[1]
                    self.scratchName = arcpy.CreateScratchName(self.namePrefix, "", "RasterDataset")
                    self.inLandCoverGrid.save(self.scratchName)
                    AddMsg(self.timer.split() + " Save intermediate grid complete: "+os.path.basename(self.scratchName))

            def _makeTabAreaTable(self):
                AddMsg(self.timer.split() + " Generating a zonal tabulate area table")
                # Alter routine to override the standard excludedValues frozenset generated from the lccObj with a different list of Values. 
                class categoryTabAreaTable(TabulateAreaTable):
                    def __init__(self, inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, tableName=None, lccObj=None):
                      
                        self._inReportingUnitFeature = inReportingUnitFeature
                        self._reportingUnitIdField = reportingUnitIdField
                        self._inLandCoverGrid = inLandCoverGrid
                        self._tableName = tableName
                        
                        self._excludedValues = flcpCalc.excludedValues
                        
                        self._createNewTable()
                         
                
                self.tabAreaTable = categoryTabAreaTable(self.inReportingUnitFeature, self.reportingUnitIdField,
                                          self.inLandCoverGrid, self.tableName, self.lccObj)                    
                     
        class metricCalcFLCPPolygon(metricCalc):
            # Subclass that overrides specific functions for the FloodplainLandCoverProportions calculation
            def _replaceRUFeatures(self):
                # Initiate our flexible cleanuplist
                if flcpCalc.saveIntermediates:
                    flcpCalc.cleanupList.append("KeepIntermediates")  # add this string as the first item in the cleanupList to prevent cleanups
                else:
                    flcpCalc.cleanupList.append((arcpy.AddMessage,("Cleaning up intermediate datasets",)))
                     
                # Generate a default filename for the output feature class
                self.zonesName = self.metricConst.shortName + "_Zone"
                 
                # replace the inReportingUnitFeature
                self.inReportingUnitFeature, self.cleanupList = vector.getIntersectOfPolygons(self.inReportingUnitFeature, 
                                                                                              self.reportingUnitIdField, 
                                                                                              self.inFloodplainGeodataset,
                                                                                              self.zonesName, 
                                                                                              self.cleanupList, self.timer)
 
  
        # Do a Describe on the flood plain input to determine if it is a raster or polygon feature
        desc = arcpy.Describe(inFloodplainGeodataset)
         
        if desc.datasetType == "RasterDataset":
            # Set toogle to ignore highest value marker in new land cover grid when checking for undefined values.
            # This value does not exist in the original land cover grid.
            ignoreHighest = True
            # Create new instance of metricCalc class to contain parameters
            flcpCalc = metricCalcFLCPRaster(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, lccFilePath,
                      metricsToRun, outTable, processingCellSize, snapRaster, optionalFieldGroups, metricConst, ignoreHighest)
        else:
            # Create new instance of metricCalc class to contain parameters
            flcpCalc = metricCalcFLCPPolygon(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, lccFilePath,
                      metricsToRun, outTable, processingCellSize, snapRaster, optionalFieldGroups, metricConst)
         
        # Assign class attributes unique to this module.
        flcpCalc.inFloodplainGeodataset = inFloodplainGeodataset
        flcpCalc.nullValuesList = [0] # List of values in the binary flood plain grid to set to null
        flcpCalc.cleanupList = [] # This is an empty list object that will contain tuples of the form (function, arguments) as needed for cleanup
        
        # Run Calculation
        flcpCalc.run()
          
        if clipLCGrid == "true":
            arcpy.Delete_management(scratchName) 
 
    except Exception as e:
        errors.standardErrorHandling(e)
 
    finally:
        if not flcpCalc.cleanupList[0] == "KeepIntermediates":
            for (function,arguments) in flcpCalc.cleanupList:
                # Flexibly executes any functions added to cleanup array.
                function(*arguments)
        setupAndRestore.standardRestore()
        env.workspace = _tempEnvironment1


def runPatchMetrics(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, _lccName, lccFilePath, metricsToRun,
                          inPatchSize, inMaxSeparation, outTable, mdcpYN, processingCellSize, snapRaster, 
                          optionalFieldGroups, clipLCGrid):
    """ Interface for script executing Patch Metrics """
    
    #from .utils import settings

    cleanupList = [] # This is an empty list object that will contain tuples of the form (function, arguments) as needed for cleanup
    try:
        # Start the timer
        timer = DateTimer()
        AddMsg(timer.start() + " Setting up initial environment variables")
        
        # index the reportingUnitIdField to speed query results
        ruIdIndex = "ruIdIndex_ATtILA"
        indexNames = [indx.name for indx in arcpy.ListIndexes(inReportingUnitFeature)]
        if ruIdIndex not in indexNames:
            arcpy.AddIndex_management(inReportingUnitFeature, reportingUnitIdField, ruIdIndex)
        
        # retrieve the attribute constants associated with this metric
        metricConst = metricConstants.pmConstants()
        
        # setup the appropriate metric fields to add to output table depending on if MDCP is selected or not
        if mdcpYN:
            metricConst.additionalFields = metricConst.additionalFields + metricConst.mdcpFields
        else:
            metricConst.additionalFields = metricConst.additionalFields
            
        
        metricsBaseNameList, optionalGroupsList = setupAndRestore.standardSetup(snapRaster, processingCellSize,
                                                                                os.path.dirname(outTable),
                                                                                [metricsToRun,optionalFieldGroups] )
        
        if globalConstants.intermediateName in optionalGroupsList:
            cleanupList.append("KeepIntermediates")  # add this string as the first item in the cleanupList to prevent cleanups
        else:
            cleanupList.append((arcpy.AddMessage,("Cleaning up intermediate datasets",)))

        lccObj = lcc.LandCoverClassification(lccFilePath)
        # get the dictionary with the LCC CLASSES attributes
        lccClassesDict = lccObj.classes
        
        # Check to see if an outputGeorgraphicCoordinate system is set in the environments. If one is not specified
        # return the spatial reference for the land cover grid. Use the returned spatial reference to calculate the
        # area of the reporting unit's polygon features to store in the zoneAreaDict
        outputSpatialRef = settings.getOutputSpatialReference(inLandCoverGrid)

        # Compile a dictionary with key:value pair of ZoneId:ZoneArea
        zoneAreaDict = polygons.getMultiPartIdAreaDict(inReportingUnitFeature, reportingUnitIdField, outputSpatialRef)
        
        # see what linear units are output in any tabulate area calculations
        outputLinearUnits = settings.getOutputLinearUnits(inLandCoverGrid)        

        # using the output linear units, get the conversion factor to convert area measures to metric appropriate values
        try:
            conversionFactor = conversion.getSqMeterConversionFactor(outputLinearUnits)
        except:
            raise errors.attilaException(errorConstants.linearUnitConversionError)
        
        # alert user if the LCC XML document has any values within a class definition that are also tagged as 'excluded' in the values node.
        settings.checkExcludedValuesInClass(metricsBaseNameList, lccObj, lccClassesDict)
        
        # alert user if the land cover grid has values undefined in the LCC XML file
        settings.checkGridValuesInLCC(inLandCoverGrid, lccObj)
        
        # if an OID type field is used for the Id field, create a new field; type integer. Otherwise copy the Id field
        outIdField = settings.getIdOutField(inReportingUnitFeature, reportingUnitIdField)
         
        #Create the output table outside of metricCalc so that result can be added for multiple metrics
        AddMsg(timer.split() + " Creating output table")
        newtable, metricsFieldnameDict = table.tableWriterByClass(outTable, metricsBaseNameList,optionalGroupsList, 
                                                                                  metricConst, lccObj, outIdField, 
                                                                                  metricConst.additionalFields)
                
        #If clipLCGrid is selected, clip the input raster to the extent of the reporting unit theme or the to the extent
        #of the selected reporting unit(s). If the metric is susceptible to edge-effects (e.g., core and edge metrics, 
        #patch metrics) extend the clip envelope an adequate distance.

        if clipLCGrid == "true":
            AddMsg(timer.split() + "Reducing input Land cover grid to smallest recommended size...")
            
            # from . import utils
            from arcpy import env        
            _startingWorkSpace= env.workspace
            env.workspace = environment.getWorkspaceForIntermediates(globalConstants.scratchGDBFilename, os.path.dirname(outTable))
            pathRoot = os.path.splitext(inLandCoverGrid)[0]
            namePrefix = "%s_%s" % (metricConst.shortName, os.path.basename(pathRoot))
            scratchName = arcpy.CreateScratchName(namePrefix,"","RasterDataset")
            inLandCoverGrid = raster.clipGridByBuffer(inReportingUnitFeature, scratchName, inLandCoverGrid, inMaxSeparation)
            env.workspace = _startingWorkSpace
            
            AddMsg(timer.split() + " Reduction complete")
        
            
        # Run metric calculate for each metric in list
        for m in metricsBaseNameList:
            # Subclass that overrides specific functions for the MDCP calculation
            class metricCalcPM(metricCalc):

                def _replaceLCGrid(self):
                    # replace the inLandCoverGrid
                    AddMsg(self.timer.split() + " Creating Patch Grid for Class:"+m)
                    scratchNameReference = [""]
                    self.inLandCoverGrid = raster.createPatchRaster(m, self.lccObj, self.lccClassesDict, self.inLandCoverGrid,
                                                                          self.metricConst, self.maxSeparation,
                                                                          self.minPatchSize, processingCellSize, timer,
                                                                          scratchNameReference)
                    self.scratchNameToBeDeleted = scratchNameReference[0]
                    AddMsg(self.timer.split() + " Patch Grid Completed for Class:"+m)

                #skip over make out table since it has already been made
                def _makeAttilaOutTable(self):
                    pass

                #set the tabAreaTable attribute for the metric class to "None" since this metric does not require it
                def _makeTabAreaTable(self):
                    self.tabAreaTable = None
                
                #Update housekeeping so it doesn't check for lcc codes
                def _housekeeping(self):
                    # Perform additional housekeeping steps - this must occur after any LCGrid or inRUFeature replacement
                    # Removed alert about lcc codes since the lcc values are not used in the Core/Edge calculations
                    # alert user if the land cover grid cells are not square (default to size along x axis)
                    settings.checkGridCellDimensions(self.inLandCoverGrid)
                        
                # Update calculateMetrics to populate Patch Metrics and MDCP
                def _calculateMetrics(self):
                    
                    AddMsg(self.timer.split() + " Calculating Patch Numbers by Reporting Unit for Class:" + m)
                     
                    # calculate Patch metrics
                    self.pmResultsDict = calculate.getPatchNumbers(self.outIdField, self.newTable, self.reportingUnitIdField, self.metricsFieldnameDict,
                                                      self.zoneAreaDict, self.metricConst, m, self.inReportingUnitFeature, 
                                                      self.inLandCoverGrid, processingCellSize, conversionFactor)
 
                    AddMsg(timer.split() + " Patch analysis has been run for Class:" + m)
                    
                    # get class name (may have been modified from LCC XML input by ATtILA)
                    outClassName = metricsFieldnameDict[m][1]
                    
                    if mdcpYN == "true": #calculate MDCP value
                    
                        AddMsg(self.timer.split() + " Calculating MDCP for Class:" + m)
                        
                        # create and name intermediate data layers
                        rastoPolyFeatureName = ("%s_%s_%s" % (metricConst.shortName, outClassName, metricConst.rastertoPoly))
                        rastoPolyFeature = files.nameIntermediateFile([rastoPolyFeatureName, "FeatureClass"], cleanupList)
                        rasterCentroidFeatureName = ("%s_%s_%s" % (metricConst.shortName, outClassName, metricConst.rastertoPoint))
                        rasterCentroidFeature = files.nameIntermediateFile([rasterCentroidFeatureName, "FeatureClass"], cleanupList)
                        polyDissolvedPatchFeatureName = ("%s_%s_%s" % (metricConst.shortName, outClassName, metricConst.polyDissolve))
                        polyDissolvedFeature = files.nameIntermediateFile([polyDissolvedPatchFeatureName, "FeatureClass"], cleanupList)
                        nearPatchTable = files.nameIntermediateFile([outClassName + metricConst.nearTable, "Dataset"], cleanupList)            
                        
                        # run the calculation script. get the results back as a dictionary keyed to RU id values
                        self.mdcpDict =  vector.tabulateMDCP(self.inLandCoverGrid, self.inReportingUnitFeature, 
                                                                   self.reportingUnitIdField, rastoPolyFeature, rasterCentroidFeature, polyDissolvedFeature,
                                                                   nearPatchTable, self.zoneAreaDict, timer, self.pmResultsDict)
                        # place the results into the output table
                        calculate.getMDCP(self.outIdField, self.newTable, self.mdcpDict, self.optionalGroupsList,
                                                 outClassName)
                        
                        AddMsg(self.timer.split() + " MDCP analysis has been run for Class:" + m)
                    
                    if self.saveIntermediates:
                        pass
                    else:
                        arcpy.Delete_management(pmCalc.scratchNameToBeDeleted)

            # Create new instance of metricCalc class to contain parameters
            pmCalc = metricCalcPM(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, lccFilePath,
                      m, outTable, processingCellSize, snapRaster, optionalFieldGroups, metricConst)
            
            pmCalc.newTable = newtable
            pmCalc.metricsFieldnameDict = metricsFieldnameDict
            pmCalc.maxSeparation = inMaxSeparation
            pmCalc.minPatchSize = inPatchSize
            pmCalc.outIdField = outIdField
            pmCalc.zoneAreaDict = zoneAreaDict
            
            #Run Calculation
            pmCalc.run()
            
            pmCalc.metricsBaseNameList = metricsBaseNameList

        if clipLCGrid == "true":
            arcpy.Delete_management(scratchName)     
    
    except Exception as e:
        errors.standardErrorHandling(e)

    finally:
        setupAndRestore.standardRestore()
        if not cleanupList[0] == "KeepIntermediates":
            for (function,arguments) in cleanupList:
                # Flexibly executes any functions added to cleanup array.
                function(*arguments)
        arcpy.RemoveIndex_management(inReportingUnitFeature, ruIdIndex)


def runCoreAndEdgeMetrics(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, _lccName, lccFilePath, metricsToRun,
                          inEdgeWidth, outTable, processingCellSize, snapRaster, optionalFieldGroups, clipLCGrid):
    """ Interface for script executing Core/Edge Metrics """

    try:
        # retrieve the attribute constants associated with this metric
        metricConst = metricConstants.caemConstants()
        # append the edge width distance value to the field suffix
        metricConst.fieldParameters[1] = metricConst.fieldSuffix + inEdgeWidth
        # for the core and edge fields, add the edge width to the  field suffix
        for i, fldParams in enumerate(metricConst.additionalFields):
            fldParams[1] = metricConst.additionalSuffixes[i] + inEdgeWidth
        
        metricsBaseNameList, optionalGroupsList = setupAndRestore.standardSetup(snapRaster, processingCellSize,
                                                                                os.path.dirname(outTable),
                                                                                [metricsToRun,optionalFieldGroups] )

        lccObj = lcc.LandCoverClassification(lccFilePath)
        # get the dictionary with the LCC CLASSES attributes
        lccClassesDict = lccObj.classes
        
        outIdField = settings.getIdOutField(inReportingUnitFeature, reportingUnitIdField)
        
        # alert user if the LCC XML document has any values within a class definition that are also tagged as 'excluded' in the values node.
        settings.checkExcludedValuesInClass(metricsBaseNameList, lccObj, lccClassesDict)
        
        # alert user if the land cover grid has values undefined in the LCC XML file
        settings.checkGridValuesInLCC(inLandCoverGrid, lccObj)
     
        #Create the output table outside of metricCalc so that result can be added for multiple metrics
        newtable, metricsFieldnameDict = table.tableWriterByClass(outTable, metricsBaseNameList,optionalGroupsList, 
                                                                                  metricConst, lccObj, outIdField, 
                                                                                  metricConst.additionalFields)
 
        #If clipLCGrid is selected, clip the input raster to the extent of the reporting unit theme or the to the extent
        #of the selected reporting unit(s). If the metric is susceptible to edge-effects (e.g., core and edge metrics, 
        #patch metrics) extend the clip envelope an adequate distance.       

        from arcpy import env        
        _tempEnvironment1 = env.workspace
        env.workspace = environment.getWorkspaceForIntermediates(globalConstants.scratchGDBFilename, os.path.dirname(outTable))


        if clipLCGrid == "true":
            timer = DateTimer()
            AddMsg(timer.start() + " Reducing input Land cover grid to smallest recommended size...")
            pathRoot = os.path.splitext(inLandCoverGrid)[0]
            namePrefix = "%s_%s" % (metricConst.shortName, os.path.basename(pathRoot))
            scratchName = arcpy.CreateScratchName(namePrefix,"","RasterDataset")
            inLandCoverGrid = raster.clipGridByBuffer(inReportingUnitFeature, scratchName, inLandCoverGrid, inEdgeWidth)
            AddMsg(timer.split() + " Reduction complete")
        
        # Run metric calculate for each metric in list
        for m in metricsBaseNameList:
        
            class metricCalcCAEM(metricCalc):
                # Subclass that overrides specific functions for the CoreAndEdgeAreaMetric calculation
                def _replaceLCGrid(self):
                    # replace the inLandCoverGrid
                    AddMsg(self.timer.split() + " Generating core and edge grid for Class: " + m.upper())
                    scratchNameReference =  [""];
                    self.inLandCoverGrid = raster.getEdgeCoreGrid(m, self.lccObj, self.lccClassesDict, self.inLandCoverGrid, 
                                                                        self.inEdgeWidth, processingCellSize,
                                                                        self.timer, metricConst.shortName, scratchNameReference)
                    self.scratchNameToBeDeleted = scratchNameReference[0]
                    AddMsg(self.timer.split() + " Core and edge grid complete")
                    
                    #Moved the save intermediate grid to the calcMetrics function so it would be one of the last steps to be performed

                #skip over make out table since it has already been made
                def _makeAttilaOutTable(self):
                    pass  
                
                def _makeTabAreaTable(self):
                    AddMsg(self.timer.split() + " Generating a zonal tabulate area table")
                    # Internal function to generate a zonal tabulate area table
                    class categoryTabAreaTable(TabulateAreaTable):
                        #Update definition so Tabulate Table is run on the POS field.
                        def _createNewTable(self):
                            self._value = "CATEGORY"
                            if self._tableName:
                                self._destroyTable = False
                                self._tableName = arcpy.CreateScratchName(self._tableName+m+inEdgeWidth, "", self._datasetType)
                            else:
                                self._tableName = arcpy.CreateScratchName(self._tempTableName+m+inEdgeWidth, "", self._datasetType)

                            arcpy.gp.TabulateArea_sa(self._inReportingUnitFeature, self._reportingUnitIdField, self._inLandCoverGrid, 
                                 self._value, self._tableName)
                            
                            self._tabAreaTableRows = arcpy.SearchCursor(self._tableName)        
                            self._tabAreaValueFields = arcpy.ListFields(self._tableName, "", "DOUBLE")
                            self._tabAreaValues = [aFld.name for aFld in self._tabAreaValueFields]
                            self._tabAreaDict = dict(zip(self._tabAreaValues,[])) 
                             
                    self.lccObj = None
                    
                    self.tabAreaTable = categoryTabAreaTable(self.inReportingUnitFeature, self.reportingUnitIdField,
                                              self.inLandCoverGrid, self.tableName, self.lccObj)
                    
                # Update housekeeping. Moved checks for undefined grid values and excluded grid values in class definitions
                # out of the for loop. Now they are only ran once at the beginning of the metric run
                def _housekeeping(self):
                    # Perform additional housekeeping steps - this must occur after any LCGrid or inRUFeature replacement

                    # alert user if the land cover grid cells are not square (default to size along x axis)
                    settings.checkGridCellDimensions(self.inLandCoverGrid)
                    # if an OID type field is used for the Id field, create a new field; type integer. Otherwise copy the Id field
                    self.outIdField = settings.getIdOutField(self.inReportingUnitFeature, self.reportingUnitIdField)
                
                    # If QAFIELDS option is checked, compile a dictionary with key:value pair of ZoneId:ZoneArea
                    self.zoneAreaDict = None
                    if globalConstants.qaCheckName in self.optionalGroupsList:
                        # Check to see if an outputGeorgraphicCoordinate system is set in the environments. If one is not specified
                        # return the spatial reference for the land cover grid. Use the returned spatial reference to calculate the
                        # area of the reporting unit's polygon features to store in the zoneAreaDict
                        self.outputSpatialRef = settings.getOutputSpatialReference(self.inLandCoverGrid)
                        self.zoneAreaDict = polygons.getMultiPartIdAreaDict(self.inReportingUnitFeature, self.reportingUnitIdField, self.outputSpatialRef)

                # Update calculateMetrics to calculate Core to Edge Ratio
                def _calculateMetrics(self):
                    self.newTable = newtable
                    self.metricsFieldnameDict = metricsFieldnameDict

                    # calculate Core to Edge ratio
                    calculate.getCoreEdgeRatio(self.outIdField, self.newTable, self.tabAreaTable, self.metricsFieldnameDict,
                                                      self.zoneAreaDict, self.metricConst, m)
                    AddMsg(self.timer.split() + " Core/Edge Ratio calculations are complete for class: " + m)


            # Create new instance of metricCalc class to contain parameters
            caemCalc = metricCalcCAEM(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, lccFilePath,
                          m, outTable, processingCellSize, snapRaster, optionalFieldGroups, metricConst)
    
            caemCalc.inEdgeWidth = inEdgeWidth
    
            # Run Calculation
            caemCalc.run()
            
            caemCalc.metricsBaseNameList = metricsBaseNameList

            #delet the intermediate raster if save intermediates option is not chosen 
            if caemCalc.saveIntermediates:
                pass
            else:
                directory = env.workspace
                path = os.path.join(directory, caemCalc.scratchNameToBeDeleted)
                arcpy.Delete_management(path)

            
        if clipLCGrid == "true":
            arcpy.Delete_management(scratchName)

    except Exception as e:
        errors.standardErrorHandling(e)

    finally:
        setupAndRestore.standardRestore()
        env.workspace = _tempEnvironment1
        

def runRiparianLandCoverProportions(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, _lccName, lccFilePath,
                            metricsToRun, inStreamFeatures, inBufferDistance, enforceBoundary, outTable, processingCellSize, snapRaster,
                            optionalFieldGroups):
    """ Interface for script executing Riparian Land Cover Proportion Metrics """
    try:
        # retrieve the attribute constants associated with this metric
        metricConst = metricConstants.rlcpConstants()
        # append the buffer distance value to the field suffix
        metricConst.fieldParameters[1] = metricConst.fieldSuffix + inBufferDistance.split()[0]

        class metricCalcRLCP(metricCalc):
            """ Subclass that overrides buffering function for the RiparianLandCoverProportions calculation """
            def _replaceRUFeatures(self):
                # check for duplicate ID entries in reportng unit feature. Perform dissolve if found
                self.duplicateIds = fields.checkForDuplicateValues(self.inReportingUnitFeature, self.reportingUnitIdField)
                # Initiate our flexible cleanuplist
                if rlcpCalc.saveIntermediates:
                    rlcpCalc.cleanupList.append("KeepIntermediates")  # add this string as the first item in the cleanupList to prevent cleanups
                else:
                    rlcpCalc.cleanupList.append((arcpy.AddMessage,("Cleaning up intermediate datasets",)))
                if self.duplicateIds:
                    AddMsg("Duplicate ID values found in reporting unit feature. Forming multipart features...")
                    # Get a unique name with full path for the output features - will default to current workspace:
                    self.namePrefix = self.metricConst.shortName + "_Dissolve"+self.inBufferDistance.split()[0]
                    self.dissolveName = utils.files.nameIntermediateFile([self.namePrefix,"FeatureClass"], rlcpCalc.cleanupList)
                    self.inReportingUnitFeature = arcpy.Dissolve_management(self.inReportingUnitFeature, self.dissolveName, 
                                                                            self.reportingUnitIdField,"","MULTI_PART")
                    
                # Generate a default filename for the buffer feature class
                self.bufferName = self.metricConst.shortName + "_Buffer"+self.inBufferDistance.split()[0]
                # Generate the buffer area to use in the metric calculation
                if enforceBoundary == "true":
                    self.inReportingUnitFeature, self.cleanupList = vector.bufferFeaturesByIntersect(self.inStreamFeatures,
                                                                                     self.inReportingUnitFeature,
                                                                                     self.bufferName, self.inBufferDistance,
                                                                                     self.reportingUnitIdField,
                                                                                     self.cleanupList)
                else:
                    self.inReportingUnitFeature, self.cleanupList = vector.bufferFeaturesWithoutBorders(self.inStreamFeatures,
                                                                                     self.inReportingUnitFeature,
                                                                                     self.bufferName, self.inBufferDistance,
                                                                                     self.reportingUnitIdField,
                                                                                     self.cleanupList)
        
        # Create new instance of metricCalc class to contain parameters
        rlcpCalc = metricCalcRLCP(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, lccFilePath,
                       metricsToRun, outTable, processingCellSize, snapRaster, optionalFieldGroups, metricConst)

        # Assign class attributes unique to this module.
        rlcpCalc.inStreamFeatures = inStreamFeatures
        rlcpCalc.inBufferDistance = inBufferDistance
        rlcpCalc.enforceBoundary = enforceBoundary

        rlcpCalc.cleanupList = [] # This is an empty list object that will contain tuples of the form (function, arguments) as needed for cleanup

        # Run Calculation
        rlcpCalc.run()      
       
    except Exception as e:
        errors.standardErrorHandling(e)

    finally:
        if not rlcpCalc.cleanupList[0] == "KeepIntermediates":
            for (function,arguments) in rlcpCalc.cleanupList:
                # Flexibly executes any functions added to cleanup array.
                function(*arguments)
        setupAndRestore.standardRestore()

def runSamplePointLandCoverProportions(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, _lccName, lccFilePath,
                            metricsToRun, inPointFeatures, ruLinkField, inBufferDistance, enforceBoundary, outTable, processingCellSize, 
                            snapRaster, optionalFieldGroups):
    """ Interface for script executing Sample Point Land Cover Proportion Metrics """

    try:
        # retrieve the attribute constants associated with this metric
        metricConst = metricConstants.splcpConstants()
        # append the buffer distance value to the field suffix
        metricConst.fieldParameters[1] = metricConst.fieldSuffix + inBufferDistance.split()[0]

        class metricCalcSPLCP(metricCalc):
            """ Subclass that overrides specific functions for the SamplePointLandCoverProportions calculation """
            def _replaceRUFeatures(self):
                # check for duplicate ID entries. Perform dissolve if found
                self.duplicateIds = fields.checkForDuplicateValues(self.inReportingUnitFeature, self.reportingUnitIdField)
                
                if self.duplicateIds:
                    AddMsg("Duplicate ID values found in reporting unit feature. Forming multipart features...")
                    # Get a unique name with full path for the output features - will default to current workspace:
                    self.namePrefix = self.metricConst.shortName + "_Dissolve"+self.inBufferDistance.split()[0]
                    self.dissolveName = arcpy.CreateScratchName(self.namePrefix,"","FeatureClass")
                    self.inReportingUnitFeature = arcpy.Dissolve_management(self.inReportingUnitFeature, self.dissolveName, 
                                                                            self.reportingUnitIdField,"","MULTI_PART")
                    
                # Generate a default filename for the buffer feature class
                self.bufferName = self.metricConst.shortName + "_Buffer"+self.inBufferDistance.split()[0]
                # Buffer the points and use the output as the new reporting units
                self.inReportingUnitFeature = vector.bufferFeaturesByID(self.inPointFeatures,
                                                                              self.inReportingUnitFeature,
                                                                              self.bufferName,self.inBufferDistance,
                                                                              self.reportingUnitIdField,self.ruLinkField)
                # Since we are replacing the reporting unit features with the buffered features we also need to replace
                # the unique identifier field - which is now the ruLinkField.
                self.reportingUnitIdField = self.ruLinkField

        # Create new instance of metricCalc class to contain parameters
        splcpCalc = metricCalcSPLCP(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, lccFilePath,
                       metricsToRun, outTable, processingCellSize, snapRaster, optionalFieldGroups, metricConst)

        # Assign class attributes unique to this module.
        splcpCalc.inPointFeatures = inPointFeatures
        splcpCalc.inBufferDistance = inBufferDistance
        splcpCalc.ruLinkField = ruLinkField
        splcpCalc.enforceBoundary = enforceBoundary

        # Run Calculation
        splcpCalc.run()

        # Clean up intermediates.  
        if not splcpCalc.saveIntermediates:
            # note, this is actually deleting the buffers, not the source reporting units.
            arcpy.Delete_management(splcpCalc.inReportingUnitFeature)
            
            if splcpCalc.duplicateIds:
                arcpy.Delete_management(splcpCalc.dissolveName)

    except Exception as e:
        errors.standardErrorHandling(e)

    finally:
        setupAndRestore.standardRestore()


def runLandCoverCoefficientCalculator(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, _lccName,
                                      lccFilePath, metricsToRun, outTable, processingCellSize, snapRaster,
                                      optionalFieldGroups):
    """Interface for script executing Land Cover Coefficient Calculator"""

    try:
        # retrieve the attribute constants associated with this metric
        metricConst = metricConstants.lcccConstants()

        # Create new LCC metric calculation subclass
        class metricCalcLCC(metricCalc):
            # Subclass that overrides specific functions for the land Cover Coefficient calculation
            def _makeAttilaOutTable(self):
                # Construct the ATtILA metric output table
                self.newTable, self.metricsFieldnameDict = table.tableWriterByCoefficient(self.outTable,
                                                                                                self.metricsBaseNameList,
                                                                                                self.optionalGroupsList,
                                                                                                self.metricConst, self.lccObj,
                                                                                                self.outIdField)
            def _calculateMetrics(self):
                # process the tabulate area table and compute metric values. Use values to populate the ATtILA output table
                calculate.landCoverCoefficientCalculator(self.lccObj.values, self.metricsBaseNameList,
                                                               self.optionalGroupsList, self.metricConst, self.outIdField,
                                                               self.newTable, self.tabAreaTable, self.metricsFieldnameDict,
                                                               self.zoneAreaDict, self.conversionFactor)

        # Instantiate LCC metric calculation subclass
        lccCalc = metricCalcLCC(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, lccFilePath,
                      metricsToRun, outTable, processingCellSize, snapRaster, optionalFieldGroups, metricConst)

        # see what linear units are used in the tabulate area table
        outputLinearUnits = settings.getOutputLinearUnits(inLandCoverGrid)

        # using the output linear units, get the conversion factor to convert the tabulateArea area measures to hectares
        try:
            conversionFactor = conversion.getSqMeterConversionFactor(outputLinearUnits)
        except:
            raise errors.attilaException(errorConstants.linearUnitConversionError)
            #raise

        # Set the conversion factor as a class attribute
        lccCalc.conversionFactor = conversionFactor

        # Run calculation
        lccCalc.run()

    except Exception as e:
        errors.standardErrorHandling(e)

    finally:
        setupAndRestore.standardRestore()



def runRoadDensityCalculator(inReportingUnitFeature, reportingUnitIdField, inRoadFeature, outTable, roadClassField="",
                             streamRoadCrossings="#", roadsNearStreams="#", inStreamFeature="#", bufferDistance="#",
                             optionalFieldGroups="#"):
    """Interface for script executing Road Density Calculator"""
    from arcpy import env

    cleanupList = [] # This is an empty list object that will contain tuples of the form (function, arguments) as needed for cleanup
    try:
        # Work on making as generic as possible
        ### Initialization
        # Start the timer
        timer = DateTimer()
        AddMsg(timer.start() + " Setting up environment variables")
        # Get the metric constants
        metricConst = metricConstants.rdmConstants()
        # Set the output workspace
        _tempEnvironment1 = env.workspace
        env.workspace = environment.getWorkspaceForIntermediates(globalConstants.scratchGDBFilename, os.path.dirname(outTable))
        _tempEnvironment4 = env.outputMFlag
        _tempEnvironment5 = env.outputZFlag
        # Streams and road crossings script fails in certain circumstances when M (linear referencing dimension) is enabled.
        # Disable for the duration of the tool.
        env.outputMFlag = "Disabled"
        env.outputZFlag = "Disabled"
        # Strip the description from the "additional option" and determine whether intermediates are stored.
        processed = parameters.splitItemsAndStripDescriptions(optionalFieldGroups, globalConstants.descriptionDelim)
        if globalConstants.intermediateName in processed:
            msg = "\nIntermediates are stored in this directory: {0}\n"
            arcpy.AddMessage(msg.format(env.workspace)) 
            #AddMsg(msg.format(env.workspace))
            cleanupList.append("KeepIntermediates")  # add this string as the first item in the cleanupList to prevent cleanups
        else:
            cleanupList.append((arcpy.AddMessage,("Cleaning up intermediate datasets",)))
        
        # Create a copy of the reporting unit feature class that we can add new fields to for calculations.  This 
        # is more appropriate than altering the user's input data. A dissolve will handle the condition of non-unique id
        # values and will also keep only the OID, shape, and reportingUnitIdField fields
        desc = arcpy.Describe(inReportingUnitFeature)
        tempName = "%s_%s" % (metricConst.shortName, desc.baseName)
        tempReportingUnitFeature = files.nameIntermediateFile([tempName,"FeatureClass"],cleanupList)
        AddMsg(timer.split() + " Creating temporary copy of " + desc.name)
        inReportingUnitFeature = arcpy.Dissolve_management(inReportingUnitFeature, os.path.basename(tempReportingUnitFeature), 
                                                           reportingUnitIdField,"","MULTI_PART")

        # Get the field properties for the unitID, this will be frequently used
        # If the field is numeric, it creates a text version of the field.
        uIDField = settings.processUIDField(inReportingUnitFeature,reportingUnitIdField)

        AddMsg(timer.split() + " Calculating reporting unit area")
        # Add a field to the reporting units to hold the area value in square kilometers
        # Check for existence of field.
        fieldList = arcpy.ListFields(inReportingUnitFeature,metricConst.areaFieldname)
        # Add and populate the area field (or just recalculate if it already exists
        unitArea = vector.addAreaField(inReportingUnitFeature,metricConst.areaFieldname)
        if not fieldList: # if the list of fields that exactly match the validated fieldname is empty...
            if not cleanupList[0] == "KeepIntermediates":
                # ...add this to the list of items to clean up at the end.
                pass
                # *** this was previously necessary when the field was added to the input - now that a copy of the input
                #     is used instead, this is not necessary.
                #cleanupList.append((arcpy.DeleteField_management,(inReportingUnitFeature,unitArea)))

        # If necessary, create a copy of the road feature class to remove M values.  The env.outputMFlag will work
        # for most datasets except for shapefiles with M and Z values. The Z value will keep the M value from being stripped
        # off. This is more appropriate than altering the user's input data.
        desc = arcpy.Describe(inRoadFeature)
        if desc.HasM or desc.HasZ:
            tempName = "%s_%s" % (metricConst.shortName, arcpy.Describe(inRoadFeature).baseName)
            tempLineFeature = files.nameIntermediateFile([tempName,"FeatureClass"],cleanupList)
            AddMsg(timer.split() + " Creating temporary copy of " + desc.name)
            inRoadFeature = arcpy.FeatureClassToFeatureClass_conversion(inRoadFeature, env.workspace, os.path.basename(tempLineFeature))


        AddMsg(timer.split() + " Calculating road density")
        # Get a unique name for the merged roads and prep for cleanup
        mergedRoads = files.nameIntermediateFile(metricConst.roadsByReportingUnitName,cleanupList)

        # Calculate the density of the roads by reporting unit.
        mergedRoads, roadLengthFieldName = calculate.lineDensityCalculator(inRoadFeature,inReportingUnitFeature,
                                                                                 uIDField,unitArea,mergedRoads,
                                                                                 metricConst.roadDensityFieldName,
                                                                                 metricConst.roadLengthFieldName,
                                                                                 roadClassField,
                                                                                 metricConst.totalImperviousAreaFieldName)

        # Build and populate final output table.
        AddMsg(timer.split() + " Compiling calculated values into output table")
        arcpy.TableToTable_conversion(inReportingUnitFeature,os.path.dirname(outTable),os.path.basename(outTable))
        # Get a list of unique road class values
        if roadClassField:
            classValues = fields.getUniqueValues(mergedRoads,roadClassField)
        else:
            classValues = []
        # Compile a list of fields that will be transferred from the merged roads feature class into the output table
        fromFields = [roadLengthFieldName, metricConst.roadDensityFieldName,metricConst.totalImperviousAreaFieldName]
        # Transfer the values to the output table, pivoting the class values into new fields if necessary.
        table.transferField(mergedRoads,outTable,fromFields,fromFields,uIDField.name,roadClassField,classValues)
        
        # If the Streams By Roads (STXRD) box is checked...
        if streamRoadCrossings and streamRoadCrossings != "false":
            # If necessary, create a copy of the stream feature class to remove M values.  The env.outputMFlag will work
            # for most datasets except for shapefiles with M and Z values. The Z value will keep the M value from being stripped
            # off. This is more appropriate than altering the user's input data.
            desc = arcpy.Describe(inStreamFeature)
            if desc.HasM or desc.HasZ:
                tempName = "%s_%s" % (metricConst.shortName, desc.baseName)
                tempLineFeature = files.nameIntermediateFile([tempName,"FeatureClass"],cleanupList)
                AddMsg(timer.split() + " Creating temporary copy of " + desc.name)
                inStreamFeature = arcpy.FeatureClassToFeatureClass_conversion(inStreamFeature, env.workspace, os.path.basename(tempLineFeature))

            
            AddMsg(timer.split() + " Calculating Stream and Road Crossings (STXRD)")
            # Get a unique name for the merged streams:
            mergedStreams = files.nameIntermediateFile(metricConst.streamsByReportingUnitName,cleanupList)

            # Calculate the density of the streams by reporting unit.
            mergedStreams, streamLengthFieldName = calculate.lineDensityCalculator(inStreamFeature,
                                                                                         inReportingUnitFeature,
                                                                                         uIDField,
                                                                                         unitArea,mergedStreams,
                                                                                         metricConst.streamDensityFieldName,
                                                                                         metricConst.streamLengthFieldName)

            # Get a unique name for the road/stream intersections:
            roadStreamMultiPoints = files.nameIntermediateFile(metricConst.roadStreamMultiPoints,cleanupList)
            # Get a unique name for the points of crossing:
            roadStreamIntersects = files.nameIntermediateFile(metricConst.roadStreamIntersects,cleanupList)
            # Get a unique name for the roads by streams summary table:
            roadStreamSummary = files.nameIntermediateFile(metricConst.roadStreamSummary,cleanupList)
            
            # Perform the roads/streams intersection and calculate the number of crossings and crossings per km
            vector.findIntersections(mergedRoads,inStreamFeature,mergedStreams,uIDField,roadStreamMultiPoints,
                                           roadStreamIntersects,roadStreamSummary,streamLengthFieldName,
                                           metricConst.xingsPerKMFieldName,roadClassField)
            
            # Transfer values to final output table.
            AddMsg(timer.split() + " Compiling calculated values into output table")
            # Compile a list of fields that will be transferred from the merged roads feature class into the output table
            fromFields = [streamLengthFieldName, metricConst.streamDensityFieldName]
            # Transfer the values to the output table, pivoting the class values into new fields if necessary.
            # Possible to add stream class values here if desired.
            table.transferField(mergedStreams,outTable,fromFields,fromFields,uIDField.name,None)
            # Transfer crossings fields - note the renaming of the count field.
            fromFields = ["FREQUENCY", metricConst.xingsPerKMFieldName]
            toFields = [metricConst.streamRoadXingsCountFieldname,metricConst.xingsPerKMFieldName]
            # Transfer the values to the output table, pivoting the class values into new fields if necessary.
            table.transferField(roadStreamSummary,outTable,fromFields,toFields,uIDField.name,roadClassField,classValues)
            

        if roadsNearStreams and roadsNearStreams != "false":
            AddMsg(timer.split() + " Calculating Roads Near Streams (RNS)")
            if not streamRoadCrossings or streamRoadCrossings == "false":  # In case merged streams haven't already been calculated:
                # Create a copy of the stream feature class, if necessary, to remove M values.  The env.outputMFlag will work
                # for most datasets except for shapefiles with M and Z values. The Z value will keep the M value from being stripped
                # off. This is more appropriate than altering the user's input data.
                desc = arcpy.Describe(inStreamFeature)
                if desc.HasM or desc.HasZ:
                    tempName = "%s_%s" % (metricConst.shortName, desc.baseName)
                    tempLineFeature = files.nameIntermediateFile([tempName,"FeatureClass"],cleanupList)
                    AddMsg(timer.split() + " Creating temporary copy of " + desc.name)
                    inStreamFeature = arcpy.FeatureClassToFeatureClass_conversion(inStreamFeature, env.workspace, os.path.basename(tempLineFeature))
                
                # Get a unique name for the merged streams:
                mergedStreams = files.nameIntermediateFile(metricConst.streamsByReportingUnitName,cleanupList)
                # Calculate the density of the streams by reporting unit.
                mergedStreams, streamLengthFieldName = calculate.lineDensityCalculator(inStreamFeature,
                                                                                             inReportingUnitFeature,
                                                                                             uIDField,unitArea,mergedStreams,
                                                                                             metricConst.streamDensityFieldName,
                                                                                             metricConst.streamLengthFieldName)
            # Get a unique name for the buffered streams:
            streamBuffer = files.nameIntermediateFile(metricConst.streamBuffers,cleanupList)
            # Set a unique name for the undissolved  road/stream buffer intersections
            tmp1RdsNearStrms = files.nameIntermediateFile(metricConst.tmp1RNS,cleanupList)
            # Set a unique name for the undissolved  road/stream buffer intersections with reporting unit IDs attached
            tmp2RdsNearStrms = files.nameIntermediateFile(metricConst.tmp2RNS,cleanupList)
            # Get a unique name for the dissolved road/stream intersections:
            roadsNearStreams = files.nameIntermediateFile(metricConst.roadsNearStreams,cleanupList)
            
            # append the buffer distance to the rns field name base
            distString = bufferDistance.split()[0]
            rnsFieldName = metricConst.rnsFieldName+distString

            vector.roadsNearStreams(inStreamFeature, mergedStreams, bufferDistance, inRoadFeature, inReportingUnitFeature, streamLengthFieldName,uIDField, streamBuffer, 
                                          tmp1RdsNearStrms, tmp2RdsNearStrms, roadsNearStreams, rnsFieldName,metricConst.roadLengthFieldName, roadClassField)
            # Transfer values to final output table.
            AddMsg(timer.split() + " Compiling calculated values into output table")
            fromFields = [rnsFieldName]
            # Transfer the values to the output table, pivoting the class values into new fields if necessary.
            table.transferField(roadsNearStreams,outTable,fromFields,fromFields,uIDField.name,roadClassField,classValues)
    
    except Exception as e:
        errors.standardErrorHandling(e)

    finally:
        if not cleanupList[0] == "KeepIntermediates":
            for (function,arguments) in cleanupList:
                # Flexibly executes any functions added to cleanup array.
                function(*arguments)
        env.workspace = _tempEnvironment1
        env.outputMFlag = _tempEnvironment4
        env.outputZFlag = _tempEnvironment5


def runStreamDensityCalculator(inReportingUnitFeature, reportingUnitIdField, inLineFeature, outTable, lineCategoryField="", 
                               optionalFieldGroups="#"):
    """Interface for script executing Road Density Calculator"""
    from arcpy import env

    cleanupList = [] # This is an empty list object that will contain tuples of the form (function, arguments) as needed for cleanup
    try:
        # Work on making as generic as possible
        ### Initialization
        # Start the timer
        timer = DateTimer()
        AddMsg(timer.start() + " Setting up environment variables")
        # Get the metric constants
        metricConst = metricConstants.sdmConstants()
        # Set the output workspace
        _tempEnvironment1 = env.workspace
        env.workspace = environment.getWorkspaceForIntermediates(globalConstants.scratchGDBFilename, os.path.dirname(outTable))
        _tempEnvironment4 = env.outputMFlag
        _tempEnvironment5 = env.outputZFlag
        # Streams and road crossings script fails in certain circumstances when M (linear referencing dimension) is enabled.
        # Disable for the duration of the tool.
        env.outputMFlag = "Disabled"
        env.outputZFlag = "Disabled"
        # Strip the description from the "additional option" and determine whether intermediates are stored.
        processed = parameters.splitItemsAndStripDescriptions(optionalFieldGroups, globalConstants.descriptionDelim)
        if globalConstants.intermediateName in processed:
            msg = "\nIntermediates are stored in this directory: {0}\n"
            arcpy.AddMessage(msg.format(env.workspace))
            #AddMsg(msg.format(env.workspace))
            cleanupList.append("KeepIntermediates")  # add this string as the first item in the cleanupList to prevent cleanups
        else:
            cleanupList.append((arcpy.AddMessage,("Cleaning up intermediate datasets",)))
        
        # Create a copy of the reporting unit feature class that we can add new fields to for calculations.  This 
        # is more appropriate than altering the user's input data. A dissolve will handle the condition of non-unique id
        # values and will also keep only the OID, shape, and reportingUnitIdField fields
        desc = arcpy.Describe(inReportingUnitFeature)
        tempName = "%s_%s" % (metricConst.shortName, desc.baseName)
        tempReportingUnitFeature = files.nameIntermediateFile([tempName,"FeatureClass"],cleanupList)
        AddMsg(timer.split() + " Creating temporary copy of " + desc.name)
        inReportingUnitFeature = arcpy.Dissolve_management(inReportingUnitFeature, os.path.basename(tempReportingUnitFeature), 
                                                           reportingUnitIdField,"","MULTI_PART")

        # Get the field properties for the unitID, this will be frequently used
        uIDField = settings.processUIDField(inReportingUnitFeature,reportingUnitIdField)

        AddMsg(timer.split() + " Calculating reporting unit area")
        # Add a field to the reporting units to hold the area value in square kilometers
        # Check for existence of field.
        fieldList = arcpy.ListFields(inReportingUnitFeature,metricConst.areaFieldname)
        # Add and populate the area field (or just recalculate if it already exists
        unitArea = vector.addAreaField(inReportingUnitFeature,metricConst.areaFieldname)
        if not fieldList: # if the list of fields that exactly match the validated fieldname is empty...
            if not cleanupList[0] == "KeepIntermediates":
                # ...add this to the list of items to clean up at the end.
                pass
                # *** this was previously necessary when the field was added to the input - now that a copy of the input
                #     is used instead, this is not necessary.
                #cleanupList.append((arcpy.DeleteField_management,(inReportingUnitFeature,unitArea)))

        # If necessary, create a copy of the stream feature class to remove M values.  The env.outputMFlag should work
        # for most datasets except for shapefiles with M and Z values, but doesn't. The Z value will keep the M value 
        # from being stripped off for several data types.
        desc = arcpy.Describe(inLineFeature)
        if desc.HasM or desc.HasZ:
            tempName = "%s_%s" % (metricConst.shortName, desc.baseName)
            tempLineFeature = files.nameIntermediateFile([tempName,"FeatureClass"],cleanupList)
            AddMsg(timer.split() + " Creating temporary copy of " + desc.name)
            inLineFeature = arcpy.FeatureClassToFeatureClass_conversion(inLineFeature, env.workspace, os.path.basename(tempLineFeature))


        AddMsg(timer.split() + " Calculating feature density")
        # Get a unique name for the merged roads and prep for cleanup
        mergedInLines = files.nameIntermediateFile(metricConst.linesByReportingUnitName,cleanupList)

        # Calculate the density of the roads by reporting unit.
        mergedInLines, lineLengthFieldName = calculate.lineDensityCalculator(inLineFeature,inReportingUnitFeature,
                                                                                 uIDField,unitArea,mergedInLines,
                                                                                 metricConst.lineDensityFieldName,
                                                                                 metricConst.lineLengthFieldName,
                                                                                 lineCategoryField)

        # Build and populate final output table.
        AddMsg(timer.split() + " Compiling calculated values into output table")
        arcpy.TableToTable_conversion(inReportingUnitFeature,os.path.dirname(outTable),os.path.basename(outTable))
        # Get a list of unique road class values
        if lineCategoryField:
            categoryValues = fields.getUniqueValues(mergedInLines,lineCategoryField)
        else:
            categoryValues = []
        # Compile a list of fields that will be transferred from the merged roads feature class into the output table
        fromFields = [lineLengthFieldName, metricConst.lineDensityFieldName]
        # Transfer the values to the output table, pivoting the class values into new fields if necessary.
        table.transferField(mergedInLines,outTable,fromFields,fromFields,uIDField.name,lineCategoryField,categoryValues)
        
    except Exception as e:
        errors.standardErrorHandling(e)

    finally:
        if not cleanupList[0] == "KeepIntermediates":
            for (function,arguments) in cleanupList:
                # Flexibly executes any functions added to cleanup array.
                function(*arguments)
        env.workspace = _tempEnvironment1
        env.outputMFlag = _tempEnvironment4
        env.outputZFlag = _tempEnvironment5
        

def runLandCoverDiversity(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, outTable, processingCellSize, 
                          snapRaster, optionalFieldGroups):
    """ Interface for script executing Land Cover Diversity Metrics """

    try:
        class metricLCDCalc:
            """ This class contains the  steps to perform a land cover diversity calculation."""

            # Initialization
            def __init__(self, inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, metricsToRun, outTable, 
                         processingCellSize, snapRaster, optionalFieldGroups, metricConst):
                self.timer = DateTimer()
                AddMsg(self.timer.start() + " Setting up environment variables")
                
                # Run the setup
                self.metricsBaseNameList, self.optionalGroupsList = setupAndRestore.standardSetup(snapRaster, 
                                                                                                  processingCellSize, 
                                                                                                  os.path.dirname(outTable), 
                                                                                                  [metricsToRun,optionalFieldGroups])
                
                # Save other input parameters as class attributes
                self.outTable = outTable
                self.inReportingUnitFeature = inReportingUnitFeature
                self.reportingUnitIdField = reportingUnitIdField
                self.metricConst = metricConst
                self.inLandCoverGrid = inLandCoverGrid

                # If the user has checked the Intermediates option, name the tabulateArea table. This will cause it to be saved.
                self.tableName = None
                self.saveIntermediates = globalConstants.intermediateName in self.optionalGroupsList
                if self.saveIntermediates:
                    self.tableName = metricConst.shortName + globalConstants.tabulateAreaTableAbbv
                    
                
            def _housekeeping(self):
                # alert user if the land cover grid cells are not square (default to size along x axis)
                settings.checkGridCellDimensions(self.inLandCoverGrid)
                # if an OID type field is used for the Id field, create a new field; type integer. Otherwise copy the Id field
                self.outIdField = settings.getIdOutField(self.inReportingUnitFeature, self.reportingUnitIdField)
                # If QAFIELDS option is checked, compile a dictionary with key:value pair of ZoneId:ZoneArea
                self.zoneAreaDict = None
                if globalConstants.qaCheckName in self.optionalGroupsList:
                    # Check to see if an outputGeorgraphicCoordinate system is set in the environments. If one is not specified
                    # return the spatial reference for the land cover grid. Use the returned spatial reference to calculate the
                    # area of the reporting unit's polygon features to store in the zoneAreaDict
                    self.outputSpatialRef = settings.getOutputSpatialReference(self.inLandCoverGrid)
                    self.zoneAreaDict = polygons.getMultiPartIdAreaDict(self.inReportingUnitFeature, self.reportingUnitIdField, self.outputSpatialRef)
                    
            def _makeAttilaOutTable(self):
                AddMsg(self.timer.split() + " Constructing the ATtILA metric output table")
                # Internal function to construct the ATtILA metric output table
                self.newTable, self.metricsFieldnameDict = table.tableWriterNoLcc(self.outTable,
                                                                                        self.metricsBaseNameList,
                                                                                        self.optionalGroupsList,
                                                                                        self.metricConst,
                                                                                        self.outIdField)
                
            def _makeTabAreaTable(self):
                AddMsg(self.timer.split() + " Generating a zonal tabulate area table")
                # Internal function to generate a zonal tabulate area table
                self.tabAreaTable = TabulateAreaTable(self.inReportingUnitFeature, self.reportingUnitIdField,
                                                      self.inLandCoverGrid, self.tableName)
                
            def _calculateMetrics(self):
                AddMsg(self.timer.split() + " Processing the tabulate area table and computing metric values")
                # Internal function to process the tabulate area table and compute metric values. Use values to populate the ATtILA output table
                calculate.landCoverDiversity(self.metricConst, self.outIdField, 
                                                   self.newTable, self.tabAreaTable, self.zoneAreaDict)
                
            # Function to run all the steps in the calculation process
            def run(self):
                # Perform additional housekeeping
                self._housekeeping()
                
                # Make Output Tables
                self._makeAttilaOutTable()
                
                # Generate Tabulation tables
                self._makeTabAreaTable()
                
                # Run final metric calculation
                self._calculateMetrics()
                

        # retrieve the attribute constants associated with this metric
        metricConst = metricConstants.lcdConstants()
        metricsToRun = metricConst.fixedMetricsToRun
        
        lcdCalc = metricLCDCalc(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, metricsToRun, outTable, 
                                processingCellSize, snapRaster, optionalFieldGroups, metricConst)
        lcdCalc.run()

    except Exception as e:
        errors.standardErrorHandling(e)

    finally:
        setupAndRestore.standardRestore()


def runPopulationDensityCalculator(inReportingUnitFeature, reportingUnitIdField, inCensusFeature, inPopField, outTable,
                                   popChangeYN, inCensusFeature2, inPopField2, optionalFieldGroups):
    """ Interface for script executing Population Density Metrics """
    from arcpy import env

    cleanupList = [] # This is an empty list object that will contain tuples of the form (function, arguments) as needed for cleanup
    try:
        ### Initialization
        # Start the timer
        timer = DateTimer()
        AddMsg(timer.start() + " Setting up environment variables")

        # retrieve the attribute constants associated with this metric
        metricConst = metricConstants.pdmConstants()

        # Set the output workspace
        _tempEnvironment1 = env.workspace
        env.workspace = environment.getWorkspaceForIntermediates(globalConstants.scratchGDBFilename, os.path.dirname(outTable))
        # Strip the description from the "additional option" and determine whether intermediates are stored.
        processed = parameters.splitItemsAndStripDescriptions(optionalFieldGroups, globalConstants.descriptionDelim)
        if globalConstants.intermediateName in processed:
            msg = "\nIntermediates are stored in this directory: {0}\n"
            arcpy.AddMessage(msg.format(env.workspace))
            #AddMsg(msg.format(env.workspace))
            cleanupList.append("KeepIntermediates")  # add this string as the first item in the cleanupList to prevent cleanups
        else:
            cleanupList.append((arcpy.AddMessage,("Cleaning up intermediate datasets",)))
        
        # Create a copy of the reporting unit feature class that we can add new fields to for calculations.  This 
        # is more appropriate than altering the user's input data. A dissolve will handle the condition of non-unique id
        # values and will also keep only the OID, shape, and reportingUnitIdField fields
        desc = arcpy.Describe(inReportingUnitFeature)
        tempName = "%s_%s" % (metricConst.shortName, desc.baseName)
        tempReportingUnitFeature = files.nameIntermediateFile([tempName,"FeatureClass"],cleanupList)
        AddMsg(timer.split() + " Creating temporary copy of " + desc.name)
        inReportingUnitFeature = arcpy.Dissolve_management(inReportingUnitFeature, os.path.basename(tempReportingUnitFeature), 
                                                           reportingUnitIdField,"","MULTI_PART")

        # Add and populate the area field (or just recalculate if it already exists
        ruArea = vector.addAreaField(inReportingUnitFeature,metricConst.areaFieldname)
        
        # Build the final output table.
        AddMsg(timer.split() + " Creating output table")
        arcpy.TableToTable_conversion(inReportingUnitFeature,os.path.dirname(outTable),os.path.basename(outTable))
        
        AddMsg(timer.split() + " Calculating population density")
        # Create an index value to keep track of intermediate outputs and fieldnames.
        index = ""
        #if popChangeYN is checked:
        if popChangeYN:
            index = "1"
        # Perform population density calculation for first (only?) population feature class
        calculate.getPopDensity(inReportingUnitFeature,reportingUnitIdField,ruArea,inCensusFeature,inPopField,
                                      env.workspace,outTable,metricConst,cleanupList,index)

        #if popChangeYN is checked:
        if popChangeYN:
            index = "2"
            AddMsg(timer.split() + " Calculating population density for second feature class")
            # Perform population density calculation for second population feature class
            calculate.getPopDensity(inReportingUnitFeature,reportingUnitIdField,ruArea,inCensusFeature2,inPopField2,
                                          env.workspace,outTable,metricConst,cleanupList,index)
            
            AddMsg(timer.split() + " Calculating population change")
            # Set up a calculation expression for population change
            calcExpression = "getPopChange(!popCount_T1!,!popCount_T2!)"
            codeBlock = """def getPopChange(pop1,pop2):
    if pop1 == 0:
        if pop2 == 0:
            return 0
        else:
            return 1
    else:
        return ((pop2-pop1)/pop1)*100"""
            
            # Calculate the population density
            vector.addCalculateField(outTable,metricConst.populationChangeFieldName,calcExpression,codeBlock)       

        AddMsg(timer.split() + " Calculation complete")
    except Exception as e:
        errors.standardErrorHandling(e)

    finally:
        if not cleanupList[0] == "KeepIntermediates":
            for (function,arguments) in cleanupList:
                # Flexibly executes any functions added to cleanup array.
                function(*arguments)
        env.workspace = _tempEnvironment1
        

def runPopulationInFloodplainMetrics(inReportingUnitFeature, reportingUnitIdField, inCensusDataset, inPopField, inFloodplainDataset, 
                                     outTable, optionalFieldGroups):
    """ Interface for script executing Population Density Metrics """
    from arcpy import env

    cleanupList = [] # This is an empty list object that will contain tuples of the form (function, arguments) as needed for cleanup
    try:
        ### Initialization
        # Start the timer
        timer = DateTimer()
        AddMsg(timer.start() + " Setting up environment variables")
        _tempEnvironment0 = env.snapRaster
        _tempEnvironment1 = env.workspace
        _tempEnvironment2 = env.cellSize
        
        # set the workspace for ATtILA intermediary files
        env.workspace = environment.getWorkspaceForIntermediates(globalConstants.scratchGDBFilename, os.path.dirname(outTable))
            
        # Strip the description from the "additional option" and determine whether intermediates are stored.
        processed = parameters.splitItemsAndStripDescriptions(optionalFieldGroups, globalConstants.descriptionDelim)
        if globalConstants.intermediateName in processed:
            msg = "\nIntermediates are stored in this directory: {0}\n"
            arcpy.AddMessage(msg.format(env.workspace))

            cleanupList.append("KeepIntermediates")  # add this string as the first item in the cleanupList to prevent cleanups
        else:
            cleanupList.append((arcpy.AddMessage,("Cleaning up intermediate datasets",)))
        
        # retrieve the attribute constants associated with this metric
        metricConst = metricConstants.pifmConstants()
        popCntFields = metricConst.populationCountFieldNames
            
        # Do a Describe on the population and flood plain inputs. Determine if they are raster or polygon
        descCensus = arcpy.Describe(inCensusDataset)
        descFldpln = arcpy.Describe(inFloodplainDataset)   

        # Create an index value to keep track of intermediate outputs and field names.
        index = 0
        
        # Generate name for reporting unit population count table.
        suffix = metricConst.fieldSuffix[index]
        popTable_RU = files.nameIntermediateFile([metricConst.popCntTableName + suffix,'Dataset'],cleanupList)

        ### Metric Calculation
        AddMsg(timer.split() + " Calculating population within each reporting unit")        
         
        if descCensus.datasetType == "RasterDataset":
            # set the raster environments so the raster operations align with the census grid cell boundaries
            env.snapRaster = inCensusDataset
            env.cellSize = descCensus.meanCellWidth
            
            # calculate the population for the reporting unit using zonal statistics as table
            arcpy.sa.ZonalStatisticsAsTable(inReportingUnitFeature, reportingUnitIdField, inCensusDataset, popTable_RU, "DATA", "SUM")
            
            # Rename the population count field.
            outPopField = metricConst.populationCountFieldNames[index]
            arcpy.AlterField_management(popTable_RU, "SUM", outPopField, outPopField)
            
            # Set variables for the flood plain population calculations
            index = 1
            suffix = metricConst.fieldSuffix[index]
            popTable_FP = files.nameIntermediateFile([metricConst.popCntTableName + suffix,'Dataset'],cleanupList)
            
            if descFldpln.datasetType == "RasterDataset":
                # Use SetNull to eliminate non-flood plain areas and to replace the flood plain cells with values from the 
                # PopulationRaster. The snap raster, and cell size have already been set to match the census raster
                AddMsg(timer.split() + " Setting non-flood plain areas to NULL")
                delimitedVALUE = arcpy.AddFieldDelimiters(inFloodplainDataset,"VALUE")
                whereClause = delimitedVALUE+" = 0"
                inCensusDataset = arcpy.sa.SetNull(inFloodplainDataset, inCensusDataset, whereClause)
                 
            else: # flood plain feature is a polygon
                # Assign the reporting unit ID to intersecting flood plain polygon segments using Identity
                fileNameBase = descFldpln.baseName
                tempName = "%s_%s_%s" % (metricConst.shortName, fileNameBase, "Identity")
                tempPolygonFeature = files.nameIntermediateFile([tempName,"FeatureClass"],cleanupList)
                AddMsg(timer.split() + " Assigning reporting unit IDs to intersecting flood plain features")
                arcpy.Identity_analysis(inFloodplainDataset, inReportingUnitFeature, tempPolygonFeature)
                inReportingUnitFeature = tempPolygonFeature
            
            AddMsg(timer.split() + " Calculating population within flood plain areas for each reporting unit")
            # calculate the population for the reporting unit using zonal statistics as table
            # The snap raster, and cell size have been set to match the census raster
            arcpy.sa.ZonalStatisticsAsTable(inReportingUnitFeature, reportingUnitIdField, inCensusDataset, popTable_FP, "DATA", "SUM")
                
            # Rename the population count field.
            outPopField = metricConst.populationCountFieldNames[index]
            arcpy.AlterField_management(popTable_FP, "SUM", outPopField, outPopField)

        else: # census features are polygons
            # Create a copy of the census feature class that we can add new fields to for calculations.
            fieldMappings = arcpy.FieldMappings()
            fieldMappings.addTable(inCensusDataset)
            [fieldMappings.removeFieldMap(fieldMappings.findFieldMapIndex(aFld.name)) for aFld in fieldMappings.fields if aFld.name != inPopField]
        
            tempName = "%s_%s" % (metricConst.shortName, descCensus.baseName)
            tempCensusFeature = files.nameIntermediateFile([tempName + "_Work","FeatureClass"],cleanupList)
            inCensusDataset = arcpy.FeatureClassToFeatureClass_conversion(inCensusDataset,env.workspace,
                                                                                 os.path.basename(tempCensusFeature),"",
                                                                                 fieldMappings)
            
            # Add a dummy field to the copied census feature class and calculate it to a value of 1.
            classField = "tmpClass"
            arcpy.AddField_management(inCensusDataset,classField,"SHORT")
            arcpy.CalculateField_management(inCensusDataset,classField,1)
            
            # Perform population count calculation for the reporting unit
            calculate.getPolygonPopCount(inReportingUnitFeature,reportingUnitIdField,inCensusDataset,inPopField,
                                      classField,popTable_RU,metricConst,index)
        
            # Set variables for the flood plain population calculations   
            index = 1
            suffix = metricConst.fieldSuffix[index]
            popTable_FP = files.nameIntermediateFile([metricConst.popCntTableName + suffix,'Dataset'],cleanupList)
            
            if descFldpln.datasetType == "RasterDataset":
                # Convert the Raster Flood plain to Polygon
                AddMsg(timer.split() + " Converting flood plain raster to a polygon feature")
                delimitedVALUE = arcpy.AddFieldDelimiters(inFloodplainDataset,"VALUE")
                whereClause = delimitedVALUE+" = 0"
                nullGrid = arcpy.sa.SetNull(inFloodplainDataset, 1, whereClause)
                tempName = "%s_%s" % (metricConst.shortName, descFldpln.baseName + "_Poly")
                tempPolygonFeature = files.nameIntermediateFile([tempName,"FeatureClass"],cleanupList)
                
                # This may fail if a polgyon created is too large. Need a routine to more elegantly reduce the maxVertices in any one polygon
                maxVertices = 250000
                try:
                    inFloodplainDataset = arcpy.RasterToPolygon_conversion(nullGrid,tempPolygonFeature,"NO_SIMPLIFY","VALUE","",maxVertices)
                except:
                    arcpy.AddMessage("Converting raster to polygon with maximum vertices technique")
                    maxVertices = maxVertices / 2
                    inFloodplainDataset = arcpy.RasterToPolygon_conversion(nullGrid,tempPolygonFeature,"NO_SIMPLIFY","VALUE","",maxVertices)
                
            else: # flood plain input is a polygon dataset
                # Create a copy of the flood plain feature class that we can add new fields to for calculations.
                # To reduce operation overhead and disk space, keep only the first field of the flood plain feature
                fieldMappings = arcpy.FieldMappings()
                fieldMappings.addTable(inFloodplainDataset)
                [fieldMappings.removeFieldMap(fieldMappings.findFieldMapIndex(aFld.name)) for aFld in fieldMappings.fields if aFld.name != fieldMappings.fields[0].name]
                
                tempName = "%s_%s" % (metricConst.shortName, descFldpln.baseName)
                tempFldplnFeature = files.nameIntermediateFile([tempName + "_Work","FeatureClass"],cleanupList)
                inFloodplainDataset = arcpy.FeatureClassToFeatureClass_conversion(inFloodplainDataset,env.workspace,
                                                                                     os.path.basename(tempFldplnFeature),"",
                                                                                     fieldMappings)
                
            # Add a field and calculate it to a value of 1. This field will use as the classField in Tabulate Intersection operation below
            classField = "tmpClass"
            arcpy.AddField_management(inFloodplainDataset,classField,"SHORT")
            arcpy.CalculateField_management(inFloodplainDataset,classField,1)

            # intersect the flood plain polygons with the reporting unit polygons
            fileNameBase = descFldpln.baseName
            # need to eliminate the tool's shortName from the fileNameBase if the flood plain polygon was derived from a raster
            fileNameBase = fileNameBase.replace(metricConst.shortName+"_","")
            tempName = "%s_%s_%s" % (metricConst.shortName, fileNameBase, "Identity")
            tempPolygonFeature = files.nameIntermediateFile([tempName,"FeatureClass"],cleanupList)
            AddMsg(timer.split() + " Assigning reporting unit IDs to flood plain features")
            arcpy.Identity_analysis(inFloodplainDataset, inReportingUnitFeature, tempPolygonFeature)
    
            AddMsg(timer.split() + " Calculating population within flood plain areas for each reporting unit")
            # Perform population count calculation for second feature class area
            calculate.getPolygonPopCount(tempPolygonFeature,reportingUnitIdField,inCensusDataset,inPopField,
                                          classField,popTable_FP,metricConst,index)
        
        # Build and populate final output table.
        AddMsg(timer.split() + " Calculating the percent of the population that is within a flood plain")
        
        # Construct a list of fields to retain in the output metrics table
        keepFields = metricConst.populationCountFieldNames
        keepFields.append(reportingUnitIdField)
        fieldMappings = arcpy.FieldMappings()
        fieldMappings.addTable(popTable_RU)
        [fieldMappings.removeFieldMap(fieldMappings.findFieldMapIndex(aFld.name)) for aFld in fieldMappings.fields if aFld.name not in keepFields]

        arcpy.TableToTable_conversion(popTable_RU,os.path.dirname(outTable),os.path.basename(outTable),"",fieldMappings)
        
        # Compile a list of fields that will be transferred from the flood plain population table into the output table
        fromFields = [popCntFields[index]]
        toField = popCntFields[index]
        # Transfer the values to the output table
        table.transferField(popTable_FP,outTable,fromFields,[toField],reportingUnitIdField,None)
        
        # Set up a calculation expression for population change
        calcExpression = "getPopPercent(!"+popCntFields[0]+"!,!"+popCntFields[1]+"!)"
        codeBlock = """def getPopPercent(pop1,pop2):
                            if pop1 == 0:
                                if pop2 == 0:
                                    return 0
                                else:
                                    return 1
                            else:
                                return (pop2/pop1)*100"""
            
        # Calculate the percent population within flood plain
        vector.addCalculateField(outTable,metricConst.populationProportionFieldName,calcExpression,codeBlock)   

        AddMsg(timer.split() + " Calculation complete")
    except Exception as e:
        errors.standardErrorHandling(e)

    finally:
        if not cleanupList[0] == "KeepIntermediates":
            for (function,arguments) in cleanupList:
                # Flexibly executes any functions added to cleanup array.
                function(*arguments)
        env.snapRaster = _tempEnvironment0
        env.workspace = _tempEnvironment1
        env.cellSize = _tempEnvironment2
        

def getProximityPolygons(inLandCoverGrid, _lccName, lccFilePath, metricsToRun,
                          inNeighborhoodSize, burnIn, burnInValue="", minPatchSize="#", 
                          outWorkspace="#", optionalFieldGroups="#"):
    """ Interface for script executing Generate Proximity Polygons utility """
    
    from arcpy.sa import Con,Raster,Reclassify,RegionGroup,RemapValue,RemapRange

    try:
        # retrieve the attribute constants associated with this metric
        metricConst = metricConstants.gppConstants()
        
        ### Initialization
        # Start the timer
        timer = DateTimer()
        AddMsg(timer.start() + " Setting up environment variables")
        processingCellSize = Raster(inLandCoverGrid).meanCellWidth
        snapRaster = inLandCoverGrid
        metricsBaseNameList, optionalGroupsList = setupAndRestore.standardSetup(snapRaster,processingCellSize,outWorkspace,
                                                                               [metricsToRun,optionalFieldGroups] )

        workDir = arcpy.env.workspace
        if (workDir[-4:] == ".gdb"):
            workDir = '\\'.join(workDir.split('\\')[0:-1])
        
        # Process the Land Cover Classification XML
        lccObj = lcc.LandCoverClassification(lccFilePath)
        # get the dictionary with the LCC CLASSES attributes
        lccClassesDict = lccObj.classes
        # Get the lccObj values dictionary. This contains all the properties of each value specified in the Land Cover Classification XML    
        lccValuesDict = lccObj.values
        # create a list of all the grid values in the selected land cover grid
        landCoverValues = raster.getRasterValues(inLandCoverGrid)
        # get the frozenset of excluded values (i.e., values marked as EXCLUDED in the Land Cover Classification XML)
        excludedValuesList = lccValuesDict.getExcludedValueIds().intersection(landCoverValues)
        
        # alert user if the LCC XML document has any values within a class definition that are also tagged as 'excluded' in the values node.
        settings.checkExcludedValuesInClass(metricsBaseNameList, lccObj, lccClassesDict)
        # alert user if the land cover grid has values undefined in the LCC XML file
        settings.checkGridValuesInLCC(inLandCoverGrid, lccObj)
        # alert user if the land cover grid cells are not square (default to size along x axis)
        settings.checkGridCellDimensions(inLandCoverGrid)
        
        # Determine if the user wants to save the intermediate products
        saveIntermediates = globalConstants.intermediateName in optionalGroupsList
        
        # determine the active map to add the output raster/features    
        currentProject = arcpy.mp.ArcGISProject("CURRENT")
        actvMap = currentProject.activeMap

        ### Computations
        
        # Check if the input land cover raster is too large to produce the output polygon feature without splitting it first
        splitRaster = True
        columns = arcpy.GetRasterProperties_management(inLandCoverGrid, 'COLUMNCOUNT').getOutput(0)
        xsplit = int(float(columns) / 40000) + 1 #original value is 40000, 500 is to test the very small raster data, 20000 is to test FCA_MULC.tif
        rows = arcpy.GetRasterProperties_management(inLandCoverGrid, 'ROWCOUNT').getOutput(0)
        ysplit = int (float(rows) / 40000) + 1
        
        if xsplit*ysplit == 1:
            splitRaster = False
        
        if splitRaster != False:
            xy = (xsplit * ysplit)
            for Chunk in range(0,xy):
                try:
                    arcpy.Delete_management(workDir + '/prox_' + str(Chunk))
                except:
                    pass  

        # Determine the maximum sum for the neighborhood
        Sum100 = pow(int(inNeighborhoodSize), 2)
        
        # Set up break points to reclass proximity grid into 20% classes
        reclassBins = raster.getRemapBinsByPercentStep(Sum100, 20)
        rngRemap = RemapRange(reclassBins)
        
        # If necessary, generate a grid of excluded areas (e.g., water bodies) to be burnt into the proximity grid 
        # This only needs to be done once regardless of the number of requested class proximity outputs  
        if burnIn == "true":
            
            if len(excludedValuesList) == 0:
                AddMsg("No excluded values in selected Land Cover Classification file. No BURN IN areas will be processed.")
                burnInGrid = None
            else:
                AddMsg("Processing BURN IN areas...")
                # create class (value = 1) / other (value = 3) / excluded grid (value = 2) raster
                # define the reclass values
                classValue = 0
                excludedValue = 1
                otherValue = 0
                newValuesList = [classValue, excludedValue, otherValue]
                
                # generate a reclass list where each item in the list is a two item list: the original grid value, and the reclass value
                classValuesList = []
                reclassPairs = raster.getInOutOtherReclassPairs(landCoverValues, classValuesList, excludedValuesList, newValuesList)
        
                AddMsg(("{0} Reclassing excluded values in land cover to 1. All other values = 0...").format(timer.split()))
                excludedBinary = Reclassify(inLandCoverGrid,"VALUE", RemapValue(reclassPairs))
                
                AddMsg(("{0} Calculating size of excluded area patches...").format(timer.split()))
                regionGrid = RegionGroup(excludedBinary,"EIGHT","WITHIN","ADD_LINK")
                
                AddMsg(("{0} Assigning {1} to patches >= minimum size threshold...").format(timer.split(), burnInValue))
                delimitedCOUNT = arcpy.AddFieldDelimiters(regionGrid,"COUNT")
                whereClause = delimitedCOUNT+" >= " + minPatchSize + " AND LINK = 1"
                burnInGrid = Con(regionGrid, int(burnInValue), 0, whereClause)
                
                # save the intermediate raster if save intermediates option has been chosen
                if saveIntermediates: 
                    namePrefix = metricConst.burnInGridName
                    scratchName = arcpy.CreateScratchName(namePrefix, "", "RasterDataset")
                    burnInGrid.save(scratchName)
                    AddMsg(timer.split() + " Save intermediate grid complete: "+os.path.basename(scratchName))
                    AddMsg(timer.split() + " before time delay, burnInGrid.catalogPath:" +  burnInGrid.catalogPath)
                    time.sleep(10)
                    AddMsg(timer.split() + " after time delay, burnInGrid.catalogPath:" +  burnInGrid.catalogPath)  
        # Run metric calculate for each metric in list
        for m in metricsBaseNameList:
            # get the grid codes for this specified metric
            classValuesList = lccClassesDict[m].uniqueValueIds.intersection(landCoverValues)

            # process the inLandCoverGrid for the selected class
            AddMsg(("Processing {0} proximity grid...").format(m.upper()))
            
            proximityGrid = raster.getProximityWithBurnInGrid(classValuesList, excludedValuesList, inLandCoverGrid, landCoverValues, 
                                                    inNeighborhoodSize, burnIn, burnInGrid, timer, rngRemap)

            # save the intermediate raster if save intermediates option has been chosen 
            if saveIntermediates:
                namePrefix = m.upper()+"_ProxRaster"
                scratchName = arcpy.CreateScratchName(namePrefix, "", "RasterDataset")
                proximityGrid.save(scratchName)
                AddMsg(timer.split() + " Save intermediate grid complete: "+os.path.basename(scratchName))
                AddMsg(timer.split() + " before time delay, proximityGrid.catalogPath:" +  proximityGrid.catalogPath)
                time.sleep(100)
                AddMsg(timer.split() + " after time delay, proximityGrid.catalogPath:" +  proximityGrid.catalogPath)                              
            # convert proximity raster to polygon
            AddMsg(timer.split() + " Converting proximity raster to a polygon feature")
            
            # Split the Raster As Needs, Process Each Piece
            if splitRaster == False:
                AddMsg(("xsplit = {0} and ysplit = {1}").format(xsplit, ysplit))
                #arcpy.conversion.RasterToPolygon(proximityGrid,"tempPoly","NO_SIMPLIFY","Value","SINGLE_OUTER_PART",None)
                if saveIntermediates:
                    arcpy.conversion.RasterToPolygon(proximityGrid.catalogPath,"tempPoly","NO_SIMPLIFY","Value","SINGLE_OUTER_PART",None)
                else:
                    arcpy.conversion.RasterToPolygon(proximityGrid,"tempPoly","NO_SIMPLIFY","Value","SINGLE_OUTER_PART",None)
            else:
                xy = (xsplit * ysplit)

                AddMsg(timer.split() + " Spliting the raster into pieces of no more than 40,000x40,000 pixels")

                AddMsg(timer.split() + " before time delay, proximityGrid.catalogPath:" +  proximityGrid.catalogPath)
                time.sleep(200)
                AddMsg(timer.split() + " after time delay, proximityGrid.catalogPath:" +  proximityGrid.catalogPath)
                if saveIntermediates:
                    arcpy.SplitRaster_management(proximityGrid.catalogPath, workDir, 'prox_', 'NUMBER_OF_TILES', 'GRID', '', str(xsplit) + ' ' + str(ysplit))
                else:
                    arcpy.SplitRaster_management(proximityGrid, workDir, 'prox_', 'NUMBER_OF_TILES', 'GRID', '', str(xsplit) + ' ' + str(ysplit))
                AddMsg(timer.split() + " finish Spliting the raster into pieces of no more than 40,000x40,000 pixels")
    
                """ For each raster: """
                for Chunk in range(0,xy):
                    try:
                        result = float(arcpy.GetRasterProperties_management(workDir + '/prox_' + str(Chunk), 'MEAN').getOutput(0))
                        # If the raster piece has data:
                        if (result != 0):
                            #""" Convert Raster to Polygon """
                            #arcpy.RasterToPolygon_conversion('prox_' + str(Chunk), 'tempPoly_' + str(Chunk), 'NO_SIMPLIFY')
                            arcpy.RasterToPolygon_conversion(workDir + '/prox_' + str(Chunk), 'tempPoly_' + str(Chunk), 'NO_SIMPLIFY')

                            #""" Dissolve the polygons """
                            arcpy.Dissolve_management('tempPoly_' + str(Chunk), 'proxD1_' + str(Chunk), 'gridcode')
                            AddMsg(timer.split() + " Processed Chunk " + str(Chunk) + " / " + str(xy))
                        else:
                            pass
                    except:
                        pass
      
                """ Merge the polygons back together """
                fcList = arcpy.ListFeatureClasses('proxD1*')
                #polygonFeature = arcpy.Merge_management(fcList, 'proxDiss')
                arcpy.Merge_management(fcList,"tempPoly")
        
            # get output name for dissolve
            namePrefix = m.upper()+metricConst.proxPolygonOutputName
            proxPolygonName = arcpy.CreateScratchName(namePrefix, "", "FeatureDataset")
            #arcpy.Dissolve_management(polygonFeature,proxPolygonName,"gridcode")
            arcpy.Dissolve_management("tempPoly",proxPolygonName,"gridcode")
            
            classFieldName = m.capitalize()+metricConst.fieldSuffix
            arcpy.AlterField_management(proxPolygonName,"gridcode", classFieldName, classFieldName)
            
            arcpy.Delete_management("tempPoly")

            if splitRaster != False:
                xy = (xsplit * ysplit)
                for Chunk in range(0,xy):
                    try:
                        arcpy.Delete_management(workDir + '/prox_' + str(Chunk))
                    except:
                        pass  
            
            # add the dissolved proximity polygon to the active map
            if actvMap != None:
                actvMap.addDataFromPath(proxPolygonName)
                AddMsg(("Adding {0} to {1} view").format(os.path.basename(proxPolygonName), actvMap.name))


    except Exception as e:
        errors.standardErrorHandling(e)

    finally:
        setupAndRestore.standardRestore()


def runPopulationLandCoverViews(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, _lccName, lccFilePath,
                    metricsToRun, viewRadius, minPatchSize="", inCensusRaster="", outTable="", processingCellSize="", 
                    snapRaster="", optionalFieldGroups=""):
    """ Interface for script executing Population With Potential Views Metrics """
    try:
       
        ''' Initialization Steps '''
        from arcpy import env
        timer = DateTimer()
        AddMsg(timer.start() + " Setting up environment variables")
         
        metricsBaseNameList, optionalGroupsList = setupAndRestore.standardSetup(snapRaster, processingCellSize,
                                                                                os.path.dirname(outTable),
                                                                                [metricsToRun,optionalFieldGroups] )
 
        # XML Land Cover Coding file loaded into memory
        lccObj = lcc.LandCoverClassification(lccFilePath)
        # get the dictionary with the LCC CLASSES attributes
        lccClassesDict = lccObj.classes
        # Get the lccObj values dictionary. This contains all the properties of each value specified in the Land Cover Classification XML    
        lccValuesDict = lccObj.values
        # create a list of all the grid values in the selected land cover grid
        landCoverValues = raster.getRasterValues(inLandCoverGrid)
        # get the frozenset of excluded values (i.e., values marked as EXCLUDED in the Land Cover Classification XML)
        excludedValuesList = lccValuesDict.getExcludedValueIds().intersection(landCoverValues)
         
        # retrieve the attribute constants associated with this metric
        metricConst = metricConstants.plcvConstants()

        # append the view radius distance value to the field suffix
        newSuffix = metricConst.fieldSuffix + viewRadius
        metricConst.fieldParameters[1] = newSuffix
        # for the output fields, add the input view radius to the field suffix
        for i, fldParams in enumerate(metricConst.additionalFields):
            fldParams[1] = metricConst.additionalSuffixes[i] + viewRadius
         
         
        ''' Housekeeping Steps ''' 
        # alert user if the LCC XML document has any values within a class definition that are also tagged as 'excluded' in the values node.
        settings.checkExcludedValuesInClass(metricsBaseNameList, lccObj, lccClassesDict)
        # alert user if the land cover grid has values undefined in the LCC XML file
        settings.checkGridValuesInLCC(inLandCoverGrid, lccObj)
        # alert user if the land cover grid cells are not square (default to size along x axis)
        settings.checkGridCellDimensions(inLandCoverGrid)
        # if an OID type field is used for the Id field, create a new field; type integer. Otherwise copy the Id field
        outIdField = settings.getIdOutField(inReportingUnitFeature, reportingUnitIdField)
         
        # Determine if the user wants to save the intermediate products
        saveIntermediates = globalConstants.intermediateName in optionalGroupsList

 
        # Initiate our flexible cleanuplist
        cleanupList = []
        if saveIntermediates:
            cleanupList.append("KeepIntermediates")  # add this string as the first item in the cleanupList to prevent cleanups
        else:
            cleanupList.append((arcpy.AddMessage,("Cleaning up intermediate datasets",)))
             
        # Check if the input land cover raster is too large to produce the output polygon feature without splitting it first
        maxSide = 40000
        splitYN, xySplits = raster.splitRasterYN(inLandCoverGrid, maxSide)
 
 
        ''' Make ATtILA Output Table '''
        #Create the output table outside of metricCalc so that result can be added for multiple metrics
        newtable, metricsFieldnameDict = table.tableWriterByClass(outTable, metricsBaseNameList,optionalGroupsList, 
                                                                                  metricConst, lccObj, outIdField, 
                                                                                  metricConst.additionalFields)
  
         
        ''' Metric Computations '''
 
        # Generate table with population counts by reporting unit
        AddMsg(timer.split() + " Calculating population within each reporting unit") 
        index = 0

        populationTable, populationField = table.createPolygonValueCountTable(inReportingUnitFeature,
                                                                              reportingUnitIdField,
                                                                              inCensusRaster,
                                                                              "",
                                                                              newtable,
                                                                              metricConst,
                                                                              index,
                                                                              cleanupList)
        
        # Eliminate unnecessary fields from the population table
        fields.deleteFields(populationTable, ["ZONE_CODE", "COUNT", "AREA"])
        
        # Set up list for the viewGrid Con operation. First value is the where clause value, the second is the true constant 
        conValues = [0,1]
        
        # Determine if a transformation method is needed to project datasets (e.g. different datums are used). 
        transformMethod = conversion.getTransformMethod(inLandCoverGrid, inCensusRaster)
        descCensus = arcpy.Describe(inCensusRaster)
        spatialCensus = descCensus.spatialReference
 
        # Run metric calculate for each metric in list
        for m in metricsBaseNameList:
            # get the grid codes for this specified metric
            classValuesList = lccClassesDict[m].uniqueValueIds.intersection(landCoverValues)
            
            # process the inLandCoverGrid for the selected class
            AddMsg(("Determining population with minimal views of {} class...").format(m.upper()))  
            viewGrid = raster.getLargePatchViewGrid(classValuesList, excludedValuesList, inLandCoverGrid, landCoverValues, 
                                          viewRadius, conValues, minPatchSize, timer, saveIntermediates, metricConst)
  
            # save the intermediate raster if save intermediates option has been chosen 
            if saveIntermediates:
                namePrefix = m.upper()+metricConst.viewRasterOutputName
                scratchName = arcpy.CreateScratchName(namePrefix, "", "RasterDataset")
                viewGrid.save(scratchName)
                AddMsg(timer.split() + " Save intermediate grid complete: "+os.path.basename(scratchName))
                             
            # convert proximity raster to polygon
            AddMsg(timer.split() + " Converting view raster to a polygon feature")
            # get output name for projected viewPolygon
            namePrefix = m.upper()+metricConst.viewPolygonOutputName
            viewPolygonFeature = files.nameIntermediateFile([namePrefix + "","FeatureClass"],cleanupList)
            
            # Split the Raster As Needs, Process Each Piece
            if splitYN == False:
                if transformMethod != "":
                    arcpy.conversion.RasterToPolygon(viewGrid,"tempPoly","NO_SIMPLIFY","Value","SINGLE_OUTER_PART",None)
                    arcpy.Project_management("tempPoly",viewPolygonFeature,spatialCensus,transformMethod)
                    arcpy.Delete_management("tempPoly")
                else:
                    arcpy.conversion.RasterToPolygon(viewGrid,viewPolygonFeature,"NO_SIMPLIFY","Value","SINGLE_OUTER_PART",None)
            else:
                xsplit = xySplits[0]
                ysplit = xySplits[1]
                xy = (xsplit * ysplit)
                workDir = arcpy.env.workspace
                AddMsg(("{0} Splitting the raster into pieces of no more than {1} x {1} pixels").format(timer.split(),maxSide))
                arcpy.SplitRaster_management(viewGrid, workDir, 'prox_', 'NUMBER_OF_TILES', 'GRID', '', str(xsplit) + ' ' + str(ysplit))
     
                """ For each raster: """
                for Chunk in range(0,xy):
                    try:
                        result = float(arcpy.GetRasterProperties_management(workDir + '/prox_' + str(Chunk), 'MEAN').getOutput(0))
                        # If the raster piece has data:
                        if (result != 0):
                            """ Convert Raster to Polygon """
                            arcpy.RasterToPolygon_conversion('prox_' + str(Chunk), 'tempPoly_' + str(Chunk), 'NO_SIMPLIFY')
 
                            """ Dissolve the polygons """
                            arcpy.Dissolve_management('prox_' + str(Chunk), 'proxD1_' + str(Chunk), 'gridcode')
                            AddMsg(timer.split() + " Processed Chunk " + str(Chunk) + " / " + str(xy))
                        else:
                            pass
                    except:
                        pass
       
                """ Merge the polygons back together """
                fcList = arcpy.ListFeatureClasses('proxD1*')
                

                # Check if viewPolygon is the same projection as the census raster, if not project it
                if transformMethod != "":
                    arcpy.Merge_management(fcList,"tempPoly")
                    arcpy.Project_management("tempPoly",viewPolygonFeature,spatialCensus,transformMethod)
                    arcpy.Delete_management("tempPoly")
                else:
                    arcpy.Merge_management(fcList, viewPolygonFeature)

            # Extract Census pixels which are in the non-view area
            AddMsg(("{} Extracting population pixels within the minimal view area...").format(timer.split())) 
            
            # Save the current environment settings, then set to match the census raster 
            tempEnvironment0 = env.snapRaster
            tempEnvironment1 = env.cellSize            
            env.snapRaster = inCensusRaster
            env.cellSize = descCensus.meanCellWidth
            
            viewPopGrid = arcpy.sa.ExtractByMask(inCensusRaster, viewPolygonFeature)
            
            # save the intermediate raster if save intermediates option has been chosen 
            if saveIntermediates:
                namePrefix = m.upper()+metricConst.areaPopRasterOutputName
                scratchName = arcpy.CreateScratchName(namePrefix, "", "RasterDataset")
                viewPopGrid.save(scratchName)
                AddMsg(timer.split() + " Save intermediate grid complete: "+os.path.basename(scratchName))
                
            # Calculate the extracted population for each reporting unit
            AddMsg(timer.split() + " Calculating population within minimal-view areas for each reporting unit")
            namePrefix = m.upper()+metricConst.areaValueCountTableName
            areaPopTable = files.nameIntermediateFile([namePrefix + "","FeatureClass"],cleanupList)
            arcpy.sa.ZonalStatisticsAsTable(inReportingUnitFeature,reportingUnitIdField,viewPopGrid,areaPopTable,"DATA","SUM")
            
            # reset the environments
            env.snapRaster = tempEnvironment0
            env.cellSize = tempEnvironment1
            
            # get the field that will be transferred from the view population table into the output table
            fromField = "SUM"
            toField = metricsFieldnameDict[m][0] #generated metric field name for the current land cover class
            
            # Transfer the fromField values to the output table
            table.addJoinCalculateField(areaPopTable, populationTable, fromField, toField, reportingUnitIdField)
            
            # Assign 0 to reporting units where no population was calculated in the view/non-view area
            calculate.replaceNullValues(populationTable, toField, metricConst.valueWhenNULL)

            # Replace the inField name suffix to identify the calcField     
            calcField = toField.replace(metricConst.fieldSuffix,metricConst.pctSuffix)
            
            # Calculate the percent population within view area
            calculate.percentageValue(populationTable, toField, populationField, calcField)

            # Calculate the population for minimum view
            calcField_WOVPOP = toField.replace(metricConst.fieldSuffix,metricConst.wovFieldSuffix)
            calculate.differenceValue(populationTable, populationField, toField, calcField_WOVPOP)

            # Calculate the percent population without view area
            calcField_WOVPCT = calcField_WOVPOP.replace(metricConst.wovFieldSuffix,metricConst.wovPctSuffix)
            calculate.percentageValue(populationTable, calcField_WOVPOP, populationField, calcField_WOVPCT)
            AddMsg(timer.split() + " Calculation complete")
           
 
    except Exception as e:
        errors.standardErrorHandling(e)
 
    finally:
        setupAndRestore.standardRestore()
        if not cleanupList[0] == "KeepIntermediates":
            for (function,arguments) in cleanupList:
                # Flexibly executes any functions added to cleanup array.
                function(*arguments)

                

def runFacilityLandCoverViews(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, _lccName, lccFilePath,
                     metricsToRun, inFacilityFeature, viewRadius, viewThreshold, outTable="", processingCellSize="", 
                     snapRaster="", optionalFieldGroups=""):
    #""" Interface for script executing Facility Land Cover Views Metrics """
    try:

        metricConst = metricConstants.flcvConstants()

        intermediateList = []

        #make a temporary facility point layer so that the field of the same name as reportingUnitIdField could be deleted
        inPointFacilityFeature = arcpy.FeatureClassToFeatureClass_conversion(inFacilityFeature, arcpy.env.workspace, metricConst.lcpPointLayer)

        intermediateList.append(inPointFacilityFeature)

        arcpy.DeleteField_management(inPointFacilityFeature, reportingUnitIdField)
        intermediateList.append(inPointFacilityFeature)

        intersectResult = arcpy.Intersect_analysis([inPointFacilityFeature,inReportingUnitFeature],metricConst.facilityOutputName,"NO_FID","","POINT")
        fieldObjList = arcpy.ListFields(intersectResult)
        intermediateList.append(intersectResult)

        # Create an empty list that will be populated with field names to be deleted      
        fieldNameList = []

        for field in fieldObjList:
            currentField = field.name.upper()
            if ((currentField != "OBJECTID") and (currentField != "SHAPE") and (currentField != reportingUnitIdField.upper())):
                fieldNameList.append(field.name)

        # Execute DeleteField to delete all fields in the field list. 
        arcpy.DeleteField_management(intersectResult, fieldNameList)


        bufferResult = arcpy.Buffer_analysis(intersectResult,metricConst.bufferOutputName,viewRadius,"","","NONE","", "PLANAR")
        intermediateList.append(bufferResult)
        runLandCoverProportions(bufferResult, "ORIG_FID", inLandCoverGrid, _lccName, lccFilePath,
                            metricsToRun, metricConst.lcpTableName, "30", inLandCoverGrid, 
                            "AREAFIELDS  -  Add Area Fields for All Land Cover Classes';'QAFIELDS  -  Add Quality Assurance Fields")# 30 if for processing cell size
        
        metricsArray = metricsToRun.split("';'")
    
        
        for currentMetrics in metricsArray:
            metricsShorName = currentMetrics.split(globalConstants.descriptionDelim)[0]
            calculate.belowValue(metricConst.lcpTableName, "p" + metricsShorName, viewThreshold, metricsShorName + metricConst.thresholdFieldSuffix)
        
        #table.addJoinCalculateField(metricConst.facilityOutputName, metricConst.lcpTableName, reportingUnitIdField, reportingUnitIdField, reportingUnitIdField)
        tableWithRUID = arcpy.AddJoin_management(metricConst.lcpTableName, "ORIG_FID", metricConst.facilityOutputName, "OBJECTID", "KEEP_ALL")
        arcpy.TableToTable_conversion(tableWithRUID, os.path.dirname(outTable), metricConst.lcpTableWithRUID)
        intermediateList.append(metricConst.lcpTableName)
        intermediateList.append(tableWithRUID)
        intermediateList.append(metricConst.lcpTableWithRUID)

        stats = []
        for currentMetrics in metricsArray:
            metricsShorName = currentMetrics.split(globalConstants.descriptionDelim)[0]
            stats.append([metricsShorName + metricConst.thresholdFieldSuffix, "Sum"])

        arcpy.Statistics_analysis(metricConst.lcpTableWithRUID, outTable, stats, reportingUnitIdField)

        #Rename the fields in the result table
        arcpy.AlterField_management(outTable, "FREQUENCY", "fCnt", "fCnt")
        
        for currentMetrics in metricsArray:
            metricsShorName = currentMetrics.split(globalConstants.descriptionDelim)[0]
            oldFieldName = "SUM_" + metricsShorName + metricConst.thresholdFieldSuffix
            newFieldName = metricsShorName + metricConst.fieldSuffix
            arcpy.AlterField_management(outTable, oldFieldName, newFieldName, newFieldName)

    except Exception as e:
        errors.standardErrorHandling(e)
 
    finally:
        setupAndRestore.standardRestore()
        if not globalConstants.intermediateName in optionalFieldGroups:
            for (intermediateResult) in intermediateList:
                arcpy.Delete_management(intermediateResult)


# def getIntersectionDensityRaster(inLineFeature, mergeLines, mergeField="#", mergeDistance='#', outWorkspace="#",
#                                  cellSize, searchRadius, areaUnits, optionalFieldGroups="#"):
#     """ Interface for script executing Generate Intersection Density Raster utility """