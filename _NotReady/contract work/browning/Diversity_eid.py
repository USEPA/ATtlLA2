#-------------------------------------------------------------------------------
# Name:        Diversity.py
# Purpose:      Script that calculates the Diversity metrics in Attila2
#
# Author:      Doug Browning
#
# Created:      09/05/2012
# Last Update:  09/12/2012
#
#-------------------------------------------------------------------------------

try:

    import arcpy, math
    from pylet.arcpyutil import environment
    from arcpy.sa import *

    # HUC file to use
    inHUC = "C:/Documents and Settings/aeerdheim/My Documents/ATtILA2/diversityscript/testdata/wtrshdDefinedProjection.shp"

    # Land Class Grid raster file to use
    inLandClass = "C:/Documents and Settings/aeerdheim/My Documents/ATtILA2/diversityscript/testdata/lc_mrlc"

    # Output file name
    outFile = "C:/Documents and Settings/aeerdheim/My Documents/ATtILA2/diversityscript/testdata/output/out.shp"

    # Temp file name - holds tabulate areas output
    tmpFile = environment.getWorkspaceForIntermediates() +"/temp.dbf"

    # Copy HUC file for starting base of output file
    arcpy.Copy_management(inHUC, outFile)
    arcpy.CreateTable_management("C:/Projects/M_Mehaffey/Attila2/testing/outputTable",inHUC,"testws2","#")

    # Add fields to output file - LC_Overlap, S, H, H_Prime, C
    fldlist = ["LCD_Overlap","S","H","H_Prime","C"]
    for fld in fldlist:
        arcpy.AddField_management(outFile, fld, "DOUBLE")

    # Set environment output coordinates var to HUC file so we know we get sq meters
    # This would be used for LC_Overlap but this was skipped in this script

    # Create table of areas
    arcpy.CheckOutExtension("Spatial")
    TabulateArea(inHUC, "FID", inLandClass, "VALUE", tmpFile)

    totalArea = 0

    # Update cursor in out file
    outrows = arcpy.UpdateCursor(outFile)
    outrow = outrows.next()

    # Search Cursor in file from tabulate areas
    rows = arcpy.SearchCursor(tmpFile)
    fields = arcpy.ListFields(tmpFile,"","All")

    for row in rows:
        # Calculate total area of all land classes for use in proportion
        totalArea = 0
        for field in fields:
            lcArea = row.getValue(field.name)
            if "VALUE_" in field.name and lcArea > 0:
                totalArea = totalArea + lcArea

        # Delete field cursor
        if field:
            del field
        if fields:
            del fields

        # Calculate proportions sum
        pSum = 0
        S = 0
        C = 0
        fields = arcpy.ListFields(tmpFile,"","All")
        for field in fields:
            lcArea = row.getValue(field.name)
            if "VALUE_" in field.name and lcArea > 0:
                P = lcArea / totalArea
                pSum = pSum + (P * math.log(P))
                C = C + P * P
                S = S + 1

        # Write H to outfile
        H = -1 * pSum
        outrow.setValue("H",H)

        # Write H' to outfile
        Hprime = H / math.log(S)
        outrow.setValue("H_Prime",Hprime)

        # Write S to outfile
        outrow.setValue("S",S)

        # Write C to outfile
        outrow.setValue("C",C)

        # Write LC_Overlap to outfile

        # Write Values to out file
        outrows.updateRow(outrow)

        # Go to next row in out file
        outrow = outrows.next()

    # Clean up cursors
    if row:
        del row
    if rows:
        del rows
    if field:
        del field
    if fields:
        del fields
    if outrow:
        del outrow
    if outrows:
        del outrows

    print "All Done - Went well"

except:
    print "All Done - Went bad"
    print arcpy.GetMessages(2)

