""" Utilities specific to area

"""
from ATtILA2.constants import globalConstants

import arcpy
from ATtILA2.setupAndRestore import _tempEnvironment3
from . import messages
from . import files
from . import vector
from . import table


def getMetricPercentAreaAndSum(metricGridCodesList, tabAreaDict, effectiveAreaSum, excludedValues):
    """ Calculates the percentage of the reporting unit effective area occupied by the metric class codes and their 
    total area
    
    **Description:**

        Retrieves stored area figures for each grid code associated with selected metric and sums them.
        That number, divided by the total effective area within the reporting unit and multiplied by 100, gives the
        percentage of the effective reporting unit that is occupied by the metric class. Both the percentage and the 
        final area sum are returned.
        
    **Arguments:**

        * *metricGridCodesList* - list of all grid values assigned to a metric class in the lcc file (e.g., [41, 42, 43] 
                                for the forest class)
                             
        * *tabAreaDict* - dictionary with the area value of each grid code in a reporting unit keyed to the grid code
        
        * *effectiveAreaSum* - sum of the area of all grid cells in the reporting unit with codes not tagged as excluded 
                                in the lcc file
                                
        * *excludedValues* - a set of grid values tagged in the xml lcc file to be excluded from the total area calculations
                            (e.g. water areas when the user is concerned with land area calculations)
        
    **Returns:**

        * float - the percentage of the reporting unit effective area that is occupied by the metric class codes
        * float - the sum of the area of metric class codes
        
    """
    
    metricAreaSum = 0                         
    for aValueID in metricGridCodesList:
        if aValueID not in excludedValues:
            metricAreaSum += tabAreaDict.get(aValueID, 0) #add 0 if the lcc defined value is not found in the grid
    
    if effectiveAreaSum > 0:
        metricPercentArea = (metricAreaSum / effectiveAreaSum) * 100
    else: # all values found in reporting unit are in the excluded set
        metricPercentArea = 0
        
    return metricPercentArea, metricAreaSum


def landCoverProportions(lccClassesDict, metricsBaseNameList, optionalGroupsList, metricConst, outIdField, newTable, 
                         tabAreaTable, metricsFieldnameDict, zoneAreaDict, zoneValueDict=False,
                         conversionFactor=None):
    """ Creates *outTable* populated with land cover proportions metrics
    
    **Description:**

        Creates *outTable* populated with land cover proportions metrics...
        
    **Arguments:**

        * *lccClassesDict* - dictionary of metric class values 
                        (e.g., classValuesDict['for'].uniqueValueIds = (41, 42, 43))
        * *metricsBaseNameList* - a list of metric BaseNames parsed from the 'Metrics to run' input 
                        (e.g., [for, agt, shrb, devt] or [NITROGEN, IMPERVIOUS])
        * *optionalGroupsList* - list of the selected options parsed from the 'Select options' input
                        (e.g., ["QAFIELDS", "AREAFIELDS", "INTERMEDIATES"])
        * *metricConst* - an object with constants specific to the metric being run (lcp vs lcosp)
        * *outIdField* - a copy of the reportingUnitIdField except where the IdField type = OID
        * *newTable* - the ATtILA created output table 
        * *tabAreaTable* - tabulateArea request output from ArcGIS
        * *metricsFieldnameDict* - a dictionary keyed to the lcc class with the ATtILA generated fieldname tuple as value
                        The tuple consists of the output fieldname and the class name as modified
                        (e.g., "forest":("fore0_E2A7","fore0")
        * *zoneAreaDict* -  dictionary with the area of each input polygon keyed to the polygon's ID value. 
                        Used in grid overlap calculations.
        * *zoneValueDict* - dictionary with a value for an input polygon feature keyed to the polygon's ID value.
                        Used in lcc class area per value calculations (e.g. square meters of forest per person).
        
    **Returns:**

        * None
        
    """
    
    try:      
        # create the cursor to add data to the output table
        outTableRows = arcpy.InsertCursor(newTable)        
        
        for tabAreaTableRow in tabAreaTable:
            tabAreaDict = tabAreaTableRow.tabAreaDict
            effectiveArea = tabAreaTableRow.effectiveArea
            excludedValues = tabAreaTableRow._excludedValues
            
            # initiate a row to add to the metric output table
            outTableRow = outTableRows.newRow()
            
            # set the reporting unit id value in the output row
            outTableRow.setValue(outIdField.name, tabAreaTableRow.zoneIdValue)
            
            # sum the areas for the selected metric's grid codes   
            for mBaseName in metricsBaseNameList: 
                # get the grid codes for this specified metric
                metricGridCodesList = lccClassesDict[mBaseName].uniqueValueIds
                # get the class percentage area and it's actual area from the tabulate area table
                metricPercentageAndArea = getMetricPercentAreaAndSum(metricGridCodesList, tabAreaDict, effectiveArea, excludedValues)
                
                # add the calculation to the output row
                outTableRow.setValue(metricsFieldnameDict[mBaseName][0], metricPercentageAndArea[0])
                
                if globalConstants.metricAddName in optionalGroupsList:
                    areaSuffix = globalConstants.areaFieldParameters[0]
                    outTableRow.setValue(metricsFieldnameDict[mBaseName][0]+areaSuffix, metricPercentageAndArea[1])

                # add per value (e.g., capita) calculations to row
                if zoneValueDict:
                    zoneValue = zoneValueDict[tabAreaTableRow.zoneIdValue]
                    classSqM = metricPercentageAndArea[1] * conversionFactor
                    perValueCalc = classSqM / zoneValue
                    #perValueCalc = metricPercentageAndArea[1] / zoneValue
                    perValueSuffix = metricConst.perCapitaSuffix
                    meterSquaredSuffix = metricConst.meterSquaredSuffix
                    outTableRow.setValue(metricsFieldnameDict[mBaseName][1]+perValueSuffix, perValueCalc)
                    outTableRow.setValue(metricsFieldnameDict[mBaseName][1]+meterSquaredSuffix, classSqM)

            # add QACheck calculations/values to row
            if zoneAreaDict:
                zoneArea = zoneAreaDict[tabAreaTableRow.zoneIdValue]
                overlapCalc = ((tabAreaTableRow.totalArea)/zoneArea) * 100
                
                qaCheckFlds = metricConst.qaCheckFieldParameters
                outTableRow.setValue(qaCheckFlds[0][0], overlapCalc)
                outTableRow.setValue(qaCheckFlds[1][0], tabAreaTableRow.totalArea)
                outTableRow.setValue(qaCheckFlds[2][0], tabAreaTableRow.effectiveArea)
                outTableRow.setValue(qaCheckFlds[3][0], tabAreaTableRow.excludedArea)
            
            # commit the row to the output table
            outTableRows.insertRow(outTableRow)
                
    finally:
        
        # delete cursor and row objects to remove locks on the data
        try:
            del outTableRows
            del outTableRow
            del tabAreaTable
            del tabAreaTableRow
        except:
            pass


