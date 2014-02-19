'''
Master module to run all metric tests

Created July, 2012

@author: thultgren Torrin Hultgren, hultgren.torrin@epa.gov
'''
import landCoverProportionsTest
import landCoverOnSlopeProportionsTest
import landCoverCoefficientTest
import riparianLandCoverTest

def runTests():
    landCoverProportionsTest.runTest()
    landCoverOnSlopeProportionsTest.runTest()
    landCoverCoefficientTest.runTest()
    riparianLandCoverTest.runTest()

if __name__ == '__main__':
    runTests()