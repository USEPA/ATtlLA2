import arcpy


class TabulateAreaTable(object):
    """ Tabluate area helper"""
    
    _value = "Value"
    _tempTableName = "xtmp"
    _valueFieldPrefix = "VALUE_"
    _datasetType = "Dataset"
    _inReportingUnitFeature = None
    _reportingUnitIdField = None
    _inLandCoverGrid = None
    _tableName = None
    _table = None
    _tabAreaValueFields = None
    _tabAreaTableRows = None
    _destroyTable = True
    

    def __init__(self, inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, tableName=None, lccObj=None):
        """ Constructor - Called when created 
        
            If tableName is None, the table will be deleted, otherwise it persists
        
        """
        
        self._inReportingUnitFeature = inReportingUnitFeature
        self._reportingUnitIdField = reportingUnitIdField
        self._inLandCoverGrid = inLandCoverGrid
        self._tableName = tableName
        
        if lccObj:
            self._excludedValues = lccObj.values.getExcludedValueIds()
        else:
            self._excludedValues = []
        
        self._createNewTable()
        
        
    def _createNewTable(self):
        """ Create the underlying arcpy table"""
        
        if self._tableName:
            self._destroyTable = False
            self._tableName = arcpy.CreateScratchName(self._tableName, "", self._datasetType)
        else:
            self._tableName = arcpy.CreateScratchName(self._tempTableName, "", self._datasetType)
            
        
        arcpy.gp.TabulateArea_sa(self._inReportingUnitFeature, self._reportingUnitIdField, self._inLandCoverGrid, 
                                 self._value, self._tableName)
        
        self._tabAreaTableRows = arcpy.SearchCursor(self._tableName)        
        self._tabAreaValueFields = arcpy.ListFields(self._tableName, self._valueFieldPrefix + "*" )
        self._tabAreaValues = [int(aFld.name.replace(self._valueFieldPrefix,"")) for aFld in self._tabAreaValueFields]
         
        self._tabAreaDict = dict(zip(self._tabAreaValues,[])) 
        
        
    def __del__(self):
        """ Destructor - Called when deleted (Housekeeping)"""
        
        del self._tabAreaTableRows
        
        if self._destroyTable:
            arcpy.Delete_management(self._tableName)
    
    
    def __iter__(self):
        """ Return iterator object """
        
        return self


    def __next__(self):
        """ Iterate items"""
        
        row = self._tabAreaTableRows.__next__()
        
        if row:
            return TabulateAreaRow(row, self._reportingUnitIdField, self._tabAreaValueFields, self._tabAreaValues, 
                                   self._tabAreaDict, self._excludedValues)
        else:
            raise StopIteration
    


class TabulateAreaRow(object):    
    """"""
    _row = None
    _tabAreaValueFields = None
    _tabAreaValues = None
    _excludedValues = []
    
    tabAreaDict = None
    zoneIdValue = -1
    excludedArea = -1
    effectiveArea = -1
    totalArea = -1
    
    
    def __init__(self, row, reportingUnitIdField, tabAreaValueFields, tabAreaValues, tabAreaDict, excludedValues):
        """ Constructor - Called when created 
        
            * row - arcpy row object
        """
        
        self._row = row
        self._tabAreaValueFields = tabAreaValueFields
        self._tabAreaValues = tabAreaValues
        self.tabAreaDict = tabAreaDict
        self._reportingUnitIdField = reportingUnitIdField
        self._excludedValues = excludedValues
        self._loadRow()
        
        
    def _loadRow(self):
        
        self.zoneIdValue = self._row.getValue(self._reportingUnitIdField)
        
        self.excludedArea = 0  #area of reporting unit not used in metric calculations e.g., water area
        self.effectiveArea = 0  #effective area of the reporting unit e.g., land area
    
        for i, aFld in enumerate(self._tabAreaValueFields):
            # store the grid code and it's area value into the dictionary
            valKey = self._tabAreaValues[i]
            valArea = self._row.getValue(aFld.name)
            self.tabAreaDict[valKey] = valArea
    
            #add the area of each grid value to the appropriate area sum i.e., effective or excluded area
            if valKey in self._excludedValues:
                self.excludedArea += valArea
            else:
                self.effectiveArea += valArea               
        
        self.totalArea = self.effectiveArea + self.excludedArea

    def __del__(self):
        """ Destructor - Called when deleted (Housekeeping)"""
        
        del self._row


