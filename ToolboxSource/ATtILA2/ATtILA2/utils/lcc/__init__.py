""" This module contains utilities specific to Land Cover Classification(LCC) XML files. 

    Each class reflects a different portion of the information stored in the XML file. These LCC XML files should have 
    a .xml file extension.
    
    To access a file, use :py:class:`LandCoverClassification` as the entry point.  
    
    .. _Node: http://docs.python.org/library/xml.dom.html#node-objects    
    .. _frozenset: http://docs.python.org/library/stdtypes.html#frozenset
    .. _dict: http://docs.python.org/library/stdtypes.html#dict
    
"""

' Last Modified 12/15/13'

from xml.dom import minidom
import os
import sys
from . import constants
import copy
from glob import glob
from collections import defaultdict
from xml.dom.minidom import NamedNodeMap

class LandCoverMetadata(object):
    """ This class holds all the metadata properties associated with the single LCC metadata-`Node`_.

    **Description:**
        
        This class holds all of the information stored within the <metadata> tag of a LCC XML file.          
        
    **Arguments:**
        
        * *metadataNode* - metadata-`Node`_ loaded from a lcc file
       
    """
    
    #: The name of the Land Cover Classification
    name = None
    
    #: A description of the Land Cover Classification
    description = None
    
    def __init__(self, metadataNode=None):
    
        self.name = " "
        self.description = " "
        
        if not metadataNode is None:
            self._loadLccMetadataNode(metadataNode)

    def _loadLccMetadataNode(self, metadataNode):
        """  This method Loads a LCC metadata-`Node`_ to assign all properties associated with this class.        
        
        **Description:**
            
            If the LCC metadata-`Node`_ was not provided as an argument when this class was instantiated, you can load one
            to assign all properties associated with this class.
            
            See the class description for additional details
                    
        """
        
        self.name = metadataNode.getElementsByTagName(constants.XmlElementMetaname)[0].firstChild.nodeValue
        self.description = metadataNode.getElementsByTagName(constants.XmlAttributeDescription)[0].firstChild.nodeValue
     
    def doesMetaDataExist(self):
        """ This method checks to see if there is any Meta Data in the control class 
        
        **Description:**
            
            This method checks the control class and returns either true or false, depending on if the Meta Data exists.
        
        **Arguments:**
            
            None
            
        **Returns:**
            
            True/False
            
        """
        if not self.name and not self.description:
            return False
         
        return True            

class LandCoverBaseClass(object):
    #: The unique identifier for the class
    classId = None
    
    #: The name of the class
    name = None
    
    #: A `list`_ of all unique identifiers for Values of all descendants
    uniqueValueIds = None
    
    #: A `list`_ of all unique identifiers for Classes of all descendants 
    uniqueClassIds = None
    
    #: A `dict`_ for all XML attributes associated with the class-`Node`_
    attributes = None
    
    #: A `LandCoverClass`_ object for the parent of this class
    parentClass = None
    
    #: A `list`_ of child classes
    childClasses = None
    
    #: A `list`_ of valueIds for all child values
    childValueIds = None
    
    #: A 'dict'_ of overwriteFields used for any class will contain 
        #: 'flcpField, lcospField, lcpField, rlcpField and splcpField'
    classoverwriteFields = None
    
    _excludeEmptyClasses = None
        
    def __init__(self, classNode=None, parentClass=None, excludeEmptyClasses=True):
        
        self.parentClass = parentClass
        self._excludeEmptyClasses = excludeEmptyClasses
        
        self.classoverwriteFields = {}
        
        for field in constants.overwriteFieldList:
            self.classoverwriteFields[field] = None
        if not classNode is None:
            self._loadLccClassNode(classNode)
        else:
            self.attributes = {}
    
    def getSize(self):
