'''
Created on Nov 18, 2011

@author: mjacks07

Constants specific to metric tools  
'''

# Common Variables
tbxSourceFolderName = "ToolboxSource"
noFeaturesMessage = "Dataset exists, but there are no features (zero rows)"
inputIdFieldTypes = ["SmallInteger", "Integer", "String"]
userOption = "User Defined"
optionalFieldsName = "Additional Options"
descriptionDelim = "  -  "
areaFieldParameters = ["_A","DOUBLE",15,0]
srcFolderSuffix = ".src"
tbxFileSuffix = ".tbx"
tbxFileDelim = "__"
tbxSriptToolDelim = "#"
metricDescription = "{0}" + descriptionDelim + "[{1}]  {2}"
qaCheckName = "QAFIELDS"
metricAddName = "AREAFIELDS"
intermediateName = "INTERMEDIATES"
qaCheckDescription = "{0}{1}Add Quality Assurance Fields".format(qaCheckName, descriptionDelim)
metricAddDescription = "{0}{1}Add Area Fields for All Land Cover Classes".format(metricAddName, descriptionDelim)
intermediateDescription = "{0}{1}Retain Intermediate Layers Generated During Metric Calculation".format(intermediateName, descriptionDelim)

# Metric Names Used for Lookup
lcpMetricName = "LandCoverProportions"
rpMetricName = "RiparianProportions"
lcsoMetricName = "LandCoverSlopeOverlap"

# Land Cover Proportions Specific Variables
lcpOptionalFieldsFilter = [qaCheckDescription, metricAddDescription]

# Land Cover and Slope Overlap
lcsoOptionalFieldsFilter = [qaCheckDescription, metricAddDescription, intermediateDescription]