""" Land Cover Proportion Metrics

    This script is associated with an ArcToolbox script tool.
    
"""


import sys
from ATtILA2 import metric
from pylet.arcpyutil import parameters


def main(_argv):
    
    # Script arguments
    inputArguments = parameters.getParametersAsText([2])
    
    metric.runLandCoverCoefficientCalculator(*inputArguments)
    
    
if __name__ == "__main__":
    main(sys.argv)
    