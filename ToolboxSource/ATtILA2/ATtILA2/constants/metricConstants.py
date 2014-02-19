import globalConstants as gc


class baseMetricConstants():
    """  """
    name = ''
    shortName = ''
    fieldPrefix = ''
    fieldSuffix = ''
    overlapName = ''
    totalAreaName = ''
    effectiveAreaName = ''
    excludedAreaName = ''
    optionalFilter = []
    fieldParameters = []
    qaCheckFieldParameters = []    
    fieldOverrideKey = ''
    additionalFields = []

class lcdConstants(baseMetricConstants):
    name = "LandCoverDiversity"
    shortName = "lcd"
    fieldPrefix = ""
    fieldSuffix = ""
    overlapName = "LCD_OVER"
    totalAreaName = ""
    effectiveAreaName = ""
    excludedAreaName = ""
    optionalFilter = [gc.qaCheckDescription, gc.intermediateDescription]
    fieldParameters = [fieldPrefix,fieldSuffix, gc.defaultDecimalFieldType, 8, 4]
    qaCheckFieldParameters = [
                              [overlapName, gc.defaultIntegerFieldType, 6]
                              ]
    fieldOverrideKey = shortName + gc.fieldOverrideName
    fixedMetricsToRun = 'H  -  Shannon Weiner;H_Prime  -  Standardized Shannon Weiner;C  -  Simpson;S  -  Simple'

class lcpConstants(baseMetricConstants):
    name = "LandCoverProportions"
    shortName = "lcp"
    fieldPrefix = "p"
    fieldSuffix = ""
    overlapName = "LCP_OVER"
    totalAreaName = "LCP_TOTA"
    effectiveAreaName = "LCP_EFFA"
    excludedAreaName = "LCP_EXCA"
    optionalFilter = [gc.qaCheckDescription, gc.metricAddDescription, gc.intermediateDescription]
    fieldParameters = [fieldPrefix,fieldSuffix, gc.defaultDecimalFieldType, 6, 1]
    qaCheckFieldParameters = [
        [overlapName, gc.defaultIntegerFieldType, 6],
        [totalAreaName, gc.defaultAreaFieldType, 15],
        [effectiveAreaName, gc.defaultAreaFieldType, 15],
        [excludedAreaName, gc.defaultAreaFieldType, 15]
        ]   
    fieldOverrideKey = shortName + gc.fieldOverrideName
    
class lcospConstants(baseMetricConstants):
    name = "LandCoverOnSlopeProportions"
    shortName = "lcosp"
    fieldSuffix = "SL"
    fieldPrefix = ""
    overlapName = "LCOSP_OVER"
    totalAreaName = "LCOSP_TOTA"
    effectiveAreaName = "LCOSP_EFFA"
    excludedAreaName = "LCOSP_EXCA"
    optionalFilter = [gc.qaCheckDescription, gc.metricAddDescription, gc.intermediateDescription]
    fieldParameters = [fieldPrefix, fieldSuffix, gc.defaultDecimalFieldType,6,1]
    qaCheckFieldParameters = [
        [overlapName, gc.defaultIntegerFieldType, 6],
        [totalAreaName, gc.defaultAreaFieldType, 15],
        [effectiveAreaName, gc.defaultAreaFieldType, 15],
        [excludedAreaName, gc.defaultAreaFieldType, 15]
        ]
    fieldOverrideKey = shortName + gc.fieldOverrideName

class lcccConstants(baseMetricConstants):
    name = "LandCoverCoefficientCalculator"
    shortName = "lccc"
    fieldPrefix = ""
    fieldSuffix = ""
    overlapName = "LCCC_OVER"
    totalAreaName = ""
    effectiveAreaName = ""
    excludedAreaName = ""
    optionalFilter = [gc.qaCheckDescription, gc.intermediateDescription]
    fieldParameters = [fieldPrefix,fieldSuffix, gc.defaultDecimalFieldType, 7, 2]
    qaCheckFieldParameters = [
        [overlapName, gc.defaultIntegerFieldType, 6]
        ]    
    fieldOverrideKey = shortName + gc.fieldOverrideName
    perUnitAreaMetrics = ("NITROGEN", "PHOSPHORUS")
    percentageMetrics = ("IMPERVIOUS")
    

