''' Utilities for conversions unique to ArcGIS

'''

def getGeometryConversionFactor(linearUnits, dimension):
    """ Returns conversion factor for converting a value to either meters or square meters. """
        
    if dimension.upper() == 'LENGTH':
        conversionFactor = getMeterConversionFactor(linearUnits)
    elif dimension.upper() == 'AREA':
        conversionFactor = getSqMeterConversionFactor(linearUnits)
    else:
        conversionFactor = 0
    
    return conversionFactor


def convertToMeters(measure, linearUnit, decimalPlaces=2):
    """ Convert distance in a specified linear unit to meters.
    
    **Description:**
        
        The first argument is a string, integer or float representing a distance measure.  This value is converted 
        to meters by applying a conversion factor. The result is then rounded to the number of decimal places specified 
        in the third argument (the default is two decimal places).  A float is always returned. If the linear unit is 
        not found in the conversion dictionary, a value of 0 is returned.  
        
    **Arguments:**
        
        * *measure* - A string, integer or float representing a distance measure
        * *linearUnit* - A string with the ArcGIS 10 linear unit type description
        * *decimalPlaces* - An integer to specify the number of decimal places to round to
    
    **Returns:**
        * float
        
    """      
    
    conversionFactor = getMeterConversionFactor(linearUnit)
    meters = float(measure) * conversionFactor
    
    return round(meters, decimalPlaces)


def convertToSqMeters(measure, linearUnit, decimalPlaces=2):
    """ Convert distance in a specified linear unit to square meters.
    
    **Description:**
        
        The first argument is a string, integer or float representing an area measure.  This value is converted 
        to square meters by applying a conversion factor. The result is then rounded to the number of decimal places 
        specified in the third argument (the default is two decimal places).  A float is always returned. If the linear 
        unit is not found in the conversion dictionary, a value of 0 is returned.  
        
    **Arguments:**
        
        * *measure* - A string, integer or float representing an area measure
        * *linearUnit* - A string with the ArcGIS 10 linear unit type description
        * *decimalPlaces* - An integer to specify the number of decimal places to round to
    
    **Returns:**
        * float
        
    """      
    
    conversionFactor = getSqMeterConversionFactor(linearUnit)
    meters = float(measure) * conversionFactor
    
    return round(meters, decimalPlaces)


def getMeterConversionFactor(linearUnitName):
    """ Provides the conversion factor necessary to convert values in an ArcGIS 10 linear unit type to meters.
    
    **Description:**
        
        The 'linearUnitName' argument is the linear unit description used in ArcGIS 10 Geographic Coordinate Systems.
        The conversion factor to convert distance measures to meters is returned. A float is always returned. If the
        linearUnitName is not found in the dictionary, an exception occurs.   
        
    **Arguments:**
        
        * *linearUnitName* - A string representing the linear unit description used in ArcGIS 10 Geographic Coordinate Systems
    
    **Returns:**
        * float
        
    """ 
        
    conversionDict = dict({
                           '150_Kilometers': 150000.0,
                           '50_Kilometers': 50000.0,
                           'Centimeter': 0.01,
                           'Chain': 20.1168,
                           'Chain_Benoit_1895_A': 20.1167824,
                           'Chain_Benoit_1895_B': 20.1167824943759,
                           'Chain_Clarke': 20.11661949,
                           'Chain_Sears': 20.1167651215526,
                           'Chain_US': 20.1168402336805,
                           'Decimeter': 0.1,
                           'Fathom': 1.8288,
                           'Foot': 0.3048,
                           'Foot_1865': 0.304800833333333,
                           'Foot_Benoit_1895_A': 0.304799733333333,
                           'Foot_Benoit_1895_B': 0.304799734763271,
                           'Foot_British_1936': 0.3048007491,
                           'Foot_Clarke': 0.304797265,
                           'Foot_Gold_Coast': 0.304799710181509,
                           'Foot_Indian': 0.304799510248147,
                           'Foot_Indian_1937': 0.30479841,
                           'Foot_Indian_1962': 0.3047996,
                           'Foot_Indian_1975': 0.3047995,
                           'Foot_Sears': 0.304799471538676,
                           'Foot_US': 0.304800609601219,
                           'Inch': 0.0254,
                           'Inch_US': 0.0254000508001016,
                           'Kilometer': 1000.0,
                           'Link': 0.201168,
                           'Link_Benoit_1895_A': 0.201167824,
                           'Link_Benoit_1895_B': 0.201167824943759,
                           'Link_Clarke': 0.2011661949,
                           'Link_Sears': 0.201167651215526,
                           'Link_US': 0.201168402336805,
                           'Meter': 1.0,
                           'Meter_German': 1.0000135965,
                           'Mile_US': 1609.34721869444,
                           'Millimeter': 0.001,
                           'Nautical_Mile': 1852.0,
                           'Nautical_Mile_UK': 1853.184,
                           'Nautical_Mile_US': 1853.248,
                           'Rod': 5.0292,
                           'Rod_US': 5.02921005842012,
                           'Statute_Mile': 1609.344,
                           'Yard': 0.9144,
                           'Yard_Benoit_1895_A': 0.9143992,
                           'Yard_Benoit_1895_B': 0.914399204289812,
                           'Yard_Clarke': 0.914391795,
                           'Yard_Indian': 0.914398530744441,
                           'Yard_Indian_1937': 0.91439523,
                           'Yard_Indian_1962': 0.9143988,
                           'Yard_Indian_1975': 0.9143985,
                           'Yard_Sears': 0.914398414616029,
                           'Yard_Sears_1922_Truncated': 0.914398,
                           'Yard_US': 0.914401828803658
                           })

    try:
        conversionFactor = conversionDict[linearUnitName]
        return conversionFactor
    except:
        raise


