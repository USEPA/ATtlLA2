""" Global, application level variables

"""
titleATtILA = "ATtILA"
descriptionDelim = "  -  "
areaFieldParameters = ["_A","DOUBLE",15,0]
tbxFileSuffix = ".tbx"
tbxFileDelim = "__"
tbxSriptToolDelim = "#"
qaCheckName = "QAFIELDS"
metricAddName = "AREAFIELDS"
intermediateName = "INTERMEDIATES"
qaCheckDescription = "{0}{1}Add Quality Assurance Fields".format(qaCheckName, descriptionDelim)
metricAddDescription = "{0}{1}Add Area Fields for All Land Cover Classes".format(metricAddName, descriptionDelim)
intermediateDescription = "{0}{1}Retain Intermediate Layers Generated During Metric Calculation".format(intermediateName, descriptionDelim)
defaultDecimalFieldType = "FLOAT"
defaultIntegerFieldType = "SHORT"
defaultAreaFieldType = "DOUBLE"
fieldOverrideName = "Field"
metricNameTooLong = "Provided metric name too long for output location. Truncated {0} to {1} "
tabulateAreaTableAbbv = "_TabArea"
scratchGDBFilename = "attilaScratchWorkspace.gdb"