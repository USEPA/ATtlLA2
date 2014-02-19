''' Error Constants
'''

errorLookup = {
'ERROR 010092':'''You have an invalid output extent.  This error can occur in the following circumstances:
  1) Some input datasets do not overlap
  2) The extent in your environment settings does not overlap the input datasets
  3) Another extent related issue\n'''}

errorCommentPrefix = "Error Comments:\n---------------\n"
errorDetailsPrefix = "\nError Details:\n--------------\n"
errorUnknown = "Unexpected Error"

linearUnitConversionError = '''Unable to determine conversion factor necessary to convert output linear units to metric units.

Please be sure that the Environment Settings > Output Coordinates are not set to a system defined with angular units of 
Decimal Degrees. If an Environment Settings > Output Coordinates is not set, please be sure to select an 'Input reporting
unit feature' that does not have a spatial reference defined with angular units of decimal degrees. 

It is also possible for this error to occur if the linear units defined in the Output Coordinates, if one is set, or the 
'Input reporting unit feature', if an Output Coordinates is not set, is not found in ATtILA's look up table. Please 
compare your linear units with those found in the ATtILA Help file.'''

nonOverlappingExtentsError = '''Input features do not overlap. Unable to perform spatial analysis.

Please be sure that the areal extent of the input Reporting unit features overlaps with the areal extent of all other input layers. '''