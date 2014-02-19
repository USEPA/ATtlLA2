""" Deployment Script

    This script zips the ATtILA2 toolbox for a deployable module following these steps:
    
    Into an empty directory, copy the following files and folders:
    
        ..\ATtILA2\src\ATtILA2.tbx
    
        ..\ATtILA2\src\ToolboxSource Folder
            it should contain just two subfolders (ATtILA2 and LandCoverClassifications) and no files except those in the two subfolders
            from the ATtILA2 subfolder, delete the tests subfolder
    
        ..\ATtILA2\src\pylet\pylet Folder
            This folder should be copied and placed in the ToolboxSource Folder
            all of it's files and subfolders are included
    
    In ..\ToolboxSource\ATtILA2\scripts rename the file 'RENAME-TO--ATtILA2.py--ON-DEPLOY.py' to 'ATtILA2.py'
    
    Make sure no hidden files or folders are accidentally copied into the new distribution folder. The hidden .git folders, used for version control, are massive and unnecessary for deployment. They shouldn't be in any of the copied folders, but better to be safe than sorry.
    
    Zip the newly populated folder and distribute.
"""

import os, sys, zipfile, shutil
from datetime import date

def zipws(path, zip, keep):
    ''' Function for zipping files.  
    
    **Description:**
        
        Recursively zips all content in the specified path
        
    **Arguments:**
    
        * *path* - file system path to be zipped
        * *zip* - name of output zip file
        * *keep* - If keep is true, the folder, along with all its contents, will be written to the zip file.  If false,
                     only the contents of the input folder will be written to the zip file - the input folder name will 
                     not appear in the zip file.
    '''
    path = os.path.normpath(path)
    # os.walk visits every subdirectory, returning a 3-tuple
    #  of directory name, subdirectories in it, and file names
    #  in it.
    #
    for (dirpath, dirnames, filenames) in os.walk(path):
        # Iterate over every file name
        #
        for file in filenames:
            try:
                if keep:
                    zip.write(os.path.join(dirpath, file),
                    os.path.join(os.path.basename(path), os.path.join(dirpath, file)[len(path)+len(os.sep):]))
                else:
                    zip.write(os.path.join(dirpath, file),            
                    os.path.join(dirpath[len(path):], file)) 
                    
            except Exception, e:
                print "    Error adding %s: %s" % (file, e)

    return None

def copyFolder(sourceFolder, destFolder, ignoreFiles):
    '''Simple function to allow us to specify a target folder for copying other folders
    '''
    outputFolder = os.path.join(destFolder,os.path.basename(sourceFolder))
    shutil.copytree(sourceFolder,outputFolder,symlinks=False, ignore=ignoreFiles)

def main(_argv):
    
    d = date.today()
    dateStr = d.strftime("%Y%b%d")
    
    outputDir = 'ATtILA_Deployment'
    toolbox = 'ATtILA 10_0.tbx'
    tbSource = 'ToolboxSource'
    pylet = '../pylet'
    outputZip = 'ATtILA_'+dateStr+'.zip'
    ignoreFiles = shutil.ignore_patterns('.git*','.settings','.project','.pydevproject','*.lfn','*.wsp','tests',
                                         'AutoSave','apidoc','CutAndPaste','*.bak','*.bat')
    
    # First create our output directory for staging the deployment.
    # If the directory already exists, remove it.
    if os.path.exists(outputDir):
        shutil.rmtree(outputDir)
    os.mkdir(outputDir)
    
    # Copy the necessary files and folders to our output directory.
    shutil.copy2(toolbox,outputDir)
    copyFolder(tbSource,outputDir,ignoreFiles)
    copyFolder(pylet,os.path.join(outputDir,tbSource),ignoreFiles)
    
    # Rename the ATtILA2.py file
    inName = os.path.join(outputDir,'ToolboxSource\\ATtILA2\\scripts\\RENAME-TO--ATtILA2.py--ON-DEPLOY.py')
    outName = os.path.join(outputDir,'ToolboxSource\\ATtILA2\\scripts\\ATtILA2.py')
    os.rename(inName,outName)
    
    # Remove the previous zipfile if it exists
    if os.path.exists(outputZip):
        os.remove(outputZip)
    # Create the zip file
    zip = zipfile.ZipFile(outputZip, 'w', zipfile.ZIP_DEFLATED)
    zipws(outputDir, zip, False)
    zip.close()
    
    # Clean up the staging output directory
    shutil.rmtree(outputDir)
    
if __name__ == "__main__":
    main(sys.argv)