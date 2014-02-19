''' Redirect import of ATtILA2 to a relative location.

    This script is required for deployment, when the user does not have packages on their PythonPath.
    
    The ToolboxSource directory is effectively added to the PythonPath by its position relative to this script.
    
    If you are also importing pylet, you must make sure to import this module first so that pylet can be found.

'''


import os
import sys

RELATIVE_VALUE = -3  # Directories to step up:  -1 = . (packages only), -2 = .. , -3 = ... , etc.
PATH_APPEND = []  # After step up, append this sub path, example: ['foo', 'bar'] -> /foo/bar is appended

pth = os.path.sep.join(__file__.split(os.path.sep)[0:RELATIVE_VALUE] + PATH_APPEND)
sys.path.insert(0, pth)

del sys.modules[__name__] 
import ATtILA2