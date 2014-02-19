""" Variable constants for tool dialog validation routines

"""

import globalConstants as gc

tbxSourceFolderName = "ToolboxSource"

inputIdFieldTypes = ["SmallInteger", "Integer", "String"]
userOption = "User Defined"
optionalFieldsName = "Additional Options"
metricDescription = "{0}" + gc.descriptionDelim + "[{1}]  {2}"
noFeaturesMessage = "Dataset exists, but there are no features (zero rows)"
noSpatialReferenceMessage = "Dataset is missing spatial reference information. Please define projection before proceeding."
noSpatialReferenceMessageMulti = "One or more datasets is missing spatial reference information. \
Please define a projection for all input datasets before proceeding."
nonIntegerGridMessage = "Input requires an integer grid. Selected dataset not an integer grid."
nonPositiveNumberMessage = "Input requires a positive number. Please enter a value greater than zero before proceeding."