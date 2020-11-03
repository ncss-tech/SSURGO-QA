# ---------------------------------------------------------------------------
# QA_CommonLines.py
# Created on: May 20, 2013

# Author: Steve.Peaslee
#         GIS Specialist
#         National Soil Survey Center
#         USDA - NRCS
# e-mail: adolfo.diaz@usda.gov
# phone: 608.662.4422 ext. 216

# Author: Adolfo.Diaz
#         GIS Specialist
#         National Soil Survey Center
#         USDA - NRCS
# e-mail: adolfo.diaz@usda.gov
# phone: 608.662.4422 ext. 216
#

# Identifies adjacent polygons with the same, specified attribute
# If common lines are found, they will be copied to a new featureclass and added to the
# ArcMap TOC.
#
# ArcGIS 10.1 compatible

# 06-03-2013. Fixed handling for some coverages, depending upon attribute fields
# 06-04-2013. Added XYTolerance setting to allow snapping of overlapping survey boundaries
#
# 06-18-2013. Changed script to use the featurelayer and to use AREASYMBOL. Quick-and-dirty test!
#
# 08-02-2013. Adolfo is still having problems with performance and a tendancy to fail after 18-20 hours
#             when run against Region 10 geodatabase in 64 bit background.
#             I have seen occasions when the cursor fails because of a lock. I think this is on the scratchGDB version.
#             May try moving scratchGDB to a 'Geodatabase' folder to avoid antivirus.
#
# 08-05-2013. Changed processing mode to use a list of AREASYMBOL values. This uses less resources.

# ==========================================================================================
# Updated  10/27/2020 - Adolfo Diaz
#
# - Updated and Tested for ArcGIS Pro 2.5.2 and python 3.6
# - All describe functions use the arcpy.da.Describe functionality.
# - All intermediate datasets are written to "in_memory" instead of written to a FGDB and
#   and later deleted.  This avoids having to check and delete intermediate data during every
#   execution.
# - All cursors were updated to arcpy.da
# - Added code to remove layers from an .aprx rather than simply deleting them
# - Updated AddMsgAndPrint to remove ArcGIS 10 boolean and gp function
# - Updated errorMsg() Traceback functions slightly changed for Python 3.6.
# - Added parallel processing factor environment
# - swithced from sys.exit() to exit()
# - All gp functions were translated to arcpy
# - Every function including main is in a try/except clause
# - Main code is wrapped in if __name__ == '__main__': even though script will never be
#   used as independent library.
# - Normal messages are no longer Warnings unnecessarily.


# ==============================================================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:

        print(msg)
        #for string in msg.split('\n'):
            #Add a geoprocessing message (in case this is run as a tool)
        if severity == 0:
            arcpy.AddMessage(msg)

        elif severity == 1:
            arcpy.AddWarning(msg)

        elif severity == 2:
            arcpy.AddError("\n" + msg)

    except:
        pass

# ==============================================================================================================================
def errorMsg():
    try:

        exc_type, exc_value, exc_traceback = sys.exc_info()
        theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]

        if theMsg.find("exit") > -1:
            AddMsgAndPrint("\n\n")
            pass
        else:
            AddMsgAndPrint(theMsg,2)

    except:
        AddMsgAndPrint("Unhandled error in unHandledException method", 2)
        pass

## ===================================================================================
def setScratchWorkspace():
    """ This function will set the scratchWorkspace for the interim of the execution
        of this tool.  The scratchWorkspace is used to set the scratchGDB which is
        where all of the temporary files will be written to.  The path of the user-defined
        scratchWorkspace will be compared to existing paths from the user's system
        variables.  If there is any overlap in directories the scratchWorkspace will
        be set to C:\TEMP, assuming C:\ is the system drive.  If all else fails then
        the packageWorkspace Environment will be set as the scratchWorkspace. This
        function returns the scratchGDB environment which is set upon setting the scratchWorkspace"""

