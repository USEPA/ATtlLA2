''' Land Cover Classification(LCC) Constants

    These constants are specific to .lcc XML files including the XML elements
    and attributes used to define the classification.
    
    Last modified 12/09/13

'''


# Files
XmlFileExtension = ".xml"
PredefinedFileDirName = "LandCoverClassifications"
UserDefinedOptionDescription = "User Defined"
AutoSaveFileName = "autoSave.xml"
TimeInterval = 5000     # 1 sec = 1000 millseconds
overwriteFieldList = ['flcpField', 'lcospField', 'lcpField', 'rlcpField', 'splcpField']


# XML Elements
XmlElementClasses = "classes"
XmlElementClass = "class"
XmlElementValues = "values"
XmlElementValue = "value"
XmlElementMetadata = "metadata"
XmlElementMetaname = "name"
XmlElementMetadescription = "description"
XmlElementCoefficient = "coefficient"
XmlElementCoefficients = "coefficients"


# XML Attributes
XmlAttributeId = "Id"
XmlAttributeName = "Name"
XmlAttributeDescription = "description"
XmlAttributeNodata = "excluded"
XmlAttributeFlcpField = "flcpField"
XmlAttributeLcospField = "lcospField"
XmlAttributeLcpField = "lcpField"
XmlAttributeRlcpField = "rlcpField"
XmlAttributeSplcpField = "splcpField"
XmlAttributeFilter = "filter"
XmlAttributeValue = "value"
XmlAttributeFieldName = "fieldName"
XmlAttributeCalcMethod = "method"

# XML Validation Attributes
XsdFilename = 'LCCSchema.xsd'
XmlAttilaNamespace = 'lcc'
XmlSchemaNamespace = 'http://www.w3.org/2001/XMLSchema-instance'
ItemsRootAttribute1 = {'xmlns:xsi': XmlSchemaNamespace}
ItemsRootAttribute2 = {'xmlns':XmlAttilaNamespace}
ItemsRootAttribute3 = {'xsi:noNamespaceSchemaLocation':XsdFilename}
XmlValidation = [ItemsRootAttribute1, ItemsRootAttribute2, ItemsRootAttribute3]
