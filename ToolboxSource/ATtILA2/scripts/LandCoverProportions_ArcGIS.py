""" Land Cover Proportion Metrics

    This script is associated with an ArcToolbox script tool
    
"""
from pylet.arcpyutil import parameters
from ATtILA2 import metrics
import sys

def main(argv):
    
    # Script arguments
    inputArguments = parameters.getParametersAsText([0])
    
    metrics.common.landCoverProportions(*inputArguments)
    
    
if __name__ == "__main__":
    main(sys.argv)
    