# def landCoverProportionsOLD(lccClassesDict, metricsBaseNameList, optionalGroupsList, metricConst, outIdField, newTable, 
#                          tabAreaTable, metricsFieldnameDict, zoneAreaDict):
#     """ Creates *outTable* populated with land cover proportions metrics
#     
#     **Description:**
# 
#         Creates *outTable* populated with land cover proportions metrics...
#         
#     **Arguments:**
# 
#         * *lccClassesDict* - dictionary of metric class values 
#                         (e.g., classValuesDict['for'].uniqueValueIds = (41, 42, 43))
#         * *metricsBaseNameList* - a list of metric BaseNames parsed from the 'Metrics to run' input 
#                         (e.g., [for, agt, shrb, devt] or [NITROGEN, IMPERVIOUS])
#         * *optionalGroupsList* - list of the selected options parsed from the 'Select options' input
#                         (e.g., ["QAFIELDS", "AREAFIELDS", "INTERMEDIATES"])
#         * *metricConst* - an object with constants specific to the metric being run (lcp vs lcosp)
#         * *outIdField* - a copy of the reportingUnitIdField except where the IdField type = OID
#         * *newTable* - the ATtILA created output table 
#         * *tabAreaTable* - tabulateArea request output from ArcGIS
#         * *metricsFieldnameDict* - a dictionary keyed to the lcc class with the ATtILA generated fieldname tuple as value
#                         The tuple consists of the output fieldname and the class name as modified
#                         (e.g., "forest":("fore0_E2A7","fore0")
#         * *zoneAreaDict* -  dictionary with the area of each input polygon keyed to the polygon's ID value. 
#                         Used in grid overlap calculations.
#         
#     **Returns:**
# 
#         * None
#         
#     """
#     
#     try:      
#         # create the cursor to add data to the output table
#         outTableRows = arcpy.InsertCursor(newTable)        
#         
#         for tabAreaTableRow in tabAreaTable:
#             tabAreaDict = tabAreaTableRow.tabAreaDict
#             effectiveArea = tabAreaTableRow.effectiveArea
#             excludedValues = tabAreaTableRow._excludedValues
#             
#             # initiate a row to add to the metric output table
#             outTableRow = outTableRows.newRow()
#             
#             # set the reporting unit id value in the output row
#             outTableRow.setValue(outIdField.name, tabAreaTableRow.zoneIdValue)
#             
#             # sum the areas for the selected metric's grid codes   
#             for mBaseName in metricsBaseNameList: 
#                 # get the grid codes for this specified metric
#                 metricGridCodesList = lccClassesDict[mBaseName].uniqueValueIds
#                 # get the class percentage area and it's actual area from the tabulate area table
#                 metricPercentageAndArea = getMetricPercentAreaAndSum(metricGridCodesList, tabAreaDict, effectiveArea, excludedValues)
#                 
#                 # add the calculation to the output row
#                 outTableRow.setValue(metricsFieldnameDict[mBaseName][0], metricPercentageAndArea[0])
#                 
#                 if globalConstants.metricAddName in optionalGroupsList:
#                     areaSuffix = globalConstants.areaFieldParameters[0]
#                     outTableRow.setValue(metricsFieldnameDict[mBaseName][0]+areaSuffix, metricPercentageAndArea[1])
# 
#             # add QACheck calculations/values to row
#             if zoneAreaDict:
#                 zoneArea = zoneAreaDict[tabAreaTableRow.zoneIdValue]
#                 overlapCalc = ((tabAreaTableRow.totalArea)/zoneArea) * 100
#                 
#                 qaCheckFlds = metricConst.qaCheckFieldParameters
#                 outTableRow.setValue(qaCheckFlds[0][0], overlapCalc)
#                 outTableRow.setValue(qaCheckFlds[1][0], tabAreaTableRow.totalArea)
#                 outTableRow.setValue(qaCheckFlds[2][0], tabAreaTableRow.effectiveArea)
#                 outTableRow.setValue(qaCheckFlds[3][0], tabAreaTableRow.excludedArea)
#             
#             # commit the row to the output table
#             outTableRows.insertRow(outTableRow)
#                 
#     finally:
#         
#         # delete cursor and row objects to remove locks on the data
#         try:
#             del outTableRows
#             del outTableRow
#             del tabAreaTable
#             del tabAreaTableRow
#         except:
#             pass
               

