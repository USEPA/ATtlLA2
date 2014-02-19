'''
Test to evaluate consistency of Land Cover Coefficient Calculation

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
            
        print "Running LandCoverCoefficient calculation"
        '''runLandCoverCoefficientCalculator(inReportingUnitFeature, reportingUnitIdField, inLandCoverGrid, _lccName, 
                                      lccFilePath, metricsToRun, outTable, processingCellSize, snapRaster, 
                                      optionalFieldGroups)'''
        ATtILA2.metric.runLandCoverCoefficientCalculator(p.inReportingUnitFeature, p.reportingUnitIdField, 
                                                      p.inLandCoverGrid, p._lccName, p.lccFilePath, p.metricsToRun_LCC,
                                                      p.outTable, p.processingCellSize, p.snapRaster, 
                                                      p.optionalFieldGroups_LCC)
    
        print "Testing LandCoverCoefficient results"
        results = outputValidation.compare(p.refLandCoverCoefficient,p.outTable)
        
        print results
    
    except Exception, e:
        ATtILA2.errors.standardErrorHandling(e)
        
if __name__ == '__main__':
    runTest()