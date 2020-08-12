""" This module contains utilities for parameters accessed using `arcpy`_, a Python package associated with ArcGIS. 

    .. _arcpy: http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#/What_is_ArcPy/000v000000v7000000/
    .. _arcpy.GetParameterAsText: http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#//000v00000014000000
"""

import arcpy

PARAMETER_ENCLOSURE = "'"



def getParametersAsText(indexesForCatalogPath = []):
    """ Get a list of all arcpy parameters as text.

        **Description:**
        
        Uses `arcpy.GetParameterAsText`_ to assemble a list of strings representing parameters from the script that is 
        being executed. ie. the input parameters for an ArcGIS toolbox dialog box, an ArcGIS modelbuilder model, or
        another python script, etc.
        
        The optional *indexesForCatalogPath* argument allows you to indicate which indexes must have
        the full catalog path retrieved. For example, if the layer name is the text returned for the parameter, you can 
        request the full path of the dataset for that parameter by adding its index to a list passed to this function. 
        
        This seems to be most critical for input parameters - the code produces an error for output parameters, so 
        don't include them in the list of integer indexes       
        
        **Arguments:**
        
        * *indexesForCatalogPath* - Iterable with integer indexes of parameters to get a catalog path for.
        
        
        **Returns:** 
        
        * list of strings
    
    """ 
  
    textParameters = []
    total = arcpy.GetArgumentCount()
    for count in range(0,total):
        try:
            if count in indexesForCatalogPath:
    #                if hasattr(arcpy.GetParameter(count), "value"):
    #                    arcpy.AddMessage("Parameter {0} has value attibute".format(count))
    #                else:
    #                    arcpy.AddMessage("Parameter {0} has NO value attibute".format(count))
                    
                # check if input parameter is a lyr file with arcpy.Exists
                if arcpy.Exists(arcpy.GetParameter(count)):
                    parameterAsText = arcpy.Describe(arcpy.GetParameter(count)).catalogPath.strip("'")
                else:
                    parameterAsText = arcpy.Describe(arcpy.GetParameter(count).dataSource).catalogPath.strip("'")
            else:
                parameterAsText = arcpy.GetParameterAsText(count).strip("'")
                
            textParameters.append(parameterAsText)
        except:
            # We're going to make an assumption that something went wrong with getting parameters, and to preserve
            # the argument index, add an ESRI null "#".  
            textParameters.append("#")
    
    return textParameters   

def splitItemsAndStripDescriptions(delimitedString, descriptionDelim, parameterDelim=";"):
    """ Splits a string of delimited item-description pairs to a list of items.

        **Description:**
        
        This function first splits a string of one or more delimited item-description pairs into a list of 
        item-description pairs.  It then proceeds to strip off the descriptions, leaving just a list of the items. 
        These items are also stripped of leading and trailing whitespace.
        
        For example, these inputs::
            
            descriptionDelim = " - "
            delimitedString = 'item1  -  description1;item2  -  description2' 
        
        result in this output::
        
            ['item1','item2']
        
        
        **Arguments:**
        
        * *delimitedString* - the full delimited string
        * *descriptionDelim* - The delimeter for item descriptions.  Descriptions are stripped off
        * *parmeterDelim* - The delimiter for parameters.  The default is a semi-colon.
        
        
        **Returns:** 
        
        * List of strings
        
        
        
    """    

    
    delimitedString = delimitedString.replace(PARAMETER_ENCLOSURE,"")
    
    itemsWithDescription = delimitedString.split(parameterDelim)
    
    itemsWithoutDescription = [itemWithDescription.split(descriptionDelim)[0].strip() for itemWithDescription in itemsWithDescription]
    
    return itemsWithoutDescription