def getCoefficientPerUnitArea(tabAreaDict, lccValuesDict, coeffId, conversionFactor):
    """  Returns the estimated amount of substance per HECTARE based on supplied coefficient values
    
    **Description:**

        For each grid value in a reporting unit, the area for that value is retrieved and converted to hectares. That
        value is then multiplied by the coefficient stored in the LCC file to estimate the amount of the selected 
        substance found in the reporting unit based on that land cover type. The estimated amount is then summed
        across all land cover types and divided by the total area of the reporting unit, again in hectares. The 
        estimated amount of substance per hectare is then returned.
        
    **Arguments:**
                             
        * *tabAreaDict* - dictionary with the area value of each grid code in a reporting unit keyed to the grid code
        * *lccValuesDict* - dictionary with all the individual VALUES and their attributes supplied in the LCC file
        * *coeffId* - string containing the coefficient Id in LCC file (e.g., "NITROGEN", "PHOSPHORUS")
        * *conversionFactor* - float value for the conversion of area values to number of hectares
        
    **Returns:**

        * float - the calculated metric based on coefficient values and metric type (per unit area)
        
    """

    coefficientTotalInPolygon = 0
    totalHectaresInPolygon = 0 
                        
    for aVal in tabAreaDict:
        valueAreaFromOutput = tabAreaDict[aVal]
        valueSqMeters = valueAreaFromOutput * conversionFactor
        valueHectares = valueSqMeters/10000.0
        totalHectaresInPolygon += valueHectares
        
        # check to see if the grid value is defined in the LCC file. Undefined values are not added to the dividend. 
        # i.e., they will be treated as if they had a coefficient value of 0
        if aVal in lccValuesDict:
            valCoefficient = lccValuesDict[aVal].getCoefficientValueById(coeffId)
            weightedValue = valueHectares * valCoefficient
            coefficientTotalInPolygon += weightedValue
        
    if coefficientTotalInPolygon > 0:    
        coefficientCalculation = coefficientTotalInPolygon / totalHectaresInPolygon
    else:
        coefficientCalculation = 0
    
    return coefficientCalculation


def getCoefficientPercentage(tabAreaDict, lccValuesDict, coeffId):
    """  Multiplies the tabulated area of each grid value by it's coefficient and sums the weighted area across all values
    
    **Description:**

        For each grid value in a reporting unit, the area for that value is retrieved and multiplied by the coefficient 
        stored in the LCC file to estimate the amount of the selected substance found in the reporting unit based on 
        that land cover type. The estimated amount is then summed across all land cover types and multiplied by 100. The 
        computed value is then returned.
        
    **Arguments:**
                             
        * *tabAreaDict* - dictionary with the area value of each grid code in a reporting unit keyed to the grid code
        * *lccValuesDict* - dictionary with all the individual VALUES and their attributes supplied in the LCC file
        * *coeffId* - string containing the coefficient Id in LCC file (e.g., "NITROGEN", "PHOSPHORUS")
        
    **Returns:**

        * float - the calculated metric based on coefficient values and metric type (per unit area or proportion)
        
    """

    coefficientTotalInPolygon = 0
    totalAreaInPolygon = 0
                        
    for aVal in tabAreaDict:
        valueArea = tabAreaDict[aVal]
        totalAreaInPolygon += valueArea
        
        # check to see if the grid value is defined in the LCC file. Undefined values are not added to the dividend. 
        # i.e., they will be treated as if they had a coefficient value of 0
        if aVal in lccValuesDict:
            valCoefficient = lccValuesDict[aVal].getCoefficientValueById(coeffId)
            weightedValue = valueArea * valCoefficient
            coefficientTotalInPolygon += weightedValue
            
    if coefficientTotalInPolygon > 0:
        coefficientCalculation = (coefficientTotalInPolygon / totalAreaInPolygon) * 100    
    else:
        coefficientCalculation = 0
  
    return coefficientCalculation


def landCoverCoefficientCalculator(lccValuesDict, metricsBaseNameList, optionalGroupsList, metricConst, outIdField, 
                                   newTable, tabAreaTable, metricsFieldnameDict, zoneAreaDict, conversionFactor):
    """ Creates *outTable* populated with land cover coefficient metrics
    
    **Description:**

        Creates *outTable* populated with land cover coefficient metrics...
        
    **Arguments:**

        * *lccValuesDict* - dictionary with all the individual VALUES and their attributes supplied in the LCC file 
                        (e.g., lccValuesDict['21'].name = "Developed, Open Space";
                               lccValuesDict['21'].getCoefficientValueById("NITROGEN") = 9.25)
        * *metricsBaseNameList* - a list of metric BaseNames parsed from the 'Metrics to run' input 
                        (e.g., [for, agt, shrb, devt] or [NITROGEN, IMPERVIOUS])
        * *optionalGroupsList* - list of the selected options parsed from the 'Select options' input
                        (e.g., ["QAFIELDS", "AREAFIELDS", "INTERMEDIATES"])
        * *metricConst* - an object with constants specific to the metric being run (lcp or lcosp, etc.)
        * *outIdField* - a copy of the reportingUnitIdField except where the IdField type = OID
        * *newTable* - the ATtILA created output table 
        * *metricsFieldnameDict* - a dictionary keyed to the lcc class with the ATtILA generated fieldname tuple as value
                        The tuple consists of the output fieldname and the class name as modified
                        (e.g., "forest":("fore0_E2A7","fore0")                        
        * *zoneAreaDict* -  dictionary with the area of each input polygon keyed to the polygon's ID value. 
                        Used in grid overlap calculations.
        * *conversionFactor* - conversion factor to convert area measures to square meters. It is a float value
        
    **Returns:**

        * None
        
    """
    
    try:
        # create the cursor to add data to the output table
        outTableRows = arcpy.InsertCursor(newTable)        
        
        for tabAreaTableRow in tabAreaTable:
            
            # initiate a row to add to the metric output table
            outTableRow = outTableRows.newRow()
            # set the reporting unit id value in the output row
            outTableRow.setValue(outIdField.name, tabAreaTableRow.zoneIdValue)
            
            # compute the amount of metric item (e.g., NITROGEN) per unit area using the supplied coefficients   
            for mBaseName in metricsBaseNameList:
                # get coefficient per unit area from the tabulate area table
                if mBaseName in metricConst.perUnitAreaMetrics:
                    coefficientCalculation = getCoefficientPerUnitArea(tabAreaTableRow.tabAreaDict, lccValuesDict, 
                                                                       mBaseName, conversionFactor)
                elif mBaseName in metricConst.percentageMetrics:
                    coefficientCalculation = getCoefficientPercentage(tabAreaTableRow.tabAreaDict, lccValuesDict,
                                                                      mBaseName)
                else:
                    arcpy.AddWarning("Procedure for %s undefined. Tell the programmer to add it to metricConstants.py" % 
                                     mBaseName)
                    
                # add the calculation to the output row
                outTableRow.setValue(metricsFieldnameDict[mBaseName][0], coefficientCalculation)
                
            # add QACheck calculations/values to row
            if globalConstants.qaCheckName in optionalGroupsList:
                zoneArea = zoneAreaDict[tabAreaTableRow.zoneIdValue]
                overlapCalc = ((tabAreaTableRow.totalArea)/zoneArea) * 100
                
                qaCheckFields = metricConst.qaCheckFieldParameters
                outTableRow.setValue(qaCheckFields[0][0], overlapCalc)
            
            # commit the row to the output table
            outTableRows.insertRow(outTableRow)
                
    finally:
        
        # delete cursor and row objects to remove locks on the data
        try:
            del outTableRows
            del outTableRow
            del tabAreaTable
            del tabAreaTableRow
        except:
            pass