def getSqMeterConversionFactor(linearUnitName):
    """ Provides the conversion factor necessary to convert values in an ArcGIS 10 linear unit type to square meters.
    
    **Description:**
        
        The 'linearUnitName' argument is the linear unit description used in ArcGIS 10 Geographic Coordinate Systems.
        The conversion factor to convert area measures to square meters is returned. A float is always returned. If the
        linearUnitName is not found in the dictionary, an exception occurs.   
        
    **Arguments:**
        
        * *linearUnitName* - A string representing the linear unit description used in ArcGIS 10 Geographic Coordinate Systems
    
    **Returns:**
        * float
        
    """ 
        
    conversionDict = dict({
                           '150_Kilometers': 22500000000.0,
                           '50_Kilometers': 2500000000.0,
                           'Centimeter': 0.0001,
                           'Chain': 404.68564224,
                           'Chain_Benoit_1895_A': 404.68493412895,
                           'Chain_Benoit_1895_B': 404.684937926029,
                           'Chain_Clarke': 404.678379705448,
                           'Chain_Sears': 404.684238955715,
                           'Chain_US': 404.687260987426,
                           'Decimeter': 0.01,
                           'Fathom': 3.34450944,
                           'Foot': 0.09290304,
                           'Foot_1865': 0.092903548000694,
                           'Foot_Benoit_1895_A': 0.092902877440071,
                           'Foot_Benoit_1895_B': 0.09290287831176,
                           'Foot_British_1936': 0.092903496651921,
                           'Foot_Clarke': 0.09290137275148,
                           'Foot_Gold_Coast': 0.092902863326732,
                           'Foot_Indian': 0.09290274144751,
                           'Foot_Indian_1937': 0.092902070738528,
                           'Foot_Indian_1962': 0.09290279616016,
                           'Foot_Indian_1975': 0.09290273520025,
                           'Foot_Sears': 0.092902717850256,
                           'Foot_US': 0.092903411613275,
                           'Inch': 0.00064516,
                           'Inch_US': 0.000645162580648,
                           'Kilometer': 1000000.0,
                           'Link': 0.040468564224,
                           'Link_Benoit_1895_A': 0.040468493412895,
                           'Link_Benoit_1895_B': 0.040468493792603,
                           'Link_Clarke': 0.040467837970545,
                           'Link_Sears': 0.040468423895572,
                           'Link_US': 0.040468726098743,
                           'Meter': 1.0,
                           'Meter_German': 1.00002719318486,
                           'Mile_US': 2589998.47031953,
                           'Millimeter': 0.000001,
                           'Nautical_Mile': 3429904.0,
                           'Nautical_Mile_UK': 3434290.937856,
                           'Nautical_Mile_US': 3434528.149504,
                           'Rod': 25.29285264,
                           'Rod_US': 25.2929538117141,
                           'Statute_Mile': 2589988.110336,
                           'Yard': 0.83612736,
                           'Yard_Benoit_1895_A': 0.83612589696064,
                           'Yard_Benoit_1895_B': 0.836125904805841,
                           'Yard_Clarke': 0.836112354763322,
                           'Yard_Indian': 0.836124673027593,
                           'Yard_Indian_1937': 0.836118636646753,
                           'Yard_Indian_1962': 0.83612516544144,
                           'Yard_Indian_1975': 0.83612461680225,
                           'Yard_Sears': 0.836124460652307,
                           'Yard_Sears_1922_Truncated': 0.836123702404,
                           'Yard_US': 0.836130704519474
                           })

    try:
        conversionFactor = conversionDict[linearUnitName]
        return conversionFactor
    except:
        raise


def getTransformMethod(inDataset1,inDataset2):
    """ Checks to see if a transformation method is needed to project geodatasets. If so, returns the most likely. """
    
    import arcpy
    # Determine if a transformation method is needed to project datasets (e.g. different datums are used). 
    desc1 = arcpy.Describe(inDataset1)
    desc2 = arcpy.Describe(inDataset2)
    spatial1 = desc1.spatialReference
    spatial2 = desc2.spatialReference
    transformList = arcpy.ListTransformations(spatial1, spatial2, desc2.extent)
    if len(transformList) == 0:
        # if no list is returned; no transformation is required
        transformMethod = ""
    else:
        # default to the first transformation method listed. ESRI documentation indicates this is typically the most suitable
        transformMethod = transformList[0]

    return transformMethod