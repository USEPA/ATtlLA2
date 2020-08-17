""" Launch the Land Cover Classification (LCC) Editor
 
    Workaround for issue where User Account Control (UAC) dialog appeared behind geoprocessing window using os.startfile 
    with .exe.  

"""


import os
currentFolder = os.path.dirname(__file__)
exeName = 'LCCEditor.exe'
exePath = os.path.join(currentFolder, exeName)
#exePath = os.path.join("D:\ATtILA2\src\ATtILA2\ToolboxSource\ATtILA2\scripts\bin", "LCCEditor.exe")
#exePath = os.path.join("D:\ATtILA2\src\LCCEditor\LCCEditor\gui", "__init__.py")
os.startfile(exePath)