#         print "init:", self.__init__.__sizeof__()
#         print "getsize:", self.getSize.__sizeof__()
#         print "_load:", self._loadLccClassNode.__sizeof__()
#         print "getclassoverwrite", self.getClassLcpAttributes.__sizeof__()
#         print "classId", self.classId.__sizeof__()
#         print "name", self.name.__sizeof__()
#         print "uniqueValueIds",self.uniqueValueIds, self.uniqueValueIds.__sizeof__()
#         print "uniqueClassIds" ,self.uniqueClassIds, self.uniqueClassIds.__sizeof__()
#         print "attributes", self.attributes, self.attributes.__sizeof__()
#         print "parentClass", self.parentClass.__sizeof__()
#         print "childClasses", self.childClasses, self.childClasses.__sizeof__()
#         print "childValueIds", self.childValueIds, self.childValueIds.__sizeof__()
#         print "classoverwriteFields", self.classoverwriteFields, self.classoverwriteFields.__sizeof__()
#         print "_excludeEmptyClasses", self._excludeEmptyClasses, self._excludeEmptyClasses.__sizeof__()
        objectSum = self.__init__.__sizeof__() + self.getSize.__sizeof__() + \
            self._loadLccClassNode.__sizeof__() + self.getClassLcpAttributes.__sizeof__() + \
            self.classId.__sizeof__() + self.name.__sizeof__() + self.uniqueValueIds.__sizeof__() + \
            self.uniqueClassIds.__sizeof__() + self.attributes.__sizeof__() + \
            self.parentClass.__sizeof__() + self.childClasses.__sizeof__() + \
            self.childValueIds.__sizeof__() + self.classoverwriteFields.__sizeof__() + \
            self._excludeEmptyClasses.__sizeof__()
            
        return objectSum
    
    def _loadLccClassNode(self, xmlClassNode):
        """  This method Loads a LCC class-`Node`_ to assign all properties associated with this class.        
        
        **Description:**
            
            If the LCC class-`Node`_ was not provided as an argument when this class was instantiated, you can load 
            one to assign all properties associated with this class.                        
            
           See the class description for additional details
           
        """   
        
        for attrIterator in xmlClassNode.attributes.items():
            if str(attrIterator[0]) == constants.XmlAttributeId or str(attrIterator[0]) == constants.XmlAttributeName \
                    or str(attrIterator[0]) == 'filter':
                continue
            self.classoverwriteFields[str(attrIterator[0])] = str(attrIterator[1]) 
        
        # Load class attributes as object properties
        self.classId = str(xmlClassNode.getAttribute(constants.XmlAttributeId))
        self.name = str(xmlClassNode.getAttribute(constants.XmlAttributeName))
        
        # Process child nodes
        if isinstance(self, LandCoverClass):    
            uniqueClassIds = set()
            uniqueValueIds = set()
        elif isinstance(self, EditorLandCoverClass):
            uniqueClassIds = []
            uniqueValueIds = []
        else:
            print("Error identifing child class")
            return
        
        self.childClasses = []
        self.childValueIds = []
        
        for childNode in xmlClassNode.childNodes:
            if isinstance(childNode, minidom.Element):
                
                # Process child classes
                if childNode.tagName == constants.XmlElementClass:
                    
                    # Point of recursion...bottom-most classes are processed first.
                    if isinstance(self, LandCoverClass):
                        landCoverClass = LandCoverClass(childNode, self, self._excludeEmptyClasses)
                    elif isinstance(self, EditorLandCoverClass):
                        landCoverClass = EditorLandCoverClass(childNode, self, self._excludeEmptyClasses)
                    else:
                        print("What the Hell")
                        return
                    # Assemble child classes
                    self.childClasses.append(landCoverClass)

                    if landCoverClass.childClasses or landCoverClass.childValueIds:
                        
                        # Add child classId to uniqueClassIds
                        uniqueClassIds.append(landCoverClass.classId)
                        
                        # Add uniqueClassIds of child
                        uniqueClassIds.extend(landCoverClass.uniqueClassIds)
                        
                        # Add uniqueValueIds of child
                        uniqueValueIds.extend(landCoverClass.uniqueValueIds)
            
                # Process child values
                elif childNode.tagName == constants.XmlElementValue:
                    valueId = int(childNode.getAttribute(constants.XmlAttributeId))
                    self.childValueIds.append(valueId)
                    uniqueValueIds.append(valueId)
                
        # Get unique IDs from child classes
        if isinstance(self, LandCoverClass):
            self.uniqueClassIds = frozenset(uniqueClassIds)
            self.uniqueValueIds = frozenset(uniqueValueIds)
        elif isinstance(self, EditorLandCoverClass):
            self.uniqueClassIds = uniqueClassIds
            self.uniqueValueIds = uniqueValueIds
        else:
            print("We should have never gotten her, but just incase")
            
        #Load all attributes into dictionary
        self.attributes = {}
        for attributeName, attributeValue in xmlClassNode.attributes.items():
            self.attributes[str(attributeName)] = str(attributeValue)

    def getClassLcpAttributes(self):
        """ Gets class Lcp Attributes """
        lcpAttributeList = []
        for keyIterable in self.classoverwriteFields.keys():
            if not self.classoverwriteFields[keyIterable] == None:
                lcpAttributeList.append(str(self.classoverwriteFields[keyIterable]))
        return lcpAttributeList
    
class LandCoverClass(LandCoverBaseClass):
    """ This class holds all of the properties associated with a LCC class-`Node`_.

    **Description:**
        
        This class holds all of the information stored in a <class> tag within a LCC XML file.  Values may be 
        duplicated in child classes, but only unique valueIds are reported.        
        
    **Arguments:**
        
        * *classNode* - LCC class-`Node`_ loaded from a lcc file
        * *parentClass* - The parent :py:class:`LandCoverClass` object


    """
    __parentLccObj = None
                  
    def _loadLccClassNode(self, classNode):
        """  This method Loads a LCC class-`Node`_ to assign all properties associated with this class.        
        
        **Description:**
            
            If the LCC class-`Node`_ was not provided as an argument when this class was instantiated, you can load 
            one to assign all properties associated with this class.                        
            
           See the class description for additional details
           
        """   
 
        # Load class attributes as object properties
        self.classId = str(classNode.getAttribute(constants.XmlAttributeId))
        self.name = str(classNode.getAttribute(constants.XmlAttributeName))
            
        # Process child nodes
        uniqueClassIds = set()
        uniqueValueIds = set()
        self.childClasses = []
        self.childValueIds = []
        
        for childNode in classNode.childNodes:
            
            if isinstance(childNode, minidom.Element):
                
                # Process child classes
                if childNode.tagName == constants.XmlElementClass:
                    
                    # Point of recursion...bottom-most classes are processed first.
                    landCoverClass = LandCoverClass(childNode, self, self._excludeEmptyClasses)
                    
                    
                    if landCoverClass.childClasses or landCoverClass.childValueIds:
                        # Assemble child classes
                        self.childClasses.append(landCoverClass)
                        
                        # Add child classId to uniqueClassIds
                        uniqueClassIds.add(landCoverClass.classId)
                        
                        # Add uniqueClassIds of child
                        uniqueClassIds.update(landCoverClass.uniqueClassIds)
                        
                        # Add uniqueValueIds of child
                        uniqueValueIds.update(landCoverClass.uniqueValueIds)
            
                # Process child values
                elif childNode.tagName == constants.XmlElementValue:
                    valueId = int(childNode.getAttribute(constants.XmlAttributeId))
                    self.childValueIds.append(valueId)
                    uniqueValueIds.add(valueId)
                
        # Get unique IDs from child classes
        self.uniqueClassIds = frozenset(uniqueClassIds)
        self.uniqueValueIds = frozenset(uniqueValueIds)
        
        #Load all attributes into dictionary
        self.attributes = {}
        for attributeName, attributeValue in classNode.attributes.items():
            self.attributes[str(attributeName)] = str(attributeValue)
       
    def addClass(self, classId, name, classFilter=None, overwriteField=None):            # *************************************