def lineDensityCalculator(inLines,inAreas,areaUID,unitArea,outLines,densityField,inLengthField,lineClass="",iaField=""):
    """ Creates *outLines* that contains one multipart linear feature for each *inArea* for calculating line density
        in kilometers per square kilometer of area.
    
    **Description:**

        Creates *outLines* that contains one multipart linear feature for each *inArea* for calculating line density
        in kilometers per square kilometer of area.  If a line class is specified, then outLines will actually contain
        one feature per class per input Area, and the linear density is also broken out by class.  If a field for 
        calculating total impervious area is given, the function will add and populate that field with a linear
        regression equation.
        
    **Arguments:**

        * *inLines* - input linear feature class with full path
        * *inAreas* - input areal unit feature class with full path
        * *areaUID* - ID field for the areal units feature class.
        * *unitArea* - field in the areal units feature class containing area in square kilometers.
        * *outLines* - desired output linear features with full path
        * *densityField* - desired fieldname for output density field
        * *inLengthField* - desired fieldname for output length field
        * *lineClass* - optional field in the input linear feature class containing classes of linear features.  
        * *iaField* - if total impervious area should be calculated for these lines, the desired output fieldname
        
    **Returns:**

        * None
        
    """
    
    from . import vector
    
    # First perform the split/dissolve/merge on the roads
    outLines, lineLengthFieldName = vector.splitDissolveMerge(inLines,inAreas,areaUID,outLines,inLengthField,lineClass)

    # Next join the reporting units layer to the merged roads layer
    arcpy.JoinField_management(outLines, areaUID.name, inAreas, areaUID.name, [unitArea])
    # Set up a calculation expression for density.
    calcExpression = "!" + lineLengthFieldName + "!/!" + unitArea + "!"
    densityField = vector.addCalculateField(outLines,densityField,calcExpression)

    if iaField: # if a field has been specified for calculating total impervious area.
        # Calculate the road density linear regression for total impervious area:
        calcExpression = "pctiaCalc(!" + densityField + "!)"
        codeblock = """def pctiaCalc(RdDensity):
        pctia = ((RdDensity - 1.78) / 0.16)
        if (RdDensity < 1.79):
            return 0
        elif (RdDensity > 11):
            return -1
        else:
            return pctia"""
        iaField = vector.addCalculateField(outLines,iaField,calcExpression,codeblock)
    
    return outLines, lineLengthFieldName


def landCoverDiversity(metricConst, outIdField, newTable, tabAreaTable, zoneAreaDict):
    """ Creates *outTable* populated with land cover diversity metrics
    
    **Description:**

        Creates *outTable* populated with land cover diversity metrics...
        
    **Arguments:**

        * *metricConst* - an object with constants specific to the metric being run (lcp vs lcosp)
        * *outIdField* - a copy of the reportingUnitIdField except where the IdField type = OID
        * *newTable* - the ATtILA created output table 
        * *tabAreaTable* - tabulateArea request output from ArcGIS
        * *zoneAreaDict* -  dictionary with the area of each input polygon keyed to the polygon's ID value. 
                        Used in grid overlap calculations.
        
    **Returns:**

        * None
        
    """
    
    try:      
        # create the cursor to add data to the output table
        outTableRows = arcpy.InsertCursor(newTable)        
        
        for tabAreaTableRow in tabAreaTable:
            
            # initiate a row to add to the metric output table
            outTableRow = outTableRows.newRow()
            
            # set the reporting unit id value in the output row
            outTableRow.setValue(outIdField.name, tabAreaTableRow.zoneIdValue)
            
            # calculate the diversity indices (H, H_Prime, C, and S) for the current reporting unit  
            h,hp,s,c = getDiversityIndices(tabAreaTableRow.tabAreaDict, tabAreaTableRow.totalArea)
            
            # populate metric fields
            outTableRow.S = s
            outTableRow.H = h
            outTableRow.H_Prime = hp
            outTableRow.C = c

            # add QACheck calculations/values to row
            if zoneAreaDict:
                zoneArea = zoneAreaDict[tabAreaTableRow.zoneIdValue]
                overlapCalc = ((tabAreaTableRow.totalArea)/zoneArea) * 100
                
                qaCheckFlds = metricConst.qaCheckFieldParameters
                outTableRow.setValue(qaCheckFlds[0][0], overlapCalc)
                
            
            # commit the row to the output table
            outTableRows.insertRow(outTableRow)
                
    finally:
        
        # delete cursor and row objects to remove locks on the data
        try:
            del outTableRows
            del outTableRow
            del tabAreaTable
            del tabAreaTableRow
        except:
            pass

        
def getDiversityIndices(tabAreaDict, totalArea):
    import math

    pSum = 0
    S = 0
    C = 0
    Hprime = 0

    for i in tabAreaDict.values():
        if i >0:
            #Calculate the percent land use for use in further calculations
            P = i / totalArea
            #Calculate the sum for use in the Shannon-Weiner calculations
            pSum += (P * math.log(P))
            #Calculate the Simpson Index
            C += P * P
            #Calculate the simple diversity
            S += 1

    #Calculate Shannon-Weiner Diversity equation (H)
    H = pSum * -1
    
    #Calculate Shannon-Weiner Diversity equation (H prime)
    if S > 1:
        Hprime = H/math.log(S)
    
    #Create Results tuple to be reported out
    diversityIndices = (H, Hprime, S, C)

    return diversityIndices 