##        This is a printout of my system environmmental variables - Windows 10
##        -----------------------------------------------------------------------------------------
##        ESRI_OS_DATADIR_LOCAL_DONOTUSE-- C:\Users\Adolfo.Diaz\AppData\Local\
##        ESRI_OS_DIR_DONOTUSE-- C:\Users\ADOLFO~1.DIA\AppData\Local\Temp\ArcGISProTemp22096\
##        ESRI_OS_DATADIR_ROAMING_DONOTUSE-- C:\Users\Adolfo.Diaz\AppData\Roaming\
##        TEMP-- C:\Users\ADOLFO~1.DIA\AppData\Local\Temp\ArcGISProTemp22096\
##        LOCALAPPDATA-- C:\Users\Adolfo.Diaz\AppData\Local
##        PROGRAMW6432-- C:\Program Files
##        COMMONPROGRAMFILES-- C:\Program Files\Common Files
##        APPDATA-- C:\Users\Adolfo.Diaz\AppData\Roaming
##        USERPROFILE-- C:\Users\Adolfo.Diaz
##        PUBLIC-- C:\Users\Public
##        SYSTEMROOT-- C:\windows
##        PROGRAMFILES-- C:\Program Files
##        COMMONPROGRAMFILES(X86)-- C:\Program Files (x86)\Common Files
##        ALLUSERSPROFILE-- C:\ProgramData
##        HOMEPATH-- \
##        HOMESHARE-- \\usda.net\NRCS\home\WIMA2\NRCS\Adolfo.Diaz
##        ONEDRIVE-- C:\Users\Adolfo.Diaz\OneDrive - USDA
##        ARCHOME-- c:\program files\arcgis\pro\
##        ARCHOME_USER-- c:\program files\arcgis\pro\
##        ------------------------------------------------------------------------------------------

    try:

        def setTempFolderAsWorkspace(sysDriveLetter):
            tempFolder = sysDrive + os.sep + "TEMP"

            if not os.path.exists(tempFolder):
                os.makedirs(tempFolder,mode=777)

            arcpy.env.scratchWorkspace = tempFolder
            AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)
            return arcpy.env.scratchGDB


        AddMsgAndPrint("\nSetting Scratch Workspace")
        scratchWK = arcpy.env.scratchWorkspace

        # -----------------------------------------------
        # Scratch Workspace is defined by user or default is set
        if scratchWK is not None:

            # dictionary of system environmental variables
            envVariables = os.environ

            # get the root system drive i.e C:
            if 'SYSTEMDRIVE' in envVariables:
                sysDrive = envVariables['SYSTEMDRIVE']
            else:
                sysDrive = None

            varsToSearch = ['HOMEDRIVE','HOMEPATH','HOMESHARE','ONEDRIVE','ARCHOME','ARCHOME_USER',
                            'ESRI_OS_DATADIR_LOCAL_DONOTUSE','ESRI_OS_DIR_DONOTUSE','ESRI_OS_DATADIR_MYDOCUMENTS_DONOTUSE',
                            'ESRI_OS_DATADIR_ROAMING_DONOTUSE','TEMP','LOCALAPPDATA','PROGRAMW6432','COMMONPROGRAMFILES','APPDATA',
                            'USERPROFILE','PUBLIC','SYSTEMROOT','PROGRAMFILES','COMMONPROGRAMFILES(X86)','ALLUSERSPROFILE']

            bSetTempWorkSpace = False

            """ Iterate through each Environmental variable; If the variable is within the 'varsToSearch' list
                above then check their value against the user-set scratch workspace.  If they have anything
                in common then switch the workspace to something local  """
            for var in envVariables:

                if not var in varsToSearch:
                    continue

                # make a list from the scratch and environmental paths
                varValueList = (envVariables[var].lower()).split(os.sep)          # ['C:', 'Users', 'adolfo.diaz', 'AppData', 'Local']
                scratchWSList = (scratchWK.lower()).split(os.sep)                 # [u'C:', u'Users', u'adolfo.diaz', u'Documents', u'ArcGIS', u'Default.gdb', u'']

                # remove any blanks items from lists
                varValueList = [val for val in varValueList if not val == '']
                scratchWSList = [val for val in scratchWSList if not val == '']

                # Make sure env variables were populated
                if len(varValueList)>0 and len(scratchWSList)>0:

                    # Home drive is being used as scrathcworkspace
                    if scratchWSList[0].lower() == envVariables['HOMEDRIVE'].lower():
                        bSetTempWorkSpace = True

                    # First element is the drive letter; remove it if they are they same.
                    if varValueList[0] == scratchWSList[0]:
                        varValueList.remove(varValueList[0])
                        scratchWSList.remove(scratchWSList[0])
                    else:
                        continue

                # Compare the values of 2 lists; order is significant
                common = [i for i, j in zip(varValueList, scratchWSList) if i == j]

                # There is commonality between the scrathWS and some env variable
                # Proceed with creating a temp path.
                if len(common) > 0:
                    bSetTempWorkSpace = True
                    break

            # The current scratch workspace shares 1 or more directory paths with the
            # system env variables.  Create a temp folder at root
            if bSetTempWorkSpace:
                AddMsgAndPrint("\tCurrent Workspace: " + scratchWK)

                if sysDrive:
                    return setTempFolderAsWorkspace(sysDrive)

                # This should never be the case.  Every computer should have a system drive (C:\)
                # packageWorkspace is set to "IN_MEMORY"
                else:
                    packageWS = [f for f in arcpy.ListEnvironments() if f=='packageWorkspace']
                    if arcpy.env[packageWS[0]]:
                        arcpy.env.scratchWorkspace = arcpy.env[packageWS[0]]
                        AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)
                    else:
                        AddMsgAndPrint("\tCould not set any scratch workspace",2)
                        return False

            # user-set workspace does not violate system paths; Check for read/write
            # permissions; if write permissions are denied then set workspace to TEMP folder
            else:
                arcpy.env.scratchWorkspace = scratchWK
                arcpy.env.scratchGDB

                if arcpy.env.scratchGDB == None:
                    AddMsgAndPrint("\tCurrent scratch workspace: " + scratchWK + " is READ only!")

                    if sysDrive:
                        return setTempFolderAsWorkspace(sysDrive)

                    else:
                        packageWS = [f for f in arcpy.ListEnvironments() if f=='packageWorkspace']
                        if arcpy.env[packageWS[0]]:
                            arcpy.env.scratchWorkspace = arcpy.env[packageWS[0]]
                            AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)
                            return arcpy.env.scratchGDB

                        else:
                            AddMsgAndPrint("\tCould not set any scratch workspace",2)
                            return False

                else:
                    AddMsgAndPrint("\tUser-defined scratch workspace is set to: "  + arcpy.env.scratchGDB)
                    return arcpy.env.scratchGDB

        # No workspace set (Very odd that it would go in here unless running directly from python)
        else:
            AddMsgAndPrint("\tNo user-defined scratch workspace ")
            sysDrive = os.environ['SYSTEMDRIVE']

            if sysDrive:
                return setTempFolderAsWorkspace(sysDrive)

            else:
                packageWS = [f for f in arcpy.ListEnvironments() if f=='packageWorkspace']
                if arcpy.env[packageWS[0]]:
                    arcpy.env.scratchWorkspace = arcpy.env[packageWS[0]]
                    AddMsgAndPrint("\tTemporarily setting scratch workspace to: " + arcpy.env.scratchGDB,1)
                    return arcpy.env.scratchGDB

                else:
                    AddMsgAndPrint("\tCould not set scratchWorkspace. Not even to default!",2)
                    return False

    except:
        errorMsg()

