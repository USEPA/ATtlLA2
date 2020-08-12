""" Road Density Metrics

    This script is associated with an ArcToolbox script tool.
    
"""


import sys
from ATtILA2 import metric
#from pylet.utils import parameters
from ..ATtILA2.utils import parameters

def main(_argv):
    
    # Script arguments
    inputArguments = parameters.getParametersAsText([0, 2, 7])
    
    metric.runRoadDensityCalculator(*inputArguments)

if __name__ == "__main__":
    main(sys.argv)