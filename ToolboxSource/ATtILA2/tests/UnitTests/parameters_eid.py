'''
Input and output parameters for all metric tests.  
Created March 2013

@author: thultgren Torrin Hultgren, hultgren.torrin@epa.gov, modified by Ellen D'Amico for Core/Edge Metric
'''

# General Parameters for all tools
baseDir = r'C:\Projects\default\Default.gdb'  # Set this to your root folder
inReportingUnitFeature = baseDir + "\\Subwatersheds_1stOrder"
reportingUnitIdField = "SuperID"
inLandCoverGrid = r"C:\Projects\default\Default.gdb\al_nlcd06_LM"
_lccName = 'NLCD 2001'
lccFilePath = r'C:\Projects\M_Mehaffey\Attila2\python\ATtILA2\ToolboxSource\LandCoverClassifications\NLCD 2001.xml'  
outTable = r"c:\projects\default\default.gdb\\"+ 'TestOutput_MDCP_patch2'
processingCellSize = '30' 
snapRaster = inLandCoverGrid  # Set by default to the input LandCover Grid, may be changed.
#optionalFieldGroups = "'QAFIELDS  -  Add Quality Assurance Fields';'AREAFIELDS  -  Add Area Fields for All Land Cover Classes'"
optionalFieldGroups = "'INTERMEDIATES  -  Retain Intermediate Layers Generated During Metric Calculation'" 

#inStreamFeatures = baseDir + 'nhd_msite.shp'
# Parameters unique to LandCoverProportions
refLandCoverOutput = baseDir + 'LandCoverReference.dbf' # Reference output data
metricsToRun = "'for  -  [pfor]  Forest'"

inEdgeWidth = "1"

maxSeparation = 0
minPatchSize = 2
SearchRadius = "200"

## Parameters unique to LandCoverOnSlopeProportionsTest
#refLandCoverOnSlopeOutput = baseDir + 'LandCoveronSlopeReference.dbf' # Reference output data
metricsToRun_LCP = "'agt  -  [agtSL]  All Agriculture';'agp  -  [agpSL]  Pasture';'agc  -  [agcSL]  Cultivated Crops'"
#inSlopeGrid = baseDir + 'slope_pct'
#inSlopeThresholdValue = '10'


## Parameters unique to LandCoverCoefficient
#refLandCoverCoefficient = baseDir + 'LandCoverCoefficientReference.dbf' # Reference output data
#metricsToRun_LCC = "'IMPERVIOUS  -  [PCTIA]  Percent Cover Total Impervious Area';'NITROGEN  -  [N_Load]  Estimated Nitrogen Loading Based on Land Cover';'PHOSPHORUS  -  [P_Load]  Estimated Phosphorus Loading Based on Land Cover'"
#optionalFieldGroups_LCC = "'QAFIELDS  -  Add Quality Assurance Fields'"  # Only metric with different optional Field Groups


# Parameters unique to riparianLandCoverTest
#refRiparianLandCover = baseDir + 'riparianLandCoverReference.dbf' # Reference output data
#metricsToRun_RLC = "'nat  -  [rnat]  All natural land use';'for  -  [rfor]  Forest';'wtlt  -  [rwtlt]  All Wetlands';'wtlw  -  [rwtlw]  Woody Wetland';'wtle  -  [rwtle]  Emergent Herbaceous Wetland';'shrb  -  [rshrb]  Shrubland';'hrbt  -  [rhrbt]  All Herbaceous';'hrbg  -  [rhrbg]  Grassland, Herbaceous';'hrbo  -  [rhrbo]  Herbaceous Other';'bart  -  [rbart]  Barren';'unat  -  [runat]  All human land use';'devt  -  [rdevt]  All Developed';'devo  -  [rdevo]  Developed, Open Space';'devl  -  [rdevl]  Developed, Low Intensity';'devm  -  [rdevm]  Developed, Medium Intensity';'devh  -  [rdevh]  Developed, High Intensity';'agt  -  [ragt]  All Agriculture';'agp  -  [ragp]  Pasture';'agc  -  [ragc]  Cultivated Crops'"
#inBufferDistance = '100' 


# Parameters unique to Road Density Metrics
rdinReportingUnitFeature = baseDir + "reportingUnitsQuick.shp"
rdreportingUnitIdField = "ID_USE1"
inRoadFeature = baseDir + "mroads.shp"
roadClassField = "" #"ACC"
streamsByRoads = True
roadsNearStreams = True
bufferDistance = "50 meters"
rdoptionalFieldGroups = "'INTERMEDIATES  -  Retain Intermediate Layers Generated During Metric Calculation'" # "#" #