#        print "Filter is ", filter
        print("\n***************************")
        print("IN ADDCLASS in LandCoverClass")
        print("*****************************")
        self.classId = classId
        self.name = name
        if classFilter:
            self.attributes['classFilter'] = str(classFilter)
        if overwriteField:
            self.attributes['overwriteField'] = str(overwriteField)
        self.attributes['id'] = str(classId)
        self.attributes['name'] = str(name)
        
#        topLevelClass = 
#        classId = id
#        name = className        
class EditorLandCoverClass(LandCoverBaseClass):
    """ This class holds all of the properties associated with a LCC class-`Node`_.

    **Description:**
        
        This class holds all of the information stored in a <class> tag within a LCC XML file.  Values may be 
        duplicated in child classes, but only unique valueIds are reported.        
        
    **Arguments:**
        
        * *classNode* - LCC class-`Node`_ loaded from a lcc file
        * *parentClass* - The parent :py:class:`LandCoverClass` object

    """
     
    __parentLccObj = None
                    
    def _loadLccClassNode(self, classNode):
        """  This method Loads a LCC class-`Node`_ to assign all properties associated with this class.        
        
        **Description:**
            
            If the LCC class-`Node`_ was not provided as an argument when this class was instantiated, you can load 
            one to assign all properties associated with this class.                        
            
           See the class description for additional details
           
        """   

        for attrIterator in classNode.attributes.items():
            if str(attrIterator[0]) == constants.XmlAttributeId or str(attrIterator[0]) == constants.XmlAttributeName \
                    or str(attrIterator[0]) == 'filter':
                continue
            self.classoverwriteFields[str(attrIterator[0])] = str(attrIterator[1]) 
        
        # Load class attributes as object properties
        self.classId = str(classNode.getAttribute(constants.XmlAttributeId))
        self.name = str(classNode.getAttribute(constants.XmlAttributeName))
            
        # Process child nodes
        uniqueClassIds = []
        uniqueValueIds = []
        self.childClasses = []
        self.childValueIds = []
        
        for childNode in classNode.childNodes:
            if isinstance(childNode, minidom.Element):
                
                # Process child classes
                if childNode.tagName == constants.XmlElementClass:
                    
                    # Point of recursion...bottom-most classes are processed first.
                    landCoverClass = EditorLandCoverClass(childNode, self, self._excludeEmptyClasses)
                    
                    # Assemble child classes
                    self.childClasses.append(landCoverClass)

                    if landCoverClass.childClasses or landCoverClass.childValueIds:
                        
                        # Add child classId to uniqueClassIds
                        uniqueClassIds.append(landCoverClass.classId)
                        
                        # Add uniqueClassIds of child
                        uniqueClassIds.extend(landCoverClass.uniqueClassIds)
                        
                        # Add uniqueValueIds of child
                        uniqueValueIds.extend(landCoverClass.uniqueValueIds)
            
                # Process child values
                elif childNode.tagName == constants.XmlElementValue:
                    valueId = int(childNode.getAttribute(constants.XmlAttributeId))
                    self.childValueIds.append(valueId)
                    uniqueValueIds.append(valueId)
                
        # Get unique IDs from child classes
        self.uniqueClassIds = uniqueClassIds
        self.uniqueValueIds = uniqueValueIds
        
        #Load all attributes into dictionary
        self.attributes = {}
        for attributeName, attributeValue in classNode.attributes.items():
            self.attributes[str(attributeName)] = str(attributeValue)
       
    def addClass(self, classId, name, overwriteField):
        """ 
            Adding a new class node with data to control class. 
         
        **Description:**
            This method takes data entered in the appropriate dialog and stores it in the control class.   
         
        **Arguments:**
            * *classId* - Alphanumeric identifier that the control class uses to reference node data
            * *name* - Descriptive title of the node data
            * *overwriteField* - 
         
        **Returns:**
            * None
    """
                     
        self.classId = str(classId)
        self.name = str(name)
        self.attributes[constants.XmlAttributeId] = str(classId)
        self.attributes[constants.XmlAttributeName] = str(name)
 
        # For attributes
        for overwriteFieldKey in overwriteField:
            self.attributes[str(overwriteFieldKey)] = str(overwriteField[overwriteFieldKey])
         
        # for overwriteField
        for iterKey in overwriteField.keys():
            self.classoverwriteFields[str(iterKey)] = str(overwriteField[iterKey])
             
        self.childClasses = []
        self.childValueIds = []
        self.uniqueClassIds = []
        self.uniqueValueIds = []
    
    def getUniqueValueIds(self):
        """ Gets the Unique Value Ids' """
        return self.uniqueValueIds 
       
    def addNewUniqueId(self,newId):
        """ Adds New Unique Id """
        self.uniqueClassIds.append(newId)
    
    def removeUniqueId(self,uniqueId):
        """ Removes Unique Id """
        self.uniqueClassIds.remove(uniqueId)
    
    def addNewValueId(self,newId):
        """ Adds New Value Id """
        if isinstance(newId, unicode):
            newId = int(newId)
        self.uniqueValueIds.append(newId)
        self.childValueIds.append(newId)
    
    def addNewValueToUniqueValueIdsNodeList(self, newId):
        """ Adds New Value to Unique Value Ids node list """
        if isinstance(newId, unicode):
            newId = int(newId)
        self.uniqueValueIds.append(newId)

    def removeValueId(self,newId):
        """ Removes Value Id """
        if isinstance(newId, unicode):
            newId = int(newId)
        self.uniqueValueIds.remove(newId)
        if self.childValueIds:
            self.childValueIds.remove(newId) 
    
    def getValueIds(self):
        """ It Gets the Value Ids' or it get's the hose again """
        return self.uniqueValueIds
        
    def isName(self, checkName):
        """ Returns bool if name is a match """
        if self.attributes[constants.XmlAttributeName].lower() == checkName.lower():
            return True
        return False
    
    def isLeaf(self):
        """ Returns true if node has values assigned to it. """
        if not self.childClasses and self.uniqueValueIds:
            return True        
        return False
    
    def canAddValuesToClassNode(self):
        """ Returns true if can add value to class node """
        if self.childClasses:
            return False
        return True
   
    def canAddChildToClassNode(self):
        """ Returns true if can add child to class node """
        if self.childValueIds:
            return False
        return True
   
    def isValueInSet(self, valueId):
        """ Checks if value is in set """
        if valueId in self.uniqueValueIds:
            return True
        return False
 
    def hasValues(self):
        """ Checks is child value has values """
        if self.childValueIds:
            return True
        return False
        
    def getChildrenClasses(self):
        """ Gets the children classes """
        return self.uniqueClassIds
                            
    def setParentClass(self, parentClass):
        """ Sets the parent class """
        self.parentClass = parentClass

