'''
Test to evaluate consistency of Land Cover on Slope Proportion Calculation

Created July 2012

@author: thultgren Torrin Hultgren, hultgren.torrin@epa.gov
'''

import arcpy
import ATtILA2
import parameters as p
import outputValidation

def runTest():
    try:
        if arcpy.Exists(p.outTable):
            arcpy.Delete_management(p.outTable)
            
        print "Running LandCoverOnSlopeProportion calculation"
        ATtILA2.metric.runLandCoverOnSlopeProportions(p.inReportingUnitFeature, p.reportingUnitIdField, 
                                                      p.inLandCoverGrid, p._lccName, p.lccFilePath, p.metricsToRun_LCSP,
                                                      p.inSlopeGrid, p.inSlopeThresholdValue, p.outTable, 
                                                      p.processingCellSize, p.snapRaster, p.optionalFieldGroups)
    
        print "Testing LandCoverOnSlopeProportion results"
        results = outputValidation.compare(p.refLandCoverOnSlopeOutput,p.outTable)
        
        print results
    
    except Exception, e:
        ATtILA2.errors.standardErrorHandling(e)
        
if __name__ == '__main__':
    runTest()