'''
Test to evaluate consistency of Population Density Calculation routine

Created May 2013

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
            
        print "Running Population Density calculation"
        ATtILA2.metric.runPopulationDensityCalculator(p.rdinReportingUnitFeature, p.rdreportingUnitIdField, 
                                                      p.inCensusFeature, p.inPopField,p.outTable,p.popChangeYN,
                                                      p.inCensusFeature2, p.inPopField2, p.rdoptionalFieldGroups)

    
        print "Testing Population Density results"
        #results = outputValidation.compare(p.refLandCoverOutput,p.outTable)
        
        #print results
    
    except Exception, e:
        ATtILA2.errors.standardErrorHandling(e)
        
if __name__ == '__main__':
    runTest()