class LandCoverBaseClasses(dict):
    """ This class holds all :py:class:`LandCoverClass` objects.

    **Description:**

        This class holds all of the :py:class:`LandCoverClass` objects loaded from the LCC XML file.          

    **Arguments:**

        * Not applicable

    """
    
    #: Boolean for exclusion of empty classes
    excludeEmptyClasses = None
    
    #: Top level classes which reside in the root of the <classes> node and have no parent
    topLevelClasses = None

    def __init__(self, classesNode=None, excludeEmptyClasses=True):

        self.excludeEmptyClasses = excludeEmptyClasses
        if not classesNode is None:
            self._loadClassesNode(classesNode)
                                 
    def _getDescendentClasses(self, landCoverClass):
        """ 
            This gets and returns descendent classes 
            
            **Description:**
                This method is a helper method of _loadClassesNode.  Do to our control class having top level nodes
                and descendent nodes from those top level nodes, a helper function is required to recursively on all
                the children.
            
            **Arguments:**
                * *landCoverClass* - xml element to be parsed 
            
            **Returns:**
                * desendentClasses
        """         
        descendentClasses = []
 
        for childClass in landCoverClass.childClasses:
            descendentClasses += self._getDescendentClasses(childClass)
            descendentClasses.append(childClass)       
         
        return descendentClasses
     
    def addTopLevelClass(self, LandCoverClass):
        """ 
            Adds a new top level class node to control class. 
            
            **Description:**
                This method allows us to add node to the separate top level control class for our truncated tree due
                to the fact that the person who wrote this originally is a big moron.  Frankly it is a miracle he got 
                hired by google.  Cause some of his decisions are down right bizarre.  In fact, he is definitely not 
                getting a Christmas (pagan) card from me.....
            
            **Arguments:**
                * *landCoverClass* - An individual node in the control class of classes.  And we are really hating the
                stupid use of control words for variable names!!
            
            **Returns:**
                * None
        """        
        if self.topLevelClasses == None:
            self.topLevelClasses = []
        self.topLevelClasses.append(LandCoverClass)
        self[LandCoverClass.classId] = LandCoverClass

