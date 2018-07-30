#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:     23/10/2017
# Copyright:   (c) Adolfo.Diaz 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

## ===================================================================================
def print_exception():

    tb = sys.exc_info()[2]
    l = traceback.format_tb(tb)
    l.reverse()
    tbinfo = "".join(l)
    AddMsgAndPrint("\n\n----------ERROR Start-------------------",2)
    AddMsgAndPrint("Traceback Info: \n" + tbinfo + "Error Info: \n    " +  str(sys.exc_type)+ ": " + str(sys.exc_value) + "",2)
    AddMsgAndPrint("----------ERROR End-------------------- \n",2)

## ================================================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    # Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line

    try:
        print msg

        #for string in msg.split('\n'):

        # Add a geoprocessing message (in case this is run as a tool)
        if severity == 0:
            arcpy.AddMessage(msg)

        elif severity == 1:
            arcpy.AddWarning(msg)

        elif severity == 2:
            arcpy.AddMessage("    ")
            arcpy.AddError(msg)

    except:
        pass
## ===============================================================================================================
def addAttributeIndex(table,fieldList,verbose=True):
# Attribute indexes can speed up attribute queries on feature classes and tables.
# This function adds an attribute index(es) for the fields passed to the table that
# is passed in. This function takes in 2 parameters:
#   1) Table - full path to an existing table or feature class
#   2) List of fields that exist in table
# This function will make sure an existing index is not associated with that field.
# Does not return anything.

    try:
        # Make sure table exists. - Just in case
        if not arcpy.Exists(table):
            AddMsgAndPrint("\tAttribute index cannot be created for: " + os.path.basename(table) + " TABLE DOES NOT EXIST",2)
            return False

        else:
            AddMsgAndPrint("\tAdding Indexes to Table: " + os.path.basename(table))

        # iterate through every field
        for fieldToIndex in fieldList:

            # Make sure field exists in table - Just in case
            if not len(arcpy.ListFields(table,"*" + fieldToIndex))>0:
                AddMsgAndPrint("\tAttribute index cannot be created for: " + fieldToIndex + ". FIELD DOES NOT EXIST",2)
                continue

            # list of indexes (attribute and spatial) within the table that are
            # associated with the field or a field that has the field name in it.
            # Important to inspect all associated fields b/c they could be using
            # a differently named index
            existingIndexes = arcpy.ListIndexes(table,"*" + fieldToIndex)
            bFieldIndexExists = False

            # check existing indexes to see if fieldToIndex is already associated
            # with an index
            if existingIndexes > 0:

                # iterate through the existing indexes looking for a field match
                for index in existingIndexes:
                    associatedFlds = index.fields

                    # iterate through the fields associated with existing index.
                    # Should only be 1 field since multiple fields are not allowed
                    # in a single FGDB.
                    for fld in associatedFlds:

                        # Field is already part of an existing index - Notify User
                        if fld.name == fieldToIndex:
                            AddMsgAndPrint("\tAttribute Index for " + fieldToIndex + " field already exists",1)
                            bFieldIndexExists = True

                    # Field is already part of an existing index - Proceed to next field
                    if bFieldIndexExists:
                        break

            # Attribute field index does not exist.  Add one.
            if not bFieldIndexExists:

                newIndex = "IDX_" + fieldToIndex

                # UNIQUE setting is not used in FGDBs - comment out
                arcpy.AddIndex_management(table,fieldToIndex,newIndex,"#","ASCENDING")

                if verbose:
                    AddMsgAndPrint("\tSuccessfully added attribute index for " + fieldToIndex)

    except:
        print_exception()
        return False

import arcpy, sys, string, os, time, datetime, re, csv, traceback, shutil
from arcpy import env

if __name__ == '__main__':

    FGDBpath = r'O:\scratch\test_20171023.gdb'
    env.workspace = FGDBpath

    fgdbTables = arcpy.ListTables('*')
    fgdbFCs = [fgdbTables.append(fc) for fc in arcpy.ListFeatureClasses('*')]

    AddMsgAndPrint("\nAdding Attribute Indexes to tables")

    for table in fgdbTables:
        tablePath = os.path.join(FGDBpath,table)
        fieldNames = [f.name for f in arcpy.ListFields(tablePath)]

        if not addAttributeIndex(tablePath,fieldNames): continue