class rlcpConstants(baseMetricConstants):
    name = "RiparianLandCoverProportions"
    shortName = "rlcp"
    fieldPrefix = "r"
    fieldSuffix = ""
    overlapName = "RLCP_OVER"
    totalAreaName = "RLCP_TOTA"
    effectiveAreaName = "RLCP_EFFA"
    excludedAreaName = "RLCP_EXCA"
    optionalFilter = [gc.qaCheckDescription, gc.metricAddDescription, gc.intermediateDescription]
    fieldParameters = [fieldPrefix, fieldSuffix, gc.defaultDecimalFieldType, 6, 1]
    qaCheckFieldParameters = [
        [overlapName, gc.defaultIntegerFieldType, 6],
        [totalAreaName, gc.defaultAreaFieldType, 15],
        [effectiveAreaName, gc.defaultAreaFieldType, 15],
        [excludedAreaName, gc.defaultAreaFieldType, 15]                                        
        ]
    fieldOverrideKey = shortName + gc.fieldOverrideName

class splcpConstants(baseMetricConstants):
    name = "SamplePointLandCoverProportions"
    shortName = "splcp"
    fieldPrefix = "s"
    fieldSuffix = ""
    overlapName = "SPLCP_OVER"
    totalAreaName = "SPLCP_TOTA"
    effectiveAreaName = "SPLCP_EFFA"
    excludedAreaName = "SPLCP_EXCA"
    optionalFilter = [gc.qaCheckDescription, gc.metricAddDescription, gc.intermediateDescription]
    fieldParameters = [fieldPrefix, fieldSuffix, gc.defaultDecimalFieldType, 6, 1]
    qaCheckFieldParameters = [
        [overlapName, gc.defaultIntegerFieldType, 6],
        [totalAreaName, gc.defaultAreaFieldType, 15],
        [effectiveAreaName, gc.defaultAreaFieldType, 15],
        [excludedAreaName, gc.defaultAreaFieldType, 15]                                        
        ]
    fieldOverrideKey = shortName + gc.fieldOverrideName
    
class caemConstants(baseMetricConstants):
    name = "CoreAndEdgeMetrics"
    shortName = "caem"
    fieldPrefix = ""
    fieldSuffix = "_E2A"
    overlapName = "CAEM_OVER"
    totalAreaName = "CAEM_TOTA"
    effectiveAreaName = "CAEM_EFFA"
    excludedAreaName = "CAEM_EXCA"
    optionalFilter = [gc.qaCheckDescription, gc.intermediateDescription]
    fieldParameters = [fieldPrefix, fieldSuffix, gc.defaultDecimalFieldType, 6, 1]
    qaCheckFieldParameters = [
        [overlapName, gc.defaultIntegerFieldType, 6],
        [totalAreaName, gc.defaultAreaFieldType, 15],
        [effectiveAreaName, gc.defaultAreaFieldType, 15],
        [excludedAreaName, gc.defaultAreaFieldType, 15]                                        
        ]
    fieldOverrideKey = shortName + gc.fieldOverrideName
    coreSuffix = "_COR"
    edgeSuffix = "_EDG"
    additionalSuffixes = [coreSuffix, edgeSuffix]
    coreField = ["", coreSuffix, gc.defaultDecimalFieldType, 6, 1]
    edgeField = ["", edgeSuffix, gc.defaultDecimalFieldType, 6, 1]
    additionalFields = [coreField, edgeField]
    