# ===================================================================================
def splitThousands(someNumber):
    """will determine where to put a thousands seperator if one is needed. Input is
       an integer.  Integer with or without thousands seperator is returned."""

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber

## ===================================================================================

# Import system modules
import sys, os, traceback, locale, time, re, arcpy


if __name__ == '__main__':

    try:
        # Script arguments...
        inLayer = arcpy.GetParameter(0)                # required input soils layer, need to make sure it has MUKEY field
        inField1 = arcpy.GetParameterAsText(1)         # primary attribute field whose values will be compared
        inField2 = arcpy.GetParameterAsText(2)         # optional secondary attribute field whose values will be compared
        asList = arcpy.GetParameter(3)                 # list of AREASYMBOL values to be processed
        #layerName = arcpy.GetParameterAsText(4)       # output featurelayer containing common soil lines (not required)

        # Check out ArcInfo license for PolygonToLine
        arcpy.SetProduct("ArcInfo")
        arcpy.env.parallelProcessingFactor = "75%"
        arcpy.env.overwriteOutput = True
        arcpy.env.XYTolerance = 0
        arcpy.env.addOutputsToMap = False

        # Need to remove any joins before converting the polygons to polylines
        try:
            arcpy.RemoveJoin_management(inLayer)
        except:
            pass

        # Then get the unqualified field name
        inField1 = arcpy.ParseFieldName(inField1).split(",")[3].strip()

        if inField2 != "":
            inField2 = arcpy.ParseFieldName(inField2).split(",")[3].strip()

        # Start by getting information about the input layer
        descInput = arcpy.da.Describe(inLayer)
        inputDT = descInput['dataType'].upper()

        if inputDT == "FEATURELAYER":
            inputName = descInput['name']
            inputFC = descInput['catalogPath']

        elif inputDT in ("FEATURECLASS", "SHAPEFILE"):
            inputName = descInput['name']
            inputFC = descInput['catalogPath']

        else:
            AddMsgAndPrint("Invalid input data type (" + inputDT + ")",2)
            exit()

        # Get workspace information
        theWorkspace = os.path.dirname(inputFC)
        descW = arcpy.da.Describe(theWorkspace)
        wkDT = descW['dataType']

        if wkDT == "FEATUREDATASET":
            theWorkspace = os.path.dirname(theWorkspace)

        # Setting workspace to that of the input soils layer
        arcpy.env.workspace = theWorkspace
        arcpy.env.overwriteOutput = True

