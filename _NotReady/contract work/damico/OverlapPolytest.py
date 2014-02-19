import arcpy, sys
from arcpy import env
##inputLayer = sys.argv[1]
inputLayer = r"C:\Projects\M_Mehaffey\Attila2\originals\TestData\Overlaps.gdb\overlaps\FullOverlap"
arcpy.env.overwriteOutput = True
##inputLayer = r"C:\Projects\M_Mehaffey\Attila2\originals\TestData\Overlaps.gdb\overlaps\AL_IsoWetl100mBuffer_subset"
overlaplist = []
nonoverlapGroupDict = {}

def main(inputLayer):
    #check for overlaps
    result, OID, overlapDict = findOverlaps(inputLayer)
    overlapList = result
    if result:
        arcpy.AddWarning("Warning your layer includes overlapping polygons! Calculating split")
        #Find groups of polygons that don't overlap
        nonoverlapGroupDict = findNonOverlapGroups(overlapDict)

        #If overlaps exists creat new layers with no overlaps(creates new intermediate layer)
        createNoOverlapLayers(overlapList, nonoverlapGroupDict, OID)
    else:
        arcpy.AddMessage("No Overlaps Found")
    
def createNoOverlapLayers(overlapList, nonoverlapGroupDict, OID):
    strlist = []
    flist = []
    #Create a feature layer of the polygons with no overlaps
    for o in overlapList:
        strlist.append(str(o))
        
    values = ",".join(strlist)
    
    arcpy.MakeFeatureLayer_management(inputLayer, "No Polygons Overlap",OID + " NOT IN (" + values + ")")
    flist.append("No Polygons Overlap")

    #Create a feature layer of polygons of each group of non overlapping polygons
    for k in nonoverlapGroupDict.keys():
        olist = []
        for o in nonoverlapGroupDict[k]:
            olist.append(str(o))
        values = ",".join(olist)
        arcpy.MakeFeatureLayer_management(inputLayer, "NoOverlap" + str(k), OID + " IN (" + values + ")")
        flist.append("NoOverlap" + str(k))
    print flist
    
    #For each layer in flist add them to ArcMap
    # Add the feature layer to ArcMap - keep in mind this is just a temporary layer.  It is actually a subset of the input layer
    arcpy.AddMessage("Adding non overlapping polygon layer(s) to view")
    for f in flist:
        mxd = arcpy.mapping.MapDocument("Current")
        df = arcpy.mapping.ListDataFrames(mxd, "Layers") [0]
        addlayer = arcpy.mapping.Layer(f)
        arcpy.mapping.AddLayer(df, addlayer, "BOTTOM")
 
def findNonOverlapGroups(overlapDict):
    group = 1
    nonoverlapGroupDict = {}
    while len(overlapDict) <> 0:
        alist = []
        #get the first OID in the overlap Dictionary
        k = overlapDict.keys()[0]
        # loop through the dictionary to check which polygons the first oid overlaps
        for z in overlapDict.keys():
            #if OID is not in the overlapDict value for a key then add that key to a list - this means these oids don't overlap the first OID
            if k not in overlapDict[z]:
                alist.append(z)
        #for each of the OID in alist         
        for a in alist:
            #Loop through the overlapDict
            for k in overlapDict.keys():
                #if the OID is in alist
                if k in alist:
                    #then loop through alist
                    for a in alist:
                        #Check to see if any of the OIDs overlap any of the others in the list
                        #if it does then remove it from alist
                        if a in overlapDict[k]:
                            alist.remove(a)


        #Create a new dictionary that groups non overlapping polygons
        nonoverlapGroupDict[group] = alist
        #For each of the OIDs in alist remove them from the overlap Dictionary
        for a in alist:
            del overlapDict[a]
        group = group + 1
    print nonoverlapGroupDict
    arcpy.AddMessage(nonoverlapGroupDict)
    arcpy.AddMessage("To create non overlapping polygons, " + str(group) + " new data layers will be created")
    return nonoverlapGroupDict

def findOverlaps(polyFc):
    """ Get the OID values for polygon features that have areas of overlap with other polygons in the same theme.

        **Description:**
        
        Identify polygons that have overlapping areas with other polygons in the same theme and generate a set of their 
        OID field value. Nested polygons (i.e., polygons contained within the boundaries of another polygon) are also
        selected with this routine. 
        
        
        **Arguments:**
        
        * *polyFc* - Polygon Feature Class
        
        
        **Returns:** 
        
        * set - A set of OID field values

        
    """ 
    
    overlapSet = set()
    overlapDict = {}
    
    oidField = arcpy.ListFields(polyFc, '', 'OID')[0]
    
    for row in arcpy.SearchCursor(polyFc, '', '', 'Shape; %s' % oidField.name):
        idlist = []
        for row2 in arcpy.SearchCursor(polyFc, '', '', 'Shape; %s' % oidField.name):
            # check to see if the polygon overlaps the second shape, or if the second shape is nested within
            if row2.Shape.overlaps(row.Shape) or row2.Shape.contains(row.Shape) and not row2.Shape.equals(row.Shape):
                overlapSet.add(row.getValue(oidField.name))
                overlapSet.add(row2.getValue(oidField.name))
                if row.getValue(oidField.name) not in overlapDict.keys():
                    idlist.append(row2.getValue(oidField.name))
                    overlapDict[row.getValue(oidField.name)] = idlist
                elif row.getValue(oidField.name) in overlapDict.keys():
                    idlist = overlapDict[row.getValue(oidField.name)]
                    idlist.append(row2.getValue(oidField.name))
                
##    print overlapDict

    return overlapSet, oidField.name, overlapDict

if __name__ == "__main__":
    main(inputLayer)