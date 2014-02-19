""" Launch the Land Cover Classification (LCC) Editor

    Launches the external editor for .lcc files from a toolbox tool
    The editor is started in a separate process, remaining open when ArcGIS is closed.
    
    The extra python script is used as a work-around for UserAccountControl dialog showing
    behind geoprocessing window when launched directly.
    
    No Arguments.
"""

import sys
import os
import arcpy

def main(_argv):
      
    currentFolderPath = os.path.dirname(__file__)
    binFolderName = "dist"
    exeName = r"LCCEditor.pyw" 
    startMsg = "\nThe full path to the executable that will be launched:"
    indentMsg = "    "
    endMsg = "\n"+"You may close ArcGIS without disrupting the editor."+"\n"
    
    pywPath = os.path.join(currentFolderPath, binFolderName, exeName)
    exePath = pywPath.replace('.pyw', '.exe')
    
    arcpy.AddMessage(startMsg)
    arcpy.AddMessage(indentMsg + exePath)
    arcpy.AddMessage(endMsg)
    
    os.startfile(pywPath)

    
if __name__ == "__main__":
    main(sys.argv)