class rdmConstants(baseMetricConstants):
    name = "RoadDensityMetrics"
    shortName = "rdm"
    fieldPrefix = ""
    fieldSuffix = ""
    overlapName = ""
    totalAreaName = ""
    effectiveAreaName = ""
    excludedAreaName = ""
    optionalFilter = [gc.intermediateDescription]
    fieldParameters = [fieldPrefix, fieldSuffix, gc.defaultDecimalFieldType, 6, 1]
    qaCheckFieldParameters = []
    fieldOverrideKey = shortName + gc.fieldOverrideName
    areaFieldname = "AREAKM2"
    roadDensityFieldName = "RDDENS"
    roadLengthFieldName = "RDKM"
    streamDensityFieldName = "STRMDENS"
    streamLengthFieldName = "STRMKM"
    totalImperviousAreaFieldName = "RDTIA"
    streamRoadXingsCountFieldname = "XCNT"
    xingsPerKMFieldName = "STXRD"
    rnsFieldName = "RNS"
    roadsByReportingUnitName = [shortName+"_RdsByRU","FeatureClass"]
    streamsByReportingUnitName = [shortName+"_StrByRU","FeatureClass"]
    roadStreamMultiPoints = [shortName+"_RdsXStrMP","FeatureClass"]
    roadStreamIntersects = [shortName+"_PtsOfXing","FeatureClass"]
    roadStreamSummary = [shortName+"_RdsXStrTbl","Dataset"]
    streamBuffers = [shortName+"_StrBuffers","FeatureClass"]
    roadsNearStreams = [shortName+"_RdsNrStrms","FeatureClass"]

class sdmConstants(baseMetricConstants):
    name = "StreamDensityMetric"
    shortName = "sdm"
    fieldPrefix = ""
    fieldSuffix = ""
    overlapName = ""
    totalAreaName = ""
    effectiveAreaName = ""
    excludedAreaName = ""
    optionalFilter = [gc.intermediateDescription]
    fieldParameters = [fieldPrefix, fieldSuffix, gc.defaultDecimalFieldType, 6, 1]
    qaCheckFieldParameters = []
    fieldOverrideKey = shortName + gc.fieldOverrideName
    areaFieldname = "AREAKM2"
    lineLengthFieldName = "STRMKM"
    lineDensityFieldName = "STRMDENS"
    linesByReportingUnitName = [shortName+"_StrByRU","FeatureClass"]
    
class pdmConstants(baseMetricConstants):
    name = "PopulationDensityMetrics"
    shortName = "pdm"
    fieldPrefix = ""
    fieldSuffix = ""
    overlapName = ""
    totalAreaName = ""
    effectiveAreaName = ""
    excludedAreaName = ""
    optionalFilter = [gc.intermediateDescription]
    fieldParameters = [fieldPrefix, fieldSuffix, gc.defaultDecimalFieldType, 6, 1]
    qaCheckFieldParameters = []
    fieldOverrideKey = shortName + gc.fieldOverrideName
    areaFieldname = "AREAKM2"
    populationDensityFieldName = "POPDENS"
    populationChangeFieldName = "POPCHG"
    intersectOutputName = shortName+"_intersectOutput"
    summaryTableName = shortName+"_summaryTable"
    
class mdcpConstants(baseMetricConstants):
    name = "MeanDisttoClosestPatch"
    shortName = "mdcp"
    fieldPrefix = ""
    fieldSuffix = "MDCP"
    overlapName = "MDCP_OVER"
    totalAreaName = "MDCP_TOTA"
    effectiveAreaName = "MDCP_EFFA"
    excludedAreaName = "MDCP_EXCA"
    rastertoPoly = [shortName+"_FinalPatchPoly","FeatureClass"]
    rastertoPoint = [shortName+"_FinalPatchCentroids", "FeatureClass"]
    polyDissolve = [shortName+"_FinalPatch_poly_diss", "FeatureClass"]
    clipPolyDissolve =[shortName+"_FinalPatch_poly_diss_clip", "FeatureClass"]
    nearTable = [shortName+"_NearTable", "Dataset"]
    optionalFilter = [gc.qaCheckDescription, gc.metricAddDescription, gc.intermediateDescription]
    fieldParameters = [fieldPrefix, fieldSuffix, gc.defaultDecimalFieldType, 6, 1]
    qaCheckFieldParameters = [
        [overlapName, gc.defaultIntegerFieldType, 6],
        [totalAreaName, gc.defaultAreaFieldType, 15],
        [effectiveAreaName, gc.defaultAreaFieldType, 15],
        [excludedAreaName, gc.defaultAreaFieldType, 15]                                        
        ]
    fieldOverrideKey = shortName + gc.fieldOverrideName