class LandCoverClasses(LandCoverBaseClasses, dict):
    """ This class holds all :py:class:`LandCoverClass` objects.

    **Description:**

        This class holds all of the :py:class:`LandCoverClass` objects loaded from the LCC XML file.          

    **Arguments:**

        * Not applicable

    """

    # Private frozenset for all unique values
    _uniqueValues = None
    
    #: Boolean for exclusion of empty classes
    excludeEmptyClasses = None
    
    #: Top level classes which reside in the root of the <classes> node and have no parent
    topLevelClasses = None

    def __init__(self, classesNode=None, excludeEmptyClasses=True):

        self.excludeEmptyClasses = excludeEmptyClasses
        
        if not classesNode is None:
            self._loadClassesNode(classesNode)
        

    def _loadClassesNode(self, classesNode):

        self.topLevelClasses = []

        for childNode in classesNode.childNodes:

            if isinstance(childNode, minidom.Element) and childNode.tagName == constants.XmlElementClass:
                topLevelClass = LandCoverClass(childNode, None, self.excludeEmptyClasses)
                self.topLevelClasses.append(topLevelClass)
                
                # Add topLevelClass and all its descendents to dictionary
                self[topLevelClass.classId] = topLevelClass
                
                for descendentClass in self._getDescendentClasses(topLevelClass):
                    self[descendentClass.classId] = descendentClass
                
                
    def _getDescendentClasses(self, landCoverClass):
        
        descendentClasses = []

        for childClass in landCoverClass.childClasses:
            print("childClass is", childClass.name)
            descendentClasses += self._getDescendentClasses(childClass)
            descendentClasses.append(childClass)       
        
        return descendentClasses

    def getUniqueValueIds(self):
        """  Get a `frozenset`_ containing all unique valueIds defined in all classes.

        **Description:**

            The valueIds defined as excluded in the values section are not included.

        **Arguments:**

            * Not applicable

        **Returns:** 
            
            * `frozenset`_
        
        """
        
        if self._uniqueValues is None:
            
            # Assemble all values found in all classes, repeats are allowed
            tempValues = []
            #for landCoverClass in self.itervalues():
            for landCoverClass in self.values():
                tempValues.extend(landCoverClass.uniqueValueIds)

            # repeats purged on conversion to frozenset
            self._uniqueValues = frozenset(tempValues)
            
        return self._uniqueValues
    
    def addTopLevelClass(self, LandCoverClass):
        print("####################################")
        print("In TopLevelClass in LandCoverClasses")
        print("####################################")
        self.topLevelClasses.append(LandCoverClass)
        self[LandCoverClass.classId] = LandCoverClass
        
class EditorLandCoverClasses(LandCoverBaseClasses, dict):
    """ This class holds all :py:class:`LandCoverClass` objects.

    **Description:**

        This class holds all of the :py:class:`LandCoverClass` objects loaded from the LCC XML file.          

    **Arguments:**

        * Not applicable

    """
    
    def _loadClassesNode(self, classesNode):    
        """ 
            Loads and parse xml into control class 
            
            **Description:**
                This method is invoked when a new control class is created.  It parse an existing xml into appropriate
                control class nodes, so that it can be accessed by model and view.
            
            **Arguments:**
                * *classesNode* - xml element to be parsed 
            
            **Returns:**
                * None
        """        

        self.topLevelClasses = []
                
        for childNode in classesNode.childNodes:

            if isinstance(childNode, minidom.Element) and childNode.tagName == constants.XmlElementClass:
                topLevelClass = EditorLandCoverClass(childNode, None, self.excludeEmptyClasses)
                self.topLevelClasses.append(topLevelClass)
                
                # Add topLevelClass and all its descendents to dictionary
                self[topLevelClass.classId] = topLevelClass
                                
                for descendentClass in self._getDescendentClasses(topLevelClass):
                    self[descendentClass.classId] = descendentClass
        
class LandCoverValue(object): 
    """ This class holds all of the properties associated with an LCC value-`Node`_.

    **Description:**
        
        This class holds all of the information stored in a <value> tag within a LCC XML file.          
        
    **Arguments:**
        
        * *valueNode* - LCC class-`Node`_ loaded from a lcc file

    """

    #: The unique identifier for the value
    valueId = None
    
    #: The name of the value
    name = ''
    
    #: A boolean for whether value is excluded, ie. water
    excluded = None
    
    # coefId as the key and LandCoverCoefficient as the value.
    _coefficients = {}
        
    def __init__(self, valueNode=None):
        
        if not valueNode is None:
            self._loadLccValueNode(valueNode)
        else:
            self.valueId = None
            self.name = ''
            self._coefficients = {}
    
    def _loadLccValueNode(self, valueNode):
        """  This method Loads a LCC value-`Node`_ to assign all properties associated with this class.
        
        **Description:**
            
            If the LCC value-`Node`_ was not provided as an argument when this class was instantiated, you can load 
            one to assign all properties associated with this class.                        
            
            See the class description for additional details
        
        """ 

        self.valueId = int(valueNode.getAttribute(constants.XmlAttributeId))
        self.name = valueNode.getAttribute(constants.XmlAttributeName)
        
        nodata = valueNode.getAttribute(constants.XmlAttributeNodata)

        if nodata.lower() == "true" or nodata == '1':
            self.excluded = True
        else:
            self.excluded = False
        
        # Load coefficients
        self._coefficients = {}
        for coefficientNode in valueNode.getElementsByTagName(constants.XmlElementCoefficient):
            lcCoef = LandCoverCoefficient(coefficientNode)
            self._coefficients[lcCoef.coefId] = lcCoef
    
    def getCoefficientValueById(self, coeffId):
        """  Given the unique identifier for a coefficient, this method returns the corresponding coefficient value. 
        
        **Description:**
        
            A LandCoverValue can have multiple coefficients.  This method allows you to look up the actual coefficient
            value as a floating point number based on the coefficient's unique identifier.  If you need additional 
            details about a coefficient, see the :py:class:`LandCoverCoefficients` property associated with 
            :py:class:`LandCoverClassification`.
        
        **Arguments:**
            
            * *coeffId* - Coefficient unique identifier, ie. IMPERVIOUS, NITROGEN, PHOSPHORUS, etc.
        
        **Returns:**
            
            * float
        
        """
        
        try:
            coeffValue = self._coefficients[coeffId].value
        except:
            coeffValue = None          
        return coeffValue 
    
    def addValues(self, valueId, name, excluded):
        """ 
            Adds a new value node to the value table 
            
            **Description:**
                This method gets the appropriate data from the dialog and then uses the data to create a new node in
                the values table. 
            
            **Arguments:**
                * *valueId* - ONE_LINE_DESCRIPTION_OF_TYPE_AND_PURPOSE 
                * *name* - ONE_LINE_DESCRIPTION_OF_TYPE_AND_PURPOSE
                * *excluded* - ONE_LINE_DESCRIPTION_OF_TYPE_AND_PURPOSE
            
            **Returns:**
                * RETURNED_OBJECT_TYPE
        """
        self.valueId = valueId
        self.name = name
        if excluded:
            self.excluded = True

    def isName(self, checkName):
        """ returns bool if name is a match """
        if self.name.lower() == checkName.lower():
            return True
        return False

