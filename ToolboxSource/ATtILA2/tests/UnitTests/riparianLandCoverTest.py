'''
Test to evaluate consistency of Riparian LandCover Proportions Calculation

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
            
        print "Running RiparianLandCoverProportions calculation"
        ATtILA2.metric.runRiparianLandCoverProportions(p.inReportingUnitFeature, p.reportingUnitIdField, 
                                                      p.inLandCoverGrid, p._lccName, p.lccFilePath, p.metricsToRun_RLC,
                                                      p.inStreamFeatures, p.inBufferDistance, p.outTable, 
                                                      p.processingCellSize, p.snapRaster, p.optionalFieldGroups)
    
        print "Testing RiparianLandCoverProportions results"
        results = outputValidation.compare(p.refRiparianLandCover,p.outTable)
        
        print results
    
    except Exception, e:
        ATtILA2.errors.standardErrorHandling(e)
        
if __name__ == '__main__':
    runTest()