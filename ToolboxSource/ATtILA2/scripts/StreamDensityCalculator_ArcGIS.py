""" Stream Density

    This script is associated with an ArcToolbox script tool.
    
"""


import sys
from ATtILA2 import metric
from pylet.arcpyutil import parameters

def main(_argv):
    
    # Script arguments
    inputArguments = parameters.getParametersAsText([])
    
    metric.runStreamDensityCalculator(*inputArguments)

if __name__ == "__main__":
    main(sys.argv)