class LandCoverValues(dict):
    """ This class holds all :py:class:`LandCoverValue` objects.

    **Description:**
        
        This class holds all of the :py:class:`LandCoverValue` objects loaded from the LCC XML file.          
        
    **Arguments:**
        
        * Not applicable

    """ 
    
    __excludedValueIds = None
    __includedValueIds = None
    
    def __init__(self, valuesNode=None):
        """ Constructor - Object initialization """
        if not valuesNode is None:
            self._loadValuesNode(valuesNode)
                
    def _loadValuesNode(self, valuesNode):
        """ Load values from valuesNode """
        
        valueNodes = valuesNode.getElementsByTagName(constants.XmlElementValue)

        for valueNode in valueNodes:
            valueId = int(valueNode.getAttribute(constants.XmlAttributeId))
            landCoverValue = LandCoverValue(valueNode)
            self[valueId] = landCoverValue
        
    def getExcludedValueIds(self):
        """  Get a `frozenset`_ containing all valueIds to be excluded       
        
        **Description:**
            
            Excluded valueIds are the raster values which a user has assigned to NoData.                       
            
        **Arguments:**
            
            * Not applicable
                        
        **Returns:** 
            
            * `frozenset`_       
        
        """

        
        if self.__excludedValueIds is None:
            
            self._updateValueIds()

        return self.__excludedValueIds


    def getIncludedValueIds(self):
        """  Get a `frozenset`_ containing all valueIds which are not marked excluded.
        
        **Description:**
            
            Included valueIds are the raster values which a user has not assigned to NoData.  
            
        **Arguments:**
            
            * Not applicable
            
        **Returns:** 
            
            * `frozenset`_       
            
        """
        
        if self.__includedValueIds is None:
            
            self._updateValueIds()

        
        return self.__includedValueIds
    
    
    def _updateValueIds(self):
        """ Updates internal frozen sets with included/excluded valueIds 
        
        **Description:**
            
            This is a private method to update the stored frozensets which are returned by separate methods.
            
        **Arguments:**
            
            * Not applicable
            
        **Returns:**
            
            * None
        
        """

        excludedValueIds = []
        includedValueIds = []
        
        # Loop through all LCObjects in this container
        #for valueId, landCoverValueObj in self.iteritems():
        for valueId, landCoverValueObj in self.items():

            #Excluded values
            if landCoverValueObj.excluded:
                excludedValueIds.append(valueId)
            
            #Included values
            else:
                includedValueIds.append(valueId)

        self.__excludedValueIds = frozenset(excludedValueIds)
        self.__includedValueIds = frozenset(includedValueIds)
    
#     def isValueIDInTree(self,valueId):
#         """ method searches dictionary for valueId and returns true if presnt and false if not prest 
#             
#             parameter : valueId to be checked
#             
#             returns ...boolean"""
#         
#         self.has_key(valueId)
#         
        
                
               
class LandCoverCoefficients(dict):
    """ This class holds :py:class:`LandCoverCoefficient` objects.

    **Description:**
        
        This class holds all of the :py:class:`LandCoverCoefficient` objects loaded from the LCC XML file.          
        
    **Arguments:**
        
        * *coefficientsNode* - LCC class-`Node`_ loaded from a lcc file

    """


    # Private frozenset for all unique values
    _uniqueValues = None
    
    def __init__(self, coefficientsNode=None):
    
        if not coefficientsNode is None:
            self._loadLccCoefficientsNode(coefficientsNode)
                    
    def _loadLccCoefficientsNode(self, coefficientsNode):
        """  This method Loads a LCC coefficients-`Node`_ to assign all properties associated with this class.
        
        **Description:**
            
            If the LCC coefficients-`Node`_ was not provided as an argument when this class was instantiated, 
            you can load one to assign all properties associated with this class.                        
            
        **Arguments:**
            
            * *valueNode* - LCC coefficients-`Node`_ loaded from a lcc file            
            
        **Returns:** 
            
            * None       
        
        """ 
        
        # Load coefficients
        for coefficientNode in coefficientsNode.getElementsByTagName(constants.XmlElementCoefficient):
            lcCoef = LandCoverCoefficient(coefficientNode)
            self[lcCoef.coefId] = lcCoef
            
