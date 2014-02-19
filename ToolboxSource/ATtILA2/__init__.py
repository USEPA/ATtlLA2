#  Created:  Mar 12, 2012
#  Author:  mjacks07, Michael A. Jackson, jackson.michael@epa.gov, majgis@gmail.com

''' Redirect import of ATtILA2 to ATtILA2/ATtILA2

'''


import os
import sys

RELATIVE_VALUE = -1  # Directories to step up:  -1 = . (packages only), -2 = .. , -3 = ... , etc.
PATH_APPEND = []  # After step up, append this sub path, example: ['foo', 'bar'] -> /foo/bar is appended

pth = os.path.sep.join(__file__.split(os.path.sep)[0:RELATIVE_VALUE] + PATH_APPEND)
sys.path.insert(0, pth)

del sys.modules[__name__] 
import ATtILA2