##        # Set scratchworkspace and then proceed with processing
##        if setScratchWorkspace():

        # get the first input field object
        chkFields = arcpy.ListFields(inputFC)

        for fld in chkFields:
            fldLength = 0

            if fld.name.upper() == inField1.upper():
                fld1Name = fld.name
                fldLength = fld.length

        # get the optional second input field object
        if inField2 != "":
            for fld in chkFields:

                if fld.name.upper() == inField2.upper():
                    fld2Name = fld.name
                    fldLength += fld.length
        else:
            fld2Name = ""

        if len(asList) == 0:
            asList = ["*"]
            AddMsgAndPrint("\nProcessing all survey areas contained in the input layer...")

        else:
            AddMsgAndPrint("\nProcessing " + splitThousands(len(asList)) + " survey areas...")

        # Total number of unique areasymbols being processed
        numOfareasymbols = len(asList)

        # set name and location for permanent QA featureclass
        comFC2 = os.path.join(theWorkspace, "QA_CommonLines")   # permanent output featureclass containing common-lines

        # set final output to shapefile if input is shapefile and make
        # the new field name compatible with the database type
        if inputFC.endswith(".shp"):
            comFC2 = comFC2 + ".shp"
            fld1Name = fld1Name[0:10]

        if arcpy.Exists(comFC2):
            try:
                arcpy.Delete_management(comFC2)
            except:
                errorMsg()
                AddMsgAndPrint("Unable to overwrite existing featureclass '" + comFC2,2)

        # set output map layer name
        #comFL = "QA Common Lines  (" + fld1Name.title() + ")"                                  # common-line featurelayer added to ArcMap

        # Counter for total number of common-line problems
        totalCommonLines = 0

        # Initialize counters and lists
        iCnt = 0
        missList = list()     # List of missing areasymbols
        listOfasCLs = list()  # List of areasymbols with common lines
        arcpy.SetProgressor("step", "Finding Common Lines", 0, numOfareasymbols)

        # Iterate through the list of soil survey areas by AREASYMBOL
        for AS in asList:
            iCnt += 1
            asCommonLines = 0

            # Use a temporary featureclass to make selections against
            selLayer = "SelectLayer"

            # set name and location for temporary output features
            comFC = os.path.join("IN_MEMORY", "xxComLines")      # temporary featureclass containing all lines

            # Read soils layer to get polygon OID and associated attribute value,
            # load this information into 'dAtt' dictionary. This will be used to
            # populate the left and right attributes of the new polyline featureclass.

            dAtt = dict()
            theFields = ["OID@",fld1Name]

            if AS == "*":
                # Processing entire layer instead of by AREASYMBOL
                fldQuery = ""
                AS = descInput['baseName']
                arcpy.SetProgressorLabel("Processing Common Lines for " + AS)

            else:
                # Processing just this AREASYMBOL
                fldQuery = arcpy.AddFieldDelimiters(comFC, fld2Name) + " = '" + AS + "'"
                arcpy.SetProgressorLabel(AS + ": " + str(iCnt) + " of " + str(numOfareasymbols))

            # Isolate the features that pertain to a specific areasymbol
            arcpy.MakeFeatureLayer_management(inputFC, selLayer, fldQuery)
            numOfASfeatures = int(arcpy.GetCount_management(selLayer).getOutput(0))

            # process this survey
            if numOfASfeatures > 0:

                # format lead spacing for console message
                spacing = " " * (4 -  len(str(iCnt)))
                AddMsgAndPrint("\n" + spacing + str(iCnt) + ". " + fld2Name + " " + AS + ": processing " + splitThousands(numOfASfeatures) + " features")
                arcpy.SetProgressorLabel(AS + ": " + str(iCnt) + " of " + str(numOfareasymbols) + " - processing " + splitThousands(numOfASfeatures) + " features")

                # Populating dAtt dictionary from a featurelayer causes problems because it may not include the
                # neccesary information for the adjacent polygon. This may slow things down a bit, but
                # it will prevent errors. WAIT! This shouldn't matter if we are only checking within the
                # survey area.

                # Save primary values for each polygon in the entire featureclass
                with arcpy.da.SearchCursor(selLayer, ["OID@",fld1Name]) as cursor:
                    for row in cursor:
                        dAtt[row[0]] = row[1]

                # Convert the selected mapunit polygon features to a temporary polyline featurelayer
                AddMsgAndPrint("\t\tConverting polygon input to a polyline featureclass...")
                arcpy.SetProgressorLabel(AS + ": " + str(iCnt) + " of " + str(numOfareasymbols) + " - Converting polygon input to a polyline featureclass")

                arcpy.PolygonToLine_management(selLayer, comFC, "IDENTIFY_NEIGHBORS")

                # Assign field names for left polygon id and right polygon id
                lPID = "LEFT_FID"
                rPID = "RIGHT_FID"
                theQuery = "(" + arcpy.AddFieldDelimiters(comFC, "LEFT_FID") + " > -1 AND " + arcpy.AddFieldDelimiters(comFC, "RIGHT_FID") + " > -1 )" # include these records for copying to final
                AddMsgAndPrint("\t\tIdentifying adjacent polygon boundaries with the same '" +  fld1Name + "' value...")
                arcpy.SetProgressorLabel(AS + ": " + str(iCnt) + " of " + str(numOfareasymbols) + " - Identifying adjacent polygon boundaries with the same '" +  fld1Name + "' value")

                # Add left and right fields for common line test attribute
                if inputFC.endswith(".shp"):
                    # Need to limit fieldname to 10 characters because of DBF restrictions
                    lFld = "L_" + fld1Name[0:8]
                    rFld = "R_" + fld1Name[0:8]
                else:
                    lFld = "L_" + fld1Name
                    rFld = "R_" + fld1Name

                # modified addfield items to allow for width of Areasymbol values
                arcpy.AddField_management(comFC, lFld, "TEXT", "", "", fldLength, lFld, "NULLABLE")
                arcpy.AddField_management(comFC, rFld, "TEXT", "", "", fldLength, rFld, "NULLABLE")

                # Open common line featureclass and use cursor to add original polygon attributes from dictionary
                theFields = [lPID,rPID,lFld,rFld]

                with arcpy.da.UpdateCursor(comFC, theFields, theQuery) as cursor:
                    for row in cursor:
                        row[2] = dAtt[row[0]]
                        row[3] = dAtt[row[1]]
                        cursor.updateRow(row)

                # Identify outer boundary and lines that are common lines and copy them to
                # the final featureclass.
                # This query will select commonlines only internal to the survey area
                # Using the xxComLines featureclass, this query will select commonlines plus
                # overlapping boundaries between adjacent surveys
                # '("LEFT_FID" > -1 AND "RIGHT_FID" > -1 ) AND "L_MUSYM" = "R_MUSYM"'
                sQuery = theQuery + " AND " + arcpy.AddFieldDelimiters(comFC, lFld) + " = " + arcpy.AddFieldDelimiters(comFC, rFld)

                tmpFL = "Temp Featurelayer"
                arcpy.MakeFeatureLayer_management(comFC, tmpFL, sQuery)

                # Count # of common lines in this areasymbol
                asCommonLines = int(arcpy.GetCount_management(tmpFL).getOutput(0))

                if asCommonLines > 0:
                    # Found at least one common-line problem.
                    # Report finding, create CommonLine featureclass and display in ArcMap
                    totalCommonLines += asCommonLines
                    listOfasCLs.append(AS)
                    AddMsgAndPrint("\t\tFound " + str(asCommonLines) + " common line problems for " + inputName + " " + inputDT.lower(), 1)

                    if arcpy.Exists(comFC2):
                        # output featureclass already exists with common lines from another survey area
                        arcpy.Append_management(tmpFL, comFC2)

                    else:
                        # first set of common lines identified, use them to create a new featureclass
                        arcpy.CopyFeatures_management(tmpFL, comFC2)

                    if arcpy.Exists(tmpFL):
                        arcpy.Delete_management(tmpFL)

                arcpy.Delete_management(comFC)

            else:
                # Skip this survey, no match for AREASYMBOL
                missList.append(AS)
                AddMsgAndPrint("\n" + sp + str(iCnt) + ". " + fld2Name + " " + AS + ": no features found for this survey")

            arcpy.SetProgressorPosition()

        # End of iteration through AREASYMBOL list
        AddMsgAndPrint("\nCommon Lines check complete \n ")

        if len(missList) > 0:
            AddMsgAndPrint("The following surveys were not found in the input layer: " + ", ".join(missList),1)

        if len(listOfasCLs) > 0:
            AddMsgAndPrint("The following survey(s) had common-line errors: " + ", ".join(listOfasCLs), 1)
            AddMsgAndPrint("Output Common Line File: " + comFC2,1)

        # Add common lines to ArcGIS Pro if any exist
        if totalCommonLines > 0 and arcpy.Exists(comFC2):
            try:
                # Add new field to track 'fixes'
                arcpy.AddField_management(comFC2, "Status", "TEXT", "", "", 10, "Status")
                arcpy.env.addOutputsToMap = True
                #arcpy.SetParameter(3, comFL)

                aprx = arcpy.mp.ArcGISProject("CURRENT")
                baseName = descInput['baseName']     # base name of the inLayer

                # Go through each map and see where the inLayer came
                # from and add the common lines layer to that map
                # remove common_lines layer if it exists
                for maps in aprx.listMaps():
                    for lyr in maps.listLayers():

                        if lyr.name == baseName:

                            # Remove 'QA_CommonLines from TOC
                            layerList = [lyr.name for lyr in maps.listLayers()]
                            clBaseName = arcpy.da.Describe(comFC2)['baseName']
                            if clBaseName in layerList:
                                AddMsgAndPrint("Removing " + clBaseName + " from " + maps.name + " Map TOC")
                                maps.removeLayer(maps.listLayers()[layerList.index(clBaseName)])

                              # Could not figure out how to add symbolized data to Pro
##                                symbologyLyrx = os.path.dirname(sys.argv[0]) + os.sep + 'RedLine.lyrx'
##                                newSymLayer = arcpy.mp.LayerFile(symbologyLyrx)
##
##                                outLyr = maps.addDataFromPath(comFC2)
##                                clLayer = maps.listLayers()[0]
##                                newClLayer = arcpy.mp.LayerFile(clLayer)
##                                AddMsgAndPrint(clLayer.name)
##
##                                #arcpy.ApplySymbologyFromLayer_management(comFC2,symbologyLyrx)
##                                arcpy.ApplySymbologyFromLayer_management(newClLayer,newSymLayer)
##                                break

                arcpy.SetParameterAsText(4, comFC2)

            except:
                pass

        else:
            AddMsgAndPrint("No commonlines detected \n ")

##        else:
##            AddMsgAndPrint("\nFailed to set scratchworkspace \n", 2)

    except:
        errorMsg()