class LandCoverCoefficient(object):
    """ This class holds all of the properties associated with a LCC coefficient-`Node`_.

    **Description:**
        
        This class holds all of the information stored in a <coefficient> tag within XML file.  Some properties are
        not available depending on the context.  The *coefId*, *name* and *fieldName* properties are available from the 
        coefficients section.  The *coefId* and *value* are availiable when associated with a value.          
        
    **Arguments:**
        
        * *coefficientNode* - LCC coefficient-`Node`_ loaded from a lcc file

    """
    
    #: The unique identifier for the coefficient
    coefId = ""
    
    #: The name of the coefficient
    name = ""
    
    #: The name of the field use in output tables
    fieldName = ""
    
    #: The actual coefficient value
    value = ""
    
    #: The Per Unit Area/Percentage Field
    calcMethod = ""
    
    
    def __init__(self, coefficientNode=None):
        
        if not coefficientNode is None:
            self._loadLccCoefficientNode(coefficientNode)
    
    
    def _loadLccCoefficientNode(self, coefficientNode):
        """  This method Loads a LCC coefficient-`Node`_ to assign all properties associated with this class.
        
        **Description:**
            
            If the LCC coefficient-`Node`_ was not provided as an argument when this class was instantiated, you can load 
            one to assign all properties associated with this class.                        
            
            See the class description for additional details
        
        """ 

        self.coefId = str(coefficientNode.getAttribute(constants.XmlAttributeId))
        self.name = str(coefficientNode.getAttribute(constants.XmlAttributeName))
        self.fieldName = str(coefficientNode.getAttribute(constants.XmlAttributeFieldName))
        self.calcMethod = str(coefficientNode.getAttribute(constants.XmlAttributeCalcMethod))
        
        try:
            self.value = float(coefficientNode.getAttribute(constants.XmlAttributeValue))
        except:
            self.value = 0.0

    def populateCoefficient(self, passedCoefId, passedName, passedFieldName, passedCalcMethod):
        self.coefId = str(passedCoefId)
        self.name = str(passedName)
        self.fieldName = str(passedFieldName)
        self.calcMethod = str(passedCalcMethod)
    
    def deepCopyCoefficient(self,originalLccObject):
        
        self.coefId = copy.deepcopy(originalLccObject.coefId)
        self.name = copy.deepcopy(originalLccObject.name)
        self.fieldName = copy.deepcopy(originalLccObject.fieldName)
        self.calcMethod = copy.deepcopy(originalLccObject.calcMethod)
        
    def populateCoefficientValue(self, passedValue):
        self.value = float(passedValue)
     
class LandCoverClassificationBase(object):
    """ This class holds all the details about a Land Cover Classification(LCC).

    **Description:**
        
        This class holds :py:class:`LandCoverClasses`, :py:class:`LandCoverValues` and :py:class:`LandCoverMetadata`
        objects and has helpful methods for extracting information from them.     
        
    **Arguments:**
        
        * *lccFilePath* - File path to LCC XML file (.xml file extension)
        * *excludeEmptyClasses* - ignore a class which does not have a value as a descendant

    """ 
    #: A :py:class:`LandCoverClasses` object holding :py:class:`LandCoverClass` objects
    classes = None
    
    #: A :py:class:`LandCoverValues` object holding :py:class:`LandCoverValue` objects
    values = None
    
    #: A :py:class:`LandCoverMetadata` object
    metadata = None
    
    #: A `dict`_ holding :py:class:`LandCoverCoefficient` objects
    coefficients = None
    
    #: A 'list' holding all the name of the LCP Fields
    overwriteFieldsNames = []
    
    #: A 'list' _ holding all selected overwriteField data
    overwriteFieldDataList = None
    
    __uniqueValueIds = None
    __uniqueValueIdsWithExcludes = None
    
    
    def __init__(self, lccFilePath=None, excludeEmptyClasses=True):
        
        if not lccFilePath is None:
            self._loadFromFilePath(lccFilePath, excludeEmptyClasses)
        else:
            self.classes = LandCoverClasses()
            self.values = LandCoverValues()
            self.metadata = LandCoverMetadata()
            self.coefficients = LandCoverCoefficients()
            self.overwriteFieldDataList = []
            
        self.overwriteFieldsNames = constants.overwriteFieldList
#        map(str, constants.overwriteFieldList)

    def populateClassoverwriteFields(self):
        for targetClass in self.classes.values():
            self.overwriteFieldDataList.extend(targetClass.getClassLcpAttributes())

class LandCoverClassification(LandCoverClassificationBase):
    """ This class holds all the details about a Land Cover Classification(LCC).

    **Description:**
        
        This class holds :py:class:`LandCoverClasses`, :py:class:`LandCoverValues` and :py:class:`LandCoverMetadata`
        objects and has helpful methods for extracting information from them.     
        
    **Arguments:**
        
        * *lccFilePath* - File path to LCC XML file (.xml file extension)
        * *excludeEmptyClasses* - ignore a class which does not have a value as a descendant

    """ 
    #: A :py:class:`LandCoverClasses` object holding :py:class:`LandCoverClass` objects
    classes = None
    
    #: A :py:class:`LandCoverValues` object holding :py:class:`LandCoverValue` objects
    values = None
    
    #: A :py:class:`LandCoverMetadata` object
    metadata = None
    
    #: A `dict`_ holding :py:class:`LandCoverCoefficient` objects
    coefficients = None
    
    __uniqueValueIds = None
    __uniqueValueIdsWithExcludes = None
    
    def __init__(self, lccFilePath=None, excludeEmptyClasses=True):
        
        if not lccFilePath is None:
            self._loadFromFilePath(lccFilePath, excludeEmptyClasses)
        else:
            self.classes = LandCoverClasses()
            self.values = LandCoverValues()
            self.metadata = LandCoverMetadata()
            self.coefficients = LandCoverCoefficients()
            self.overwriteFieldDataList = []
            
        self.overwriteFieldsNames = constants.overwriteFieldList