def getCoreEdgeRatio(outIdField, newTable, tabAreaTable, metricsFieldnameDict, zoneAreaDict, metricConst, m):
    """ Creates *outTable* populated with land cover edge to area metrics
    
    **Description:**

        Populates the *outTable* with the land cover edge to area ratio, the percent area designated Core,
        and the percent area that is designated Edge for each reporting unit for the supplied LCC class. 
        
    **Arguments:**

        * *outIdField* - a copy of the reportingUnitIdField except where the IdField type = OID
        * *newTable* - the ATtILA created output table 
        * *tabAreaTable* - tabulateArea request output from ArcGIS
        * *metricsFieldnameDict* - a dictionary keyed to the lcc class with the ATtILA generated fieldname tuple as value
                        The tuple consists of the output fieldname and the class name as modified
                        (e.g., "forest":("fore0_E2A7","fore0")
        * *zoneAreaDict* -  dictionary with the area of each input polygon keyed to the polygon's ID value. 
                        Used in grid overlap calculations.
        * *metricConst* - an object with constants specific to the metric being run (lcp vs lcosp)
        * *m* - a metric BaseName parsed from the 'Metrics to run' input 
                        (e.g., [for, agt, shrb, devt] or [NITROGEN, IMPERVIOUS])

        
    **Returns:**

        * None
        
    """  
    CoreEdgeDict = {}

    try:    
        # Calculate Core/Edge metrics and place results in dictionary with zoneIdValue as the key
        for tabAreaTableRow in tabAreaTable:
            edgeArea = 0
            if ("EDGE" in tabAreaTableRow.tabAreaDict):
                edgeArea = tabAreaTableRow.tabAreaDict["EDGE"]
            coreArea = 0
            if ("CORE" in tabAreaTableRow.tabAreaDict):
                coreArea = tabAreaTableRow.tabAreaDict["CORE"]
            otherArea = 0
            if ("OTHER" in tabAreaTableRow.tabAreaDict):
                otherArea = tabAreaTableRow.tabAreaDict["OTHER"]
            excludedArea = 0
            if ("EXCLUDED" in tabAreaTableRow.tabAreaDict):
                excludedArea = tabAreaTableRow.tabAreaDict["EXCLUDED"]
                
            totalArea = edgeArea + coreArea + otherArea + excludedArea
            effectiveArea = totalArea - excludedArea 
            
            # test to make sure land cover values exist in this zoneId, then gather metrics
            if effectiveArea > 0:
                percentEdge = (edgeArea/effectiveArea)*100
                percentCore = (coreArea/effectiveArea)*100
                if edgeArea or coreArea > 0: # don't want to divide by zero
                    CtoERatio = (edgeArea/(edgeArea + coreArea))*100
                else:
                    arcpy.AddWarning( m + " landuse doesn't exist in reporting unit feature " + str(tabAreaTableRow.zoneIdValue))
                    CtoERatio = 0
            else:
                arcpy.AddWarning("All landuse is tagged as EXCLUDED in reporting unit feature " + str(tabAreaTableRow.zoneIdValue))
                percentEdge = 0
                percentCore = 0
                CtoERatio = 0
                            
            resultsTuple = (CtoERatio, percentCore, percentEdge, totalArea, effectiveArea, excludedArea)
            CoreEdgeDict[tabAreaTableRow.zoneIdValue] = resultsTuple

        
        # Check to see if newTable has already been set up
        rowcount = int(arcpy.GetCount_management(newTable).getOutput(0))
        if rowcount == 0:
            outTableRows = arcpy.InsertCursor(newTable)
            for k in CoreEdgeDict.keys():
                # initiate a row to add to the metric output table
                outTableRow = outTableRows.newRow()
                
                # set the reporting unit id value in the output row
                outTableRow.setValue(outIdField.name, k)
                
                # commit the row to the output table
                outTableRows.insertRow(outTableRow)
            del outTableRows, outTableRow
            
        # assemble the names for the core and edge fields    
        outClassName = metricsFieldnameDict[m][1]
        coreFieldName = metricConst.coreField[0]+outClassName+metricConst.coreField[1]
        edgeFieldName = metricConst.edgeField[0]+outClassName+metricConst.edgeField[1]
            
        # create the cursor to add data to the output table
        outTableRows = arcpy.UpdateCursor(newTable)        
        outTableRow = outTableRows.next()
        while outTableRow:
            uid = outTableRow.getValue(outIdField.name)
            # populate the edge to core ratio for the current reporting unit
            if (uid in CoreEdgeDict):
                outTableRow.setValue(metricsFieldnameDict[m][0], CoreEdgeDict[uid][0])
                outTableRow.setValue(coreFieldName, CoreEdgeDict[uid][1])
                outTableRow.setValue(edgeFieldName, CoreEdgeDict[uid][2])
            else:
                outTableRow.setValue(metricsFieldnameDict[m][0], 0)
                outTableRow.setValue(coreFieldName, 0)
                outTableRow.setValue(edgeFieldName, 0)
                    
            
            # add QACheck calculations/values to row
            if zoneAreaDict:
                zoneArea = zoneAreaDict[uid]
                qaCheckFlds = metricConst.qaCheckFieldParameters

                if (uid in CoreEdgeDict):
                    overlapCalc = ((CoreEdgeDict[uid][3])/zoneArea) * 100
                    outTableRow.setValue(qaCheckFlds[0][0], overlapCalc)
                    outTableRow.setValue(qaCheckFlds[1][0], CoreEdgeDict[uid][3])
                    outTableRow.setValue(qaCheckFlds[2][0], CoreEdgeDict[uid][4])
                    outTableRow.setValue(qaCheckFlds[3][0], CoreEdgeDict[uid][5])
                else:
                    outTableRow.setValue(qaCheckFlds[0][0], 0)
                    outTableRow.setValue(qaCheckFlds[1][0], 0)
                    outTableRow.setValue(qaCheckFlds[2][0], 0)
                    outTableRow.setValue(qaCheckFlds[3][0], 0)                       
            
            # commit the row to the output table
            outTableRows.updateRow(outTableRow)
            outTableRow = outTableRows.next()
    finally:
    
        # delete cursor and row objects to remove locks on the data
        try:
            del outTableRows
            del outTableRow
            del tabAreaTable
            del tabAreaTableRow
        except:
            pass
  

