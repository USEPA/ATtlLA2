''' These classes are for inheritance by ToolValidator classes

    These classes shouldn't be used directly as ToolValidators.
    Create a new ToolValidator class that inherits one of these classes.
'''

import arcpy
import os
from xml.dom.minidom import parse
from glob import glob 
import __main__
from ATtILA2.constants import globalConstants
from ATtILA2.constants import validatorConstants
import pylet.lcc.constants as lccConstants
from pylet.lcc import LandCoverClassification, LandCoverCoefficient
    
class ProportionsValidator(object):
    """ Class for inheritance by ToolValidator Only
    
        This currently serves the following tools:
            Land Cover on Slope Proportions
            Land Cover Proportions
    

        
        Description of ArcToolbox parameters:
        -------------------------------------
        
        inTableIndex:  Two consecutive parameters
        1. Table(reporting units)
        2. Field(dropdown):  Obtained from="<Table>"
           
        inRasterIndex:  One parameter
        1. Raster Layer
        
        startIndex:  Three consecutive parameters 
        1. String: default  
        2. File: filter=lccFileExtension
        3. String:  MultiValue=Yes; 
        
        outTableIndex: Index of output table parameter
        1. table: required, output
        
        processingCellSizeIndex:  Index of optional processing cell size parameter
        1. Analysis cell size
        
        snapRasterIndex:  Index of optional snap raster parameter
        1. Raster Layer
        
        optionalFieldsIndex:  index of optional fields parameter
        1. String: Properties: MultiValue=Yes
        
    
    """
    
    # Indexes of input parameters
    inTableIndex = 0 
    inRasterIndex = 0  
    startIndex = 0  
    processingCellSizeIndex = 0
    outTableIndex = 0 
    snapRasterIndex = 0 
    optionalFieldsIndex = 0 
    
    # Indexes of secondary input parameters
    inRaster2Index = 0
    inRaster3Index = 0
    inMultiFeatureIndex = 0
    inVector2Index = 0
    inDistanceIndex = 0
        
    # Additional local variables
    srcDirName = validatorConstants.tbxSourceFolderName
    
    # Metric Specific
    filterList = []
    overrideAttributeName = ""
    fieldPrefix = ""
    fieldSuffix = ""
    metricShortName = ""
    
    def __init__(self):
        """ ESRI - Initialize ToolValidator class"""
        
        # Load metric constants        
        self.inputIdFieldTypes = validatorConstants.inputIdFieldTypes
        self.lccSchemeUserOption = validatorConstants.userOption
        self.metricAddDescription = globalConstants.metricAddDescription      
        self.metricDescription = validatorConstants.metricDescription
        self.noFeaturesMessage = validatorConstants.noFeaturesMessage
        self.noSpatialReferenceMessage = validatorConstants.noSpatialReferenceMessage
        self.noSpatialReferenceMessageMulti = validatorConstants.noSpatialReferenceMessageMulti
        self.nonIntegerGridMessage = validatorConstants.nonIntegerGridMessage
        self.nonPositiveNumberMessage = validatorConstants.nonPositiveNumberMessage
        
        # Load global constants
        self.optionalFieldsName = validatorConstants.optionalFieldsName
        self.qaCheckDescription = globalConstants.qaCheckDescription

        
        # Load LCC constants
        self.lccFileDirName = lccConstants.PredefinedFileDirName       
        self.lccFileExtension = lccConstants.XmlFileExtension
        self.idAttributeName = lccConstants.XmlAttributeId
        self.nameAttributeName = lccConstants.XmlAttributeName
        self.classElementName = lccConstants.XmlElementClass
        self.filterAttributeName = lccConstants.XmlAttributeFilter
        
        # Set relative indexes
        self.lccFilePathIndex = self.startIndex + 1
        self.lccClassesIndex = self.startIndex + 2
        self.inputFieldsIndex = self.inTableIndex + 1
        
        # Assign parameters to local variables
        self.parameters = arcpy.GetParameterInfo()
        self.inputTableParameter = self.parameters[self.inTableIndex]
        self.inputFieldsParameter = self.parameters[self.inputFieldsIndex]
        self.lccSchemeParameter =  self.parameters[self.startIndex]
        self.lccFilePathParameter = self.parameters[self.lccFilePathIndex]
        self.lccClassesParameter = self.parameters[self.lccClassesIndex]
        self.processingCellSizeParameter = self.parameters[self.processingCellSizeIndex]
        self.inRasterParameter = self.parameters[self.inRasterIndex]
        self.outTableParameter = self.parameters[self.outTableIndex]
        self.snapRasterParameter = self.parameters[self.snapRasterIndex]
        self.optionsParameter = self.parameters[self.optionalFieldsIndex]
        
        # Assign secondary input parameters to local variables
        if self.inRaster2Index:
            self.inRaster2Parameter = self.parameters[self.inRaster2Index]
            
        if self.inMultiFeatureIndex:
            self.inMultiFeatureParameter = self.parameters[self.inMultiFeatureIndex]
            
        if self.inVector2Index:
            self.inVector2Parameter = self.parameters[self.inVector2Index]
            
        if self.inDistanceIndex:
            self.inDistanceParameter = self.parameters[self.inDistanceIndex]

               
        # Additional local variables
        self.currentFilePath = ""
        self.ruFilePath = ""
        self.initialized = False


    def initializeParameters(self):
        """ ESRI - Initialize parameters"""
        absPath = os.path.dirname(os.path.abspath(getattr(__main__,'__file__','__main__.py')));

        # Populate predefined LCC dropdown
        #parentDir = os.path.dirname( absPath.split("#")[0])
        parentDir = absPath
      
        self.srcDirPath = os.path.join(parentDir, self.srcDirName, )
        self.lccFileDirSearch = os.path.join(self.srcDirPath, self.lccFileDirName, "*" + self.lccFileExtension)
        
        filterList = []
        self.lccLookup = {}
                
        for lccPath in glob(self.lccFileDirSearch):
            lccSchemeName = os.path.basename(lccPath).rstrip(self.lccFileExtension)
            filterList.append(lccSchemeName)
            self.lccLookup[lccSchemeName] = lccPath
            
        self.lccSchemeParameter.filter.list = filterList + [self.lccSchemeUserOption]
        self.lccFilePathParameter.enabled = False
        self.lccClassesParameter.enabled = False
                
        # Move parameters to optional section
        self.optionsParameter.category = self.optionalFieldsName
        
        # Set options filter
        self.optionsParameter.filter.list = self.filterList
        
        self.initialized = True
        
        
    def updateParameters(self):
        """ ESRI - Modify the values and properties of parameters before internal validation is performed.  
        
            This method is called whenever a parameter has been changed.
        
        """
        
        if not self.initialized:
            self.initializeParameters()

        self.updateInputLccParameters()
        self.updateInputFieldsParameter()
        self.updateOutputTableParameter()


    def updateOutputTableParameter(self):
        """ Update an output table parameter
        
        **Description:**
            
            Removes .shp that is automatically generated for output table parameters and replaces it with .dbf
        
        """
       
        if self.outTableParameter.value:
            outTablePath = str(self.outTableParameter.value)
            self.outTableParameter.value  = outTablePath.replace('.shp', '.dbf')

    
    def updateInputLccParameters(self):
        """ Update Land Cover Classification Parameters 
        
            These parameters include LCC file path and list of classes with checkboxes.
        
        """
        
        # Converts None to "None", so must do a check
        lccSchemeName = ""
        if self.lccSchemeParameter.value:
            lccSchemeName = str(self.lccSchemeParameter.value)

        # User defined LCC Scheme
        lccFilePath = ""
        if  lccSchemeName == self.lccSchemeUserOption:
            lccFilePath = str(self.lccFilePathParameter.value)      
            self.lccFilePathParameter.enabled = True
            
        # Pre-defined  LCC Scheme  
        elif lccSchemeName:
            lccFilePath = self.lccLookup[lccSchemeName]
            
            # Delete user defined file path in dialog
            self.lccFilePathParameter.value = lccFilePath
            self.lccFilePathParameter.enabled = False

        
        # Get list of LCC names with description
        classNames = []
        if lccFilePath and self.currentFilePath != lccFilePath and os.path.isfile(lccFilePath):
            self.currentFilePath = lccFilePath
            classNames = self.getLccList(lccFilePath)
  
        # Populate checkboxes with LCC name and description
        if classNames:
            self.lccClassesParameter.enabled = True
        else:
            self.lccClassesParameter.enabled = False  
            self.lccClassesParameter.value = ""
        
        # Prevent the changing of the classification scheme from causing dialog errors when metrics are already checked    
        if not self.lccSchemeParameter.hasBeenValidated:
            self.lccClassesParameter.value = ""
            
        self.lccClassesParameter.filter.list = classNames
        
        
    def getLccList(self, lccFilePath):
        classNames = []
        lccDocument = parse(lccFilePath)
        classNodes = lccDocument.getElementsByTagName(self.classElementName)
        

        message = self.metricDescription
        for classNode in classNodes:
            
            # ignore class without value as descendant(child, child of child, etc.)
            if not classNode.getElementsByTagName(lccConstants.XmlElementValue):
                continue
            
            # Check filter, skip class if short metric name found (semi-colon delimiter)
            filterValue = classNode.getAttribute(self.filterAttributeName)
            shortNames = filterValue.split(";")
            if self.metricShortName in shortNames:
                continue
            
            classId = classNode.getAttribute(self.idAttributeName)
            name = classNode.getAttribute(self.nameAttributeName)     
            
            # Check for field override, ie NINDEX, UINDEX
            fieldName = classNode.getAttribute(self.overrideAttributeName)
            if not fieldName:
                fieldName = self.fieldPrefix + classId + self.fieldSuffix
            
            className = message.format(classId, fieldName, name)
            classNames.append(className)   
            
        return classNames
        
        
    def updateInputFieldsParameter(self):
        """  Set selected input field to first field of specified type
            
             Specified types comes from self.inputIdFieldTypes set in __init__()
             
        """
        
        fieldTypes = set(self.inputIdFieldTypes)
        tablePath = self.inputTableParameter.value
        fieldName = self.inputFieldsParameter.value
        
        # Proceed only if table path exists, but field name hasn't been set
        if tablePath and not fieldName:
            try:
                fields = arcpy.ListFields(tablePath)
                
                for field in fields:
                    if field.type in fieldTypes:
                        self.inputFieldsParameter.value = field.name
                        break
                    
                if not self.inputFieldsParameter.value:
                    for field in fields:
                        if field.type == "OID":
                            self.inputFieldsParameter.value = field.name
                            break
                        
            except:
                pass
                
        
    def updateMessages(self):
        """ ESRI - Modify the messages created by internal validation for each tool parameter.  
        
            This method is called after internal validation.
            
        """

        # Set lcc file parameter required only if user-defined is set
        if self.lccSchemeParameter.value != self.lccSchemeUserOption:
            self.lccFilePathParameter.clearMessage()
            
        # Clear required on disabled lcc class selection
        if not self.lccClassesParameter.enabled:
            self.lccClassesParameter.clearMessage()
        
        # Remove required on optional fields
        self.optionsParameter.clearMessage()
        
        # Set optional raster options if env is set
        if not self.processingCellSizeParameter.value:
            try:
                envCellSize = int(arcpy.env.cellSize)
            except:
                envCellSize = None
            if envCellSize:
                self.processingCellSizeParameter.value = envCellSize
                
        # Set optional snap raster if env is set
        if not self.snapRasterParameter.value:
            self.snapRasterParameter.value = arcpy.env.snapRaster
            
        # Check if input raster is defined
        if self.inRasterParameter.value:
           
            if hasattr(self.inRasterParameter.value, "dataSource"):
                self.inRasterParameter.Value = str(self.inRasterParameter.value.dataSource)
                self.parameters[self.inRasterIndex].value = self.inRasterParameter.Value
            # Check for is input raster layer has spatial reference
            #self.spRefCheck(self.inRasterParameter)
            if arcpy.Describe(self.inRasterParameter.value).spatialReference.name.lower() == "unknown":
                self.inRasterParameter.setErrorMessage(self.noSpatialReferenceMessage)
            
            # Check if input raster is an integer grid
            inRaster = arcpy.Raster(str(self.inRasterParameter.value))
            if not inRaster.isInteger:
                self.inRasterParameter.setErrorMessage(self.nonIntegerGridMessage)
            
            # Update Processing cell size if empty
            if not self.processingCellSizeParameter.value and not self.processingCellSizeParameter.hasError():
                cellSize = arcpy.Raster(str(self.inRasterParameter.value)).meanCellWidth #get from metadata
                self.processingCellSizeParameter.value = cellSize
            
            # Update Snap Raster Parameter if it is empty
            if not self.snapRasterParameter.value and not self.inRasterParameter.hasError():
                self.snapRasterParameter.value = str(self.inRasterParameter.value)
            
        # Check input features
        if self.inputTableParameter.value and not self.inputTableParameter.hasError():
        
        #    # Check for empty input features
        #    if not arcpy.SearchCursor(self.inputTableParameter.value).next():
        #        self.inputTableParameter.setErrorMessage(self.noFeaturesMessage)
            
            # Check for if input feature layer has spatial reference
            # # query for a dataSource attribute, if one exists, it is a lyr file. Get the lyr's data source to do a Describe
            if hasattr(self.inputTableParameter.value, "dataSource"):
                if arcpy.Describe(self.inputTableParameter.value.dataSource).spatialReference.name.lower() == "unknown":
                    self.inputTableParameter.setErrorMessage(self.noSpatialReferenceMessage)
            else:
                if arcpy.Describe(self.inputTableParameter.value).spatialReference.name.lower() == "unknown":
                    self.inputTableParameter.setErrorMessage(self.noSpatialReferenceMessage)

        # Check if processingCellSize is a positive number            
        if self.processingCellSizeParameter.value:
            try:
                cellSizeValue = arcpy.Raster(str(self.processingCellSizeParameter.value)).meanCellWidth
            except:
                cellSizeValue = self.processingCellSizeParameter.value
            if float(str(cellSizeValue)) <= 0:
                self.processingCellSizeParameter.setErrorMessage(self.nonPositiveNumberMessage)
            
        # CHECK ON SECONDARY INPUTS IF PROVIDED
        
        # Check if a secondary input raster is indicated - use if raster can be either integer or float
        if self.inRaster2Index:
            # if provided, check if input raster2 is defined
            if self.inRaster2Parameter.value:
                # query for a dataSource attribute, if one exists, it is a lyr file. Get the lyr's data source to do a Describe
                if hasattr(self.inRaster2Parameter.value, "dataSource"):
                    if arcpy.Describe(self.inRaster2Parameter.value.dataSource).spatialReference.name.lower() == "unknown":
                        self.inRaster2Parameter.setErrorMessage(self.noSpatialReferenceMessage)
                else:
                    if arcpy.Describe(self.inRaster2Parameter.value).spatialReference.name.lower() == "unknown":
                        self.inRaster2Parameter.setErrorMessage(self.noSpatialReferenceMessage)
                
        # Check if a secondary multiple input feature is indicated            
        if self.inMultiFeatureIndex:
            # if provided, get the valueTable and process each entry
            if self.inMultiFeatureParameter.value:
                multiFeatures = self.inMultiFeatureParameter.value
                rowCount = multiFeatures.rowCount
                for row in range(0, rowCount):
                    value = multiFeatures.getValue(row, 0)
                    if value:
                        # check to see if it has a spatial reference
                        d = arcpy.Describe(value)
                        if d.spatialReference.name.lower() == "unknown":
                            self.inMultiFeatureParameter.setErrorMessage(self.noSpatialReferenceMessageMulti)
                            
        # Check if a secondary vector input feature is indicated
        if self.inVector2Index:
            # if provided, check if input vector2 is defined
            if self.inVector2Parameter.value:
                # query for a dataSource attribue, if one exists, it is a lyr file. Get the lyr's data source to do a Decribe
                if hasattr(self.inVector2Parameter.value, "dataSource"):
                    if arcpy.Describe(self.inVector2Parameter.value.dataSource).spatialReference.name.lower() == "unknown":
                        self.inVector2Parameter.setErrorMessage(self.noSpatialReferenceMessage)
                else:
                    if arcpy.Describe(self.inVector2Parameter.value).spatialReference.name.lower() == "unknown":
                        self.inVector2Parameter.setErrorMessage(self.noSpatialReferenceMessage) 
                        
        # Check if distance input (e.g., buffer width, edge width) is a positive number            
        if self.inDistanceIndex:
            if self.inDistanceParameter.value:
                distanceValue = self.inDistanceParameter.value
                # use the split function so this routine can be used for both long and linear unit data types
                strDistance = str(distanceValue).split()[0]
                if float(strDistance) <= 0.0:
                    self.inDistanceParameter.setErrorMessage(self.nonPositiveNumberMessage)
            else:
                # need the else condition as a 0 value won't trigger the if clause 
                self.inDistanceParameter.setErrorMessage(self.nonPositiveNumberMessage)
                        
            
class CoefficientValidator(ProportionsValidator):
    """ Class for inheritance by ToolValidator Only """

    def getLccList(self, lccFilePath):
        lccList = []
        lccDoc = LandCoverClassification(lccFilePath)
        message = self.metricDescription
        for coefficient in lccDoc.coefficients.values():
            assert isinstance(coefficient, LandCoverCoefficient)
            line = message.format(coefficient.coefId, coefficient.fieldName, coefficient.name)
            lccList.append(line)
            
        return lccList
    
    
class NoLccFileValidator(object):
    """ Class for inheritance by ToolValidator Only
    
        This currently serves the following tools:
            Road Density Metrics
    

        
        Description of ArcToolbox parameters:
        -------------------------------------
        
        inTableIndex:  Two consecutive parameters
        1. Table(reporting units)
        2. Field(dropdown):  Obtained from="<Table>"
                 
        outTableIndex: Index of output table parameter
        1. table: required, output
        
        optionalFieldsIndex:  index of optional fields parameter
        1. String: Properties: MultiValue=Yes
        
    
    """
    
    
    # Indexes of input parameters
    inTableIndex = 0 
    outTableIndex = 0 
    processingCellSizeIndex = 0
    snapRasterIndex = 0 
    optionalFieldsIndex = 0 
    
    # Indexes of secondary input parameters
    inRasterIndex = 0
    inMultiFeatureIndex = 0
    inVector2Index = 0
    inVector3Index = 0
    inDistanceIndex = 0
    checkbox1Index = 0
    checkbox2Index = 0
    checkboxInParameters = {}
    
    # Additional local variables
    srcDirName = validatorConstants.tbxSourceFolderName
    
    # Metric Specific
    filterList = []
    
    def __init__(self):
        """ ESRI - Initialize ToolValidator class"""
        
        # Load metric constants        
        self.inputIdFieldTypes = validatorConstants.inputIdFieldTypes
        self.noFeaturesMessage = validatorConstants.noFeaturesMessage
        self.noSpatialReferenceMessage = validatorConstants.noSpatialReferenceMessage
        self.noSpatialReferenceMessageMulti = validatorConstants.noSpatialReferenceMessageMulti
        self.nonIntegerGridMessage = validatorConstants.nonIntegerGridMessage
        self.nonPositiveNumberMessage = validatorConstants.nonPositiveNumberMessage
        
        # Load global constants
        self.optionalFieldsName = validatorConstants.optionalFieldsName
        
        # Set relative indexes
        self.inputFieldsIndex = self.inTableIndex + 1
        
        # Assign parameters to local variables
        self.parameters = arcpy.GetParameterInfo()
        self.inputTableParameter = self.parameters[self.inTableIndex]
        self.inputFieldsParameter = self.parameters[self.inputFieldsIndex]
        self.outTableParameter = self.parameters[self.outTableIndex]
        self.optionsParameter = self.parameters[self.optionalFieldsIndex]
        
        # Assign secondary input parameters to local variables
        if self.inRasterIndex:
            self.inRasterParameter = self.parameters[self.inRasterIndex]
            
        if self.processingCellSizeIndex:
            self.processingCellSizeParameter = self.parameters[self.processingCellSizeIndex]
            
        if self.snapRasterIndex:
            self.snapRasterParameter = self.parameters[self.snapRasterIndex]
        
        if self.inMultiFeatureIndex:
            self.inMultiFeatureParameter = self.parameters[self.inMultiFeatureIndex]
            
        if self.inVector2Index:
            self.inVector2Parameter = self.parameters[self.inVector2Index]
            
        if self.inVector3Index:
            self.inVector3Parameter = self.parameters[self.inVector3Index]
            
        if self.inDistanceIndex:
            self.inDistanceParameter = self.parameters[self.inDistanceIndex]
            
        if self.checkbox1Index:
            self.checkbox1Parameter = self.parameters[self.checkbox1Index]
            
        if self.checkbox2Index:
            self.checkbox2Parameter = self.parameters[self.checkbox2Index]

               
        # Additional local variables
        self.currentFilePath = ""
        self.ruFilePath = ""
        self.initialized = False


    def initializeParameters(self):
        """ ESRI - Initialize parameters"""
        
        # disable dependent input fields until optional check boxes are selected    
        if self.checkboxInParameters:
            for val in self.checkboxInParameters.values():
                for indx in val:
                    self.parameters[indx].enabled = False  
        
        # Move parameters to optional section
        self.optionsParameter.category = self.optionalFieldsName
        
        # Set options filter
        self.optionsParameter.filter.list = self.filterList
    
        self.initialized = True
        
        
    def updateParameters(self):
        """ ESRI - Modify the values and properties of parameters before internal validation is performed.  
        
            This method is called whenever a parameter has been changed.
        
        """
        
        if not self.initialized:
            self.initializeParameters()

        self.updateInputFieldsParameter()
        self.updateOutputTableParameter()

        # if checkboxes are provided, use the indexes specified in the tool's validation script to identify the 
        # parameter locations of any additional needed inputs for that checkbox and enable those parameters
        if self.checkbox1Index:
            cboxListeners = self.checkboxInParameters.values()[0]
            self.updateCheckboxParameters(self.checkbox1Parameter, cboxListeners)

        if self.checkbox2Index:
            cboxListeners = self.checkboxInParameters.values()[1]
            self.updateCheckboxParameters(self.checkbox2Parameter, cboxListeners)

    def updateCheckboxParameters(self, checkboxParameter, cboxListeners):
        if checkboxParameter.value:
            for indx in cboxListeners:
                self.parameters[indx].enabled = True

    def updateOutputTableParameter(self):
        """ Update an output table parameter
        
        **Description:**
            
            Removes .shp that is automatically generated for output table parameters and replaces it with .dbf
        
        """
       
        if self.outTableParameter.value:
            outTablePath = str(self.outTableParameter.value)
            self.outTableParameter.value  = outTablePath.replace('.shp', '.dbf')

    
              
        
    def updateInputFieldsParameter(self):
        """  Set selected input field to first field of specified type
            
             Specified types comes from self.inputIdFieldTypes set in __init__()
             
        """
        
        fieldTypes = set(self.inputIdFieldTypes)
        tablePath = self.inputTableParameter.value
        fieldName = self.inputFieldsParameter.value
        
        # Proceed only if table path exists, but field name hasn't been set
        if tablePath and not fieldName:
            try:
                fields = arcpy.ListFields(tablePath)
                
                for field in fields:
                    if field.type in fieldTypes:
                        self.inputFieldsParameter.value = field.name
                        break
                    
                if not self.inputFieldsParameter.value:
                    for field in fields:
                        if field.type == "OID":
                            self.inputFieldsParameter.value = field.name
                            break
                        
            except:
                pass
                
        
    def updateMessages(self):
        """ ESRI - Modify the messages created by internal validation for each tool parameter.  
        
            This method is called after internal validation.
            
        """
        
        # Remove required on optional fields
        self.optionsParameter.clearMessage()
                                 
        # Check input features
        if self.inputTableParameter.value and not self.inputTableParameter.hasError():
        
        #    # Check for empty input features
        #    if arcpy.SearchCursor(self.inputTableParameter.value).next():
        #        self.inputTableParameter.setErrorMessage(self.noFeaturesMessage)
            
            # Check for if input feature layer has spatial reference
            # # query for a dataSource attribute, if one exists, it is a lyr file. Get the lyr's data source to do a Describe
            if hasattr(self.inputTableParameter.value, "dataSource"):
                if arcpy.Describe(self.inputTableParameter.value.dataSource).spatialReference.name.lower() == "unknown":
                    self.inputTableParameter.setErrorMessage(self.noSpatialReferenceMessage)
            else:
                if arcpy.Describe(self.inputTableParameter.value).spatialReference.name.lower() == "unknown":
                    self.inputTableParameter.setErrorMessage(self.noSpatialReferenceMessage)
           
        # CHECK ON SECONDARY INPUTS IF PROVIDED
        
        # if optional check box is unselected, clear the parameter message area and value area    
        if self.checkboxInParameters:
            for val in self.checkboxInParameters.values():
                for indx in val:
                    if not self.parameters[indx].enabled:
                        self.parameters[indx].clearMessage()
                        self.parameters[indx].value = ''
                        
        # Check if a raster is needed for metric calculations
        if self.inRasterIndex:
            if self.inRasterParameter.value:
                if hasattr(self.inRasterParameter.value, "dataSource"):
                    self.inRasterParameter.Value = str(self.inRasterParameter.value.dataSource)
                    self.parameters[self.inRasterIndex].value = self.inRasterParameter.Value
                # Check for is input raster layer has spatial reference
                #self.spRefCheck(self.inRasterParameter)
                if arcpy.Describe(self.inRasterParameter.value).spatialReference.name.lower() == "unknown":
                    self.inRasterParameter.setErrorMessage(self.noSpatialReferenceMessage)
            
                # Check if input raster is an integer grid
                inRaster = arcpy.Raster(str(self.inRasterParameter.value))
                if not inRaster.isInteger:
                    self.inRasterParameter.setErrorMessage(self.nonIntegerGridMessage)
            
                # Update Processing cell size if empty
                if not self.processingCellSizeParameter.value and not self.processingCellSizeParameter.hasError():
                    cellSize = arcpy.Raster(str(self.inRasterParameter.value)).meanCellWidth #get from metadata
                    self.processingCellSizeParameter.value = cellSize
            
                # Update Snap Raster Parameter if it is empty
                if not self.snapRasterParameter.value and not self.inRasterParameter.hasError():
                    self.snapRasterParameter.value = str(self.inRasterParameter.value)
                
        
        # Check if a secondary multiple input feature is indicated            
        if self.inMultiFeatureIndex:
            # if provided, get the valueTable and process each entry
            if self.inMultiFeatureParameter.value:
                multiFeatures = self.inMultiFeatureParameter.value
                rowCount = multiFeatures.rowCount
                for row in range(0, rowCount):
                    value = multiFeatures.getValue(row, 0)
                    if value:
                        # check to see if it has a spatial reference
                        d = arcpy.Describe(value)
                        if d.spatialReference.name.lower() == "unknown":
                            self.inMultiFeatureParameter.setErrorMessage(self.noSpatialReferenceMessageMulti)
                            
        # Check if a secondary vector input feature is indicated
        if self.inVector2Index:
            # check if input vector2 is defined
            if self.inVector2Parameter.value:
                # query for a dataSource attribue, if one exists, it is a lyr file. Get the lyr's data source to do a Decribe
                if hasattr(self.inVector2Parameter.value, "dataSource"):
                    if arcpy.Describe(self.inVector2Parameter.value.dataSource).spatialReference.name.lower() == "unknown":
                        self.inVector2Parameter.setErrorMessage(self.noSpatialReferenceMessage)
                else:
                    if arcpy.Describe(self.inVector2Parameter.value).spatialReference.name.lower() == "unknown":
                        self.inVector2Parameter.setErrorMessage(self.noSpatialReferenceMessage) 
                        
        # Check if a tertiary vector input feature is indicated
        if self.inVector3Index:
            # check if input vector3 is defined
            if self.inVector3Parameter.value:
                # query for a dataSource attribue, if one exists, it is a lyr file. Get the lyr's data source to do a Decribe
                if hasattr(self.inVector3Parameter.value, "dataSource"):
                    if arcpy.Describe(self.inVector3Parameter.value.dataSource).spatialReference.name.lower() == "unknown":
                        self.inVector3Parameter.setErrorMessage(self.noSpatialReferenceMessage)
                else:
                    if arcpy.Describe(self.inVector3Parameter.value).spatialReference.name.lower() == "unknown":
                        self.inVector3Parameter.setErrorMessage(self.noSpatialReferenceMessage)
                        
        # Check if distance input (e.g., buffer width, edge width) is a positive number            
        if self.inDistanceIndex:
            # check that the supplied value is positive
            if self.inDistanceParameter.value:
                distanceValue = self.inDistanceParameter.value
                # use the split function so this routine can be used for both long and linear unit data types
                strDistance = str(distanceValue).split()[0]
                if float(strDistance) <= 0.0:
                    self.inDistanceParameter.setErrorMessage(self.nonPositiveNumberMessage)
#            else:
#                # need the else condition as a 0 value won't trigger the if clause 
#                self.inDistanceParameter.setErrorMessage(self.nonPositiveNumberMessage)