#        map(str, constants.overwriteFieldList)

    def _loadFromFilePath(self, lccFilePath, excludeEmptyClasses=True):
        """  This method loads a Land Cover Classification (.xml) file.
        
        **Description:**
            
            If the file path to a LCC file was not provided as an argument when this class was instantiated, you can 
            load one to assign all properties associated with this class.                        
            
            See the class description for additional details     
                    
        """
        self.overwriteFieldDataList = []
        
        # Flush cashed objects, dependent of previous file
        self.__uniqueValueIds = None
        self.__uniqueValueIdsWithExcludes = None
        self.lccFilePath = lccFilePath
        
        # Load file into DOM
        lccDocument = minidom.parse(lccFilePath)
        
        # Load Values
        valuesNode = lccDocument.getElementsByTagName(constants.XmlElementValues)[0]
        self.values = LandCoverValues(valuesNode)      
        
        # Load Classes
        classesNode = lccDocument.getElementsByTagName(constants.XmlElementClasses)[0]
        self.classes = LandCoverClasses(classesNode, excludeEmptyClasses) 
        
        # Load Metadata
        metadataNode = lccDocument.getElementsByTagName(constants.XmlElementMetadata)[0]
        self.metadata = LandCoverMetadata(metadataNode)   

        # Load Coefficients
        try:
            coefficientsNode = lccDocument.getElementsByTagName(constants.XmlElementCoefficients)[0]
            self.coefficients = LandCoverCoefficients(coefficientsNode)
        except:
            pass
        
        self.populateClassoverwriteFields()
        
    def getUniqueValueIds(self):
        """  Get a `frozenset`_ containing all unique valueIds in the Land Cover Classification.
         
        **Description:**
             
            The valueIds will be from both the values and classes, which are not defined excluded.  
            Done by original coder not used in current iteration, but might be used for future compatibility with other
            programs, so not taken out.                  
             
        **Arguments:**
             
            * Not applicable
                         
        **Returns:** 
             
            * `frozenset`_       
         
        """
         
        if self.__uniqueValueIds is None:
             
            valueIdsInClasses = self.values.getIncludedValueIds()
            valueIdsInValues = self.classes.getUniqueValueIds()
             
            valueIds = list(valueIdsInClasses) + list(valueIdsInValues)
             
            self.__uniqueValueIds = frozenset(valueIds)
             
        return self.__uniqueValueIds
 
 
    def getUniqueValueIdsWithExcludes(self):
        """  Get a `frozenset`_ of all unique values in the lcc file with excluded values included.
         
        **Description:**
             
            The valueIds will be from both the values and classes and they will include those defined as excluded.             
            Done by original coder not used in current iteration, but might be used for future compatibility with other
            programs, so not taken out.
             
        **Arguments:**
             
            * Not applicable
                         
        **Returns:** 
             
            * `frozenset`_       
         
        """        
 
 
        if self.__uniqueValueIdsWithExcludes is None:
             
            includedValueIds = list(self.getUniqueValueIds())
            excludedValueIds = list(self.values.getExcludedValueIds())
             
            self.__uniqueValueIdsWithExcludes = frozenset(includedValueIds + excludedValueIds)
         
        return self.__uniqueValueIdsWithExcludes
    
class EditorLandCoverClassification(LandCoverClassificationBase):
    """ This class holds all the details about a Land Cover Classification(LCC).

    **Description:**
        
        This class holds :py:class:`LandCoverClasses`, :py:class:`LandCoverValues` and :py:class:`LandCoverMetadata`
        objects and has helpful methods for extracting information from them.     
        
    **Arguments:**
        
        * *lccFilePath* - File path to LCC XML file (.xml file extension)
        * *excludeEmptyClasses* - ignore a class which does not have a value as a descendant

    """     
    def __init__(self, lccFilePath=None, excludeEmptyClasses=True):
        
        if not lccFilePath is None:
            self._loadFromFilePath(lccFilePath, excludeEmptyClasses)
        else:
            self.classes = EditorLandCoverClasses()
            self.values = LandCoverValues()
            self.metadata = LandCoverMetadata()
            self.coefficients = LandCoverCoefficients()
            self.overwriteFieldDataList = []
            
        self.overwriteFieldsNames = constants.overwriteFieldList
#        map(str, constants.overwriteFieldList)

    def _loadFromFilePath(self, lccFilePath, excludeEmptyClasses=True):
        """  This method loads a Land Cover Classification (.xml) file.
        
        **Description:**
            
            If the file path to a LCC file was not provided as an argument when this class was instantiated, you can 
            load one to assign all properties associated with this class.                        
            
            See the class description for additional details     
                    
        """
        self.overwriteFieldDataList = []
        
        # Flush cashed objects, dependent of previous file
        self.__uniqueValueIds = None
        self.__uniqueValueIdsWithExcludes = None
        self.lccFilePath = lccFilePath
        
        # Load file into DOM
        lccDocument = minidom.parse(lccFilePath)
        
        # Load Values
        valuesNode = lccDocument.getElementsByTagName(constants.XmlElementValues)[0]
        self.values = LandCoverValues(valuesNode)      
        
        # Load Classes
        classesNode = lccDocument.getElementsByTagName(constants.XmlElementClasses)[0]
        self.classes = EditorLandCoverClasses(classesNode, excludeEmptyClasses) 
        
        # Load Metadata
        metadataNode = lccDocument.getElementsByTagName(constants.XmlElementMetadata)[0]
        self.metadata = LandCoverMetadata(metadataNode)   

        # Load Coefficients
        try:
            coefficientsNode = lccDocument.getElementsByTagName(constants.XmlElementCoefficients)[0]
            self.coefficients = LandCoverCoefficients(coefficientsNode)
        except:
            pass
        
        self.populateClassoverwriteFields()
    