def getMDCP(outIdField, newTable, mdcpDict, optionalGroupsList, outClassName):
    try:
        # Check to see if newTable has already been set up
        rowcount = int(arcpy.GetCount_management(newTable).getOutput(0))
        if rowcount == 0:
            outTableRows = arcpy.InsertCursor(newTable)
            for k in mdcpDict.keys():
                # initiate a row to add to the metric output table
                outTableRow = outTableRows.newRow()
                
                # set the reporting unit id value in the output row
                outTableRow.setValue(outIdField.name, k)
                
                # commit the row to the output table
                outTableRows.insertRow(outTableRow)
            del outTableRows, outTableRow
        # If QA fields are selected, add fields for pwn (patches w/ neighbors) and pwon (patches w/o) for the class
        if globalConstants.qaCheckName in optionalGroupsList:
            arcpy.AddField_management(newTable, outClassName+"_PWN", "Double")
            arcpy.AddField_management(newTable, outClassName+"_PWON", "Double")
        
        mdcpFieldName = outClassName+"_MDCP"

        # create the cursor to add data to the output table
        outTableRows = arcpy.UpdateCursor(newTable)        
        outTableRow = outTableRows.next()
        while outTableRow:
            uid = outTableRow.getValue(outIdField.name)
            # populate the mean distance to edge patch for the current reporting unit
            outTableRow.setValue(mdcpFieldName, mdcpDict[uid].split(",")[2])
            
            # If QA fields are selected, populate the pwon and pwn fields
            if globalConstants.qaCheckName in optionalGroupsList:
                outTableRow.setValue(outClassName+"_PWN", mdcpDict[uid].split(",")[0])
                outTableRow.setValue(outClassName+"_PWON", mdcpDict[uid].split(",")[1])
            
            # commit the row to the output table
            outTableRows.updateRow(outTableRow)
            outTableRow = outTableRows.next()
            
    finally:
        
        # delete cursor and row objects to remove locks on the data
        try:
            del outTableRows
            del outTableRow
            
        except:
            pass
    

def getPatchNumbers(outIdField, newTable, reportingUnitIdField, metricsFieldnameDict, zoneAreaDict, metricConst, m, 
                    inReportingUnitFeature, inLandCoverGrid, processingCellSize, conversionFactor):
    # from . import calculate, conversion, environment, fields, files, messages, parameters, polygons, raster, settings, tabarea, table, vector
    from arcpy import env
    resultsDict={}
    
    try:
        # create list to identify EXCLUDED and OTHER VALUE fields in the tabulate area table
        ignoreFieldList = ["VALUE__9999", "VALUE_0"]
        
        # put the proper field delimiters around the ID field name for SQL expressions
        delimitedField = arcpy.AddFieldDelimiters(inReportingUnitFeature, reportingUnitIdField)
        
        # Initialize custom progress indicator
        totalRUs = len(zoneAreaDict)
        loopProgress = messages.loopProgress(totalRUs)
    
        #For each Reporting Unit run Tabulate Area Analysis and add the results to a dictionary
        for aZone in zoneAreaDict.keys():
            # set initial metric values
            numpatch = 0
            patchArea = 0
            otherArea = 0
            excludedArea = 0
            lrgpatch = 0
            avepatch = 0
            proportion = 0
            patchdensity = 0
            
            if isinstance(aZone, int): # reporting unit id is an integer - convert to string for SQL expression
                squery = "%s = %s" % (delimitedField, str(aZone))
            else: # reporting unit id is a string - enclose it in single quotes for SQL expression
                squery = "%s = '%s'" % (delimitedField, str(aZone))
            
            #Create a feature layer of the single reporting unit
            arcpy.MakeFeatureLayer_management(inReportingUnitFeature,"subwatersheds_Layer",squery)
            
            #Set the geoprocessing extent to just the extent of the selected reporting unit
            selectedRUName = "selectedRU_"+str(aZone)
            arcpy.CopyFeatures_management("subwatersheds_Layer", selectedRUName)
    
            #Tabulate areas of patches within single reporting unit
            tabareaTable = "temptable"
            arcpy.sa.TabulateArea(selectedRUName, reportingUnitIdField, inLandCoverGrid,"Value", tabareaTable, processingCellSize)
            
            arcpy.Delete_management(selectedRUName)
            
            rowcount = int(arcpy.GetCount_management(tabareaTable).getOutput(0))
            if rowcount == 0:
                arcpy.AddWarning("No land cover grid data found in " + str(aZone))
            
            else:
                #Loop through each row in the table and calculate the patch metrics 
                rows = arcpy.SearchCursor(tabareaTable)
                row = rows.next()
        
                while row:
                    flds = arcpy.ListFields(tabareaTable)
                    valueFieldsList = [f.name for f in flds if "VALUE" in f.name]
                    
                    patchAreaList = [row.getValue(fld) for fld in valueFieldsList if fld not in ignoreFieldList]
                    
                    # find the area of the OTHER and EXCLUDED classes if they are found in the reporting unit
                    try:
                        otherArea = row.getValue("VALUE_0")
                    except:
                        otherArea = 0
                        
                    try:
                        excludedArea = row.getValue("VALUE__9999")
                    except:
                        excludedArea = 0
                    
                    if len(patchAreaList) == 0:
                        arcpy.AddWarning("No patches found in " + str(aZone))
                        
                    else: 
                        numpatch = len(patchAreaList)
                        patchArea = sum(patchAreaList)
                        lrgpatch = max(patchAreaList)
                        avepatch = patchArea/numpatch
                        proportion = (lrgpatch/patchArea) * 100
                        
                        #convert to square kilometers
                        rasterRUArea = otherArea + patchArea
                        rasterRUAreaKM = rasterRUArea* (conversionFactor/1000000)
                        patchdensity = numpatch/rasterRUAreaKM         
        
                    row = rows.next()
                
            resultsDict[aZone] = (proportion,numpatch,avepatch,patchdensity,lrgpatch,patchArea,otherArea,excludedArea,zoneAreaDict[aZone])

            loopProgress.update()
            
        # Restore the original enviroment extent
        env.extent = _tempEnvironment3

        # Check to see if newTable has already been set up
        rowcount = int(arcpy.GetCount_management(newTable).getOutput(0))
        if rowcount == 0:
            outTableRows = arcpy.InsertCursor(newTable)
            for k in resultsDict.keys():
                # initiate a row to add to the metric output table
                outTableRow = outTableRows.newRow()
                
                # set the reporting unit id value in the output row
                outTableRow.setValue(outIdField.name, k)
                
                # commit the row to the output table
                outTableRows.insertRow(outTableRow)
            del outTableRows, outTableRow
            
        # assemble the names for the patch metric fields 
        outClassName = metricsFieldnameDict[m][1]
        numFieldName = metricConst.numField[0]+outClassName+metricConst.numField[1]
        avgFieldName = metricConst.avgField[0]+outClassName+metricConst.avgField[1]
        densFieldName = metricConst.densField[0]+outClassName+metricConst.densField[1]
        lrgFieldName = metricConst.lrgField[0]+outClassName+metricConst.lrgField[1]
        
        # check to see if QA fields are included in table
        fldNames = [f.name for f in arcpy.ListFields(newTable)]
        QAFields = metricConst.overlapName in fldNames
   
        # create the cursor to add data to the output table
        outTableRows = arcpy.UpdateCursor(newTable)        
        outTableRow = outTableRows.next()
        while outTableRow:
            uid = outTableRow.getValue(outIdField.name)
            # populate the patch metric fields for the current reporting unit
            if (uid in resultsDict):
                outTableRow.setValue(metricsFieldnameDict[m][0], resultsDict[uid][0])
                outTableRow.setValue(numFieldName, resultsDict[uid][1])
                outTableRow.setValue(avgFieldName, resultsDict[uid][2])
                outTableRow.setValue(densFieldName, resultsDict[uid][3])
                outTableRow.setValue(lrgFieldName, resultsDict[uid][4])
            else:
                outTableRow.setValue(metricsFieldnameDict[m][0], 0)
                outTableRow.setValue(numFieldName, 0)
                outTableRow.setValue(avgFieldName, 0)
                outTableRow.setValue(densFieldName, 0)
                outTableRow.setValue(lrgFieldName, 0)
            
            # add QACheck calculations/values to row
            if QAFields:
                 
                qaCheckFlds = metricConst.qaCheckFieldParameters
                effectiveArea = resultsDict[uid][5] + resultsDict[uid][6]
                excludedArea = resultsDict[uid][7]
                vectorRUArea = resultsDict[uid][8]
                rasterRUArea = effectiveArea + excludedArea
                overlapCalc = (rasterRUArea/ vectorRUArea) * 100
                
                outTableRow.setValue(qaCheckFlds[0][0], overlapCalc)
                outTableRow.setValue(qaCheckFlds[1][0], rasterRUArea)
                outTableRow.setValue(qaCheckFlds[2][0], effectiveArea)
                outTableRow.setValue(qaCheckFlds[3][0], excludedArea)
            
            # commit the row to the output table
            outTableRows.updateRow(outTableRow)
            outTableRow = outTableRows.next()
    finally:
    
        # delete cursor and row objects to remove locks on the data
        try:
            del rows
            del row
            del outTableRows
            del outTableRow
            arcpy.Delete_management(tabareaTable)
        except:
            pass
        
    return resultsDict

            
def getPopDensity(inReportingUnitFeature,reportingUnitIdField,ruArea,inCensusFeature,inPopField,tempWorkspace,
                  outTable,metricConst,cleanupList,index=""):
    """ Performs a transfer of population from input census features to input reporting unit features using simple
        areal weighting.  
    
    **Description:**

        This function makes a temporary copy of the input census features, and using that temporary copy, adds and 
        calculates a field containing the census unit area in square kilometers, and adds and populates a field containing 
        the population density per square kilometer.  The temporary features and their attributes are then intersected
        with the input reporting units.  The area of the intersected polygons is calculated, and then multiplied by
        the population density value from the census data, giving a population count for the intersected polygons.
        Finally, the population counts are summarized by reporting unit ID, giving a population count for each reporting
        unit, and that population count is transferred to the output table, and an appropriate density value calculated.
        
    **Arguments:**

        * *inReportingUnitFeature* - input Reporting Unit feature class with full path.
        * *reportingUnitIdField* - the name of the field in the reporting unit feature class containing a unique identifier
        * *ruArea* - the name of the field in the reporting unit feature class containing the unit area in square kilometers
        * *inCensusFeature* - input population feature class with full path
        * *inPopField* - the name of the field in the population feature class containing count values
        * *tempWorkspace* - an Esri workspace (folder or file geodatabase) where intermediate values will be stored
        * *outTable* -  the output table that will contain calculated population and density values
        * *metricConst* - an ATtILA2 object containing constant values to match documentation
        * *cleanupList* - object containing commands and parameters to perform at cleanup time.
        * *index* - if this function is going to be run multiple times, this index is used to keep track of intermediate
                    outputs and fieldnames.
        
    **Returns:**

        * None
        
    """
    from ATtILA2 import utils
    import os
    # If the user specified an index, add an underscore as prefix.
    if index != "":
        index = "_T" + index
    # Create a copy of the census feature class that we can add new fields to for calculations.  This 
    # is more appropriate than altering the user's input data.
    fieldMappings = arcpy.FieldMappings()
    fieldMappings.addTable(inCensusFeature)
    [fieldMappings.removeFieldMap(fieldMappings.findFieldMapIndex(aFld.name)) for aFld in fieldMappings.fields if aFld.name != inPopField]

    desc = arcpy.Describe(inCensusFeature)
    tempName = "%s_%s" % (metricConst.shortName, desc.baseName)
    tempCensusFeature = files.nameIntermediateFile([tempName + index,"FeatureClass"],cleanupList)
    inCensusFeature = arcpy.FeatureClassToFeatureClass_conversion(inCensusFeature,tempWorkspace,
                                                                         os.path.basename(tempCensusFeature),"",
                                                                         fieldMappings)

    # Add and populate the area field (or just recalculate if it already exists
    popArea = vector.addAreaField(inCensusFeature,'popArea')
    
    # Set up a calculation expression for the density calculation
    calcExpression = "!" + inPopField + "!/!" + popArea + "!"
    # Calculate the population density
    inPopDensityField = vector.addCalculateField(inCensusFeature,'popDens' + index,calcExpression)
    
    # Intersect the reporting units with the population features.
    intersectOutput = files.nameIntermediateFile([metricConst.intersectOutputName + index,"FeatureClass"],cleanupList)
    arcpy.Intersect_analysis([inReportingUnitFeature,inCensusFeature], intersectOutput)
    
    # Add and populate the area field of the intersected polygons
    intArea = vector.addAreaField(intersectOutput,'intArea')
    
    # Calculate the population of the intersected areas by multiplying population density by intersected area
    # Set up a calculation expression for the density calculation
    calcExpression = "!" + inPopDensityField + "!*!" + intArea + "!"
    # Calculate the population density
    intPopField = vector.addCalculateField(intersectOutput,'intPop',calcExpression)
    
    # Intersect the reporting units with the population features.
    summaryTable = files.nameIntermediateFile([metricConst.summaryTableName + index,'Dataset'],cleanupList)
    # Sum population for each reporting unit.
       
    """ If the reportingUnitIdField field is not found, it is assumed that
    the original field was an object ID field that was lost in a format conversion, and the code switches to the new
    objectID field."""
    uIDFields = arcpy.ListFields(intersectOutput,reportingUnitIdField)
    if uIDFields == []: # If the list is empty, grab the field of type OID
        uIDFields = arcpy.ListFields(intersectOutput,"",'OID')
    uIDField = uIDFields[0] # This is an arcpy field object
    reportingUnitIdField = uIDField.name

    arcpy.Statistics_analysis(intersectOutput, summaryTable, [[intPopField, "SUM"]], reportingUnitIdField)

    # Compile a list of fields that will be transferred from the intersected feature class into the output table
    fromFields = ["SUM_" + intPopField]
    toField = 'popCount' + index
    # Transfer the values to the output table
    table.transferField(summaryTable,outTable,fromFields,[toField],reportingUnitIdField,None)
    
    # Set up a calculation expression for the final density calculation
    calcExpression = "!" + toField + "!/!" + ruArea + "!"
    # Calculate the population density
    vector.addCalculateField(outTable,metricConst.populationDensityFieldName + index,calcExpression)


def getPolygonPopCount(inPolygonFeature,inPolygonIdField,inCensusFeature,inPopField,classField,
                  outTable,metricConst,index=""):
    """ Performs a transfer of population from input census features to input polygon features using simple
        areal weighting.  
    
    **Description:**

        This function uses Tabulate Intersection to construct a table with a field containing the area weighted
        population count for each input polygon unit. The population field is renamed from the metric constants entry.
        Finally, fields in the constructed table are trimmed down to just the Polygon Id field, the population count
        field, and any required fields such as OID.
        
    **Arguments:**

        * *inPolygonFeature* - input Polygon feature class with full path.
        * *inPolygonIdField* - the name of the field in the reporting unit feature class containing a unique identifier
        * *inCensusFeature* - input population feature class with full path
        * *inPopField* - the name of the field in the population feature class containing count values
        * *classField* - a field in the population feature class with a constant value
        * *outTable* -  the output table that will contain calculated population values
        * *metricConst* - an ATtILA2 object containing constant values to match documentation
        * *index* - if this function is going to be run multiple times, this index is used to keep track of intermediate
                    outputs and field names.
        
    **Returns:**

        * None
        
    """
    # Construct a table with a field containing the area weighted population count for each input polygon unit
    arcpy.TabulateIntersection_analysis(inPolygonFeature,[inPolygonIdField],inCensusFeature,outTable,[classField],[inPopField])
    
    # Rename the population count field.
    outPopField = metricConst.populationCountFieldNames[index]
    arcpy.AlterField_management(outTable, inPopField, outPopField, outPopField)
    
def replaceNullValues(inTable,inField,newValue):
    # Replace NULL values in a field with the supplied value
    whereClause = inField+" IS NULL"
    updateCursor = arcpy.UpdateCursor(inTable, whereClause, "", inField)
    for updateRow in updateCursor:
        updateRow.setValue(inField, newValue)
        # Persist all of the updates for this row.
        updateCursor.updateRow(updateRow)
        # Clean up our row element for memory management and to remove locks
        del updateRow
    # Clean up our row element for memory management and to remove locks
    del updateCursor
    
def percentageValue(inTable, numeratorField, denominatorField, percentField):
    # Set up a calculate percentage expression 
    calcExpression = "getValuePercent(!"+numeratorField+"!,!"+denominatorField+"!)"
    codeBlock = """def getValuePercent(n,d):
                        if d == 0:
                            if n == 0:
                                return 0
                            else:
                                return 1
                        else:
                            return (n/d)*100"""
    
    # Calculate and record the percent population within view area
    vector.addCalculateField(inTable, percentField, calcExpression, codeBlock)
def differenceValue(inTable, totalField, subtratorField, resultField):
    # Set up a calculate percentage expression 
    calcExpression = "getValueDifference(!"+totalField+"!,!"+subtratorField+"!)"
    codeBlock = """def getValueDifference(n,d):
                        return (n-d)"""
    
    # Calculate and record the percent population within view area
    vector.addCalculateField(inTable, resultField, calcExpression, codeBlock)

def belowValue(inTable, sourceField, threshold, addedField):
    # Set up a calculate percentage expression 
    calcExpression = "getValuePercent(!"+sourceField+"!, "+ threshold + ")"
    codeBlock = """def getValuePercent(n, d):
                        if n < d:
                            return 1
                        else:
                            return 0"""
    
    # Calculate and record the percent population within view area
    vector.addCalculateFieldInteger(inTable, addedField, calcExpression, codeBlock)

