'''
Input and output parameters for all metric tests.  
Created July, 2012

@author: thultgren Torrin Hultgren, hultgren.torrin@epa.gov
'''

# General Parameters for all tools
baseDir = 'C:\\temp\\ATtILA2_data\\testData\\'  # Set this to your root folder
inReportingUnitFeature = baseDir + "reportingUnitsQuick.shp"
reportingUnitIdField = "ID_USE1"
inLandCoverGrid = baseDir + "nlcd00"
_lccName = 'NLCD 2001'
lccFilePath = r'C:\sync\ATtILA2\SourceCode\ATtILA2\ToolboxSource\LandCoverClassifications\NLCD 2001.xml'  
outTable = baseDir + 'TestOutput'
processingCellSize = '30' 
snapRaster = inLandCoverGrid  # Set by default to the input LandCover Grid, may be changed.
optionalFieldGroups = "'QAFIELDS  -  Add Quality Assurance Fields';'AREAFIELDS  -  Add Area Fields for All Land Cover Classes'"
inStreamFeatures = baseDir + 'nhd_msite.shp'

# Parameters unique to LandCoverProportions
refLandCoverOutput = baseDir + 'LandCoverReference.dbf' # Reference output data
metricsToRun_LCP = "'nat  -  [NINDEX]  All natural land use';'for  -  [pfor]  Forest';'wtlt  -  [pwtlt]  All Wetlands';'wtlw  -  [pwtlw]  Woody Wetland';'wtle  -  [pwtle]  Emergent Herbaceous Wetland';'shrb  -  [pshrb]  Shrubland';'hrbt  -  [phrbt]  All Herbaceous';'hrbg  -  [phrbg]  Grassland, Herbaceous';'hrbo  -  [phrbo]  Herbaceous Other';'bart  -  [pbart]  Barren';'unat  -  [UINDEX]  All human land use';'devt  -  [pdevt]  All Developed';'devo  -  [pdevo]  Developed, Open Space';'devl  -  [pdevl]  Developed, Low Intensity';'devm  -  [pdevm]  Developed, Medium Intensity';'devh  -  [pdevh]  Developed, High Intensity';'agt  -  [pagt]  All Agriculture';'agp  -  [pagp]  Pasture';'agc  -  [pagc]  Cultivated Crops'"


# Parameters unique to LandCoverOnSlopeProportionsTest
refLandCoverOnSlopeOutput = baseDir + 'LandCoveronSlopeReference.dbf' # Reference output data
metricsToRun_LCSP = "'agt  -  [agtSL]  All Agriculture';'agp  -  [agpSL]  Pasture';'agc  -  [agcSL]  Cultivated Crops'"
inSlopeGrid = baseDir + 'slope_pct'
inSlopeThresholdValue = '10'


# Parameters unique to LandCoverCoefficient
refLandCoverCoefficient = baseDir + 'LandCoverCoefficientReference.dbf' # Reference output data
metricsToRun_LCC = "'IMPERVIOUS  -  [PCTIA]  Percent Cover Total Impervious Area';'NITROGEN  -  [N_Load]  Estimated Nitrogen Loading Based on Land Cover';'PHOSPHORUS  -  [P_Load]  Estimated Phosphorus Loading Based on Land Cover'"
optionalFieldGroups_LCC = "'QAFIELDS  -  Add Quality Assurance Fields'"  # Only metric with different optional Field Groups


# Parameters unique to riparianLandCoverTest
refRiparianLandCover = baseDir + 'riparianLandCoverReference.dbf' # Reference output data
metricsToRun_RLC = "'nat  -  [rnat]  All natural land use';'for  -  [rfor]  Forest';'wtlt  -  [rwtlt]  All Wetlands';'wtlw  -  [rwtlw]  Woody Wetland';'wtle  -  [rwtle]  Emergent Herbaceous Wetland';'shrb  -  [rshrb]  Shrubland';'hrbt  -  [rhrbt]  All Herbaceous';'hrbg  -  [rhrbg]  Grassland, Herbaceous';'hrbo  -  [rhrbo]  Herbaceous Other';'bart  -  [rbart]  Barren';'unat  -  [runat]  All human land use';'devt  -  [rdevt]  All Developed';'devo  -  [rdevo]  Developed, Open Space';'devl  -  [rdevl]  Developed, Low Intensity';'devm  -  [rdevm]  Developed, Medium Intensity';'devh  -  [rdevh]  Developed, High Intensity';'agt  -  [ragt]  All Agriculture';'agp  -  [ragp]  Pasture';'agc  -  [ragc]  Cultivated Crops'"
inBufferDistance = '100' 


# Parameters unique to Road Density Metrics
rdinReportingUnitFeature = baseDir + "reportingUnitsQuick.shp"
rdreportingUnitIdField = "ID_USE1"
inRoadFeature = baseDir + "mroads.shp"
roadClassField = "" #"ACC"
streamsByRoads = True
roadsNearStreams = True
bufferDistance = "50 meters"
rdoptionalFieldGroups = "'INTERMEDIATES  -  Retain Intermediate Layers Generated During Metric Calculation'" # "#" #

# Parameters unique to Population Density Calculation
inCensusFeature = baseDir + "blkgrp2000.shp"
inPopField = "MALES"
popChangeYN = True
inCensusFeature2 = baseDir + "blkgrp2000.shp"
inPopField2 = "FEMALES"