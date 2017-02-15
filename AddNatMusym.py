# Code copied from SDA_CustomQuery script and modified to get NationalMusym from Soil Data Access
# Steve Peaslee 10-18-2016


## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        print msg

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

## ================================================================================================================
def errorMsg():

    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]
        AddMsgAndPrint(theMsg,2)

    except:
        AddMsgAndPrint("Unhandled error in errorMsg method", 2)
        pass

## ================================================================================================================
def splitThousands(someNumber):
    """ will determine where to put a thousands seperator if one is needed.
        Input is an integer.  Integer with or without thousands seperator is returned."""

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber

## ================================================================================================================
def GetMukeys(theInput):
    # Create a list of unique MUKEY values from spatial layer for use in SDA query

    try:
        AddMsgAndPrint("\nCompiling a list of unique MUKEY values",0)
        arcpy.SetProgressorLabel("Compiling a list of unique MUKEY values")

        # Describe the input data
        theDesc = arcpy.Describe(theInput)
        theDataType = theDesc.dataType

        # Get Featureclass and total count
        if theDataType.lower() == "featurelayer":
            theFC = theDesc.featureClass.catalogPath
            featureCount = int(arcpy.GetCount_management(theFC).getOutput(0))

        elif theDataType.lower() in ["featureclass", "shapefile"]:
            theFC = theInput
            featureCount = int(arcpy.GetCount_management(theInput).getOutput(0))

        else:
            AddMsgAndPrint("\nUnknown data type: " + theDataType.lower(),2)
            sys.exit()

        mukeyField = FindField(theFC,"MUKEY")
        mukeyList = list()

        # Exit if "MUKEY" doesn't exist
        if not mukeyField:
            AddMsgAndPrint("\t\"MUKEY\" field is missing! -- Cannot get MUKEY Values.  EXITING!",2)
            sys.exit()

        if featureCount:

            with arcpy.da.SearchCursor(theInput, [mukeyField]) as cur:
                for rec in cur:
                    if not rec[0] in mukeyList:
                        mukeyList.append(rec[0])

            AddMsgAndPrint("\tThere are " + splitThousands(len(mukeyList)) + " unique MUKEY values", 1)

        else:
            AddMsgAndPrint("\n\tThere are no features in layer.  Empty Geometry. EXITING",2)
            sys.exit()

        if not len(mukeyList):
            AddMsgAndPrint("\n\tThere are no MUKEYS in layer. EXITING",2)
            sys.exit()

        return mukeyList

    except:
        errorMsg()
        AddMsgAndPrint("\nCould not retrieve list of MUKEYs",2)
        sys.exit()

## ================================================================================================================
def FindField(layer,chkField):
    # Check table or featureclass to see if specified field exists
    # If fully qualified name is found, return that name; otherwise return ""
    # Set workspace before calling FindField

    try:

        if arcpy.Exists(layer):

            theDesc = arcpy.Describe(layer)
            theFields = theDesc.fields
            theField = theFields[0]

            for theField in theFields:

                # Parses a fully qualified field name into its components (database, owner name, table name, and field name)
                parseList = arcpy.ParseFieldName(theField.name) # (null), (null), (null), MUKEY

                # choose the last component which would be the field name
                theFieldname = parseList.split(",")[len(parseList.split(','))-1].strip()  # MUKEY

                if theFieldname.upper() == chkField.upper():
                    return theField.name

            return False

        else:
            AddMsgAndPrint("\tInput layer not found", 0)
            return False

    except:
        errorMsg()
        return False

## ===================================================================================
def getNATMUSYM(mukeyList, featureLayer):
    # POST REST which uses urllib and JSON
    # Send query to SDM Tabular Service, returning data in JSON format
    # Sends a list of MUKEYS and returns a pair for each MUKEY [MUKEY,NATMUSYM]
    # Adds NATMUSYM field to inputFeature layer if not present.

    try:

        AddMsgAndPrint("\nRequesting tabular data for " + splitThousands(len(mukeyList)) + " map units...")
        arcpy.SetProgressorLabel("Sending tabular request to Soil Data Access...")

        # convert the list into a comma seperated string
        mukeys = ",".join(mukeyList)

        # 'SELECT m.mukey, m.nationalmusym as natmusym from mapunit m where mukey in (753574,2809844,753571)'
        sQuery = "SELECT m.mukey, m.nationalmusym as natmusym from mapunit m where mukey in (" + mukeys + ")"

        # Tabular service to append to SDA URL
        theURL = "https://sdmdataaccess.nrcs.usda.gov/Tabular/SDMTabularService/post.rest"

        # Create request using JSON, return data as JSON
        dRequest = dict()
        dRequest["FORMAT"] = "JSON+COLUMNNAME+METADATA"
        dRequest["QUERY"] = sQuery
        jData = json.dumps(dRequest)

        # Send request to SDA Tabular service using urllib2 library
        req = urllib2.Request(theURL, jData)
        resp = urllib2.urlopen(req)
        jsonString = resp.read()
        data = json.loads(jsonString)

        """{u'Table': [[u'mukey', u'natmusym'],
                    [u'ColumnOrdinal=0,ColumnSize=4,NumericPrecision=10,NumericScale=255,ProviderType=Int,IsLong=False,ProviderSpecificDataType=System.Data.SqlTypes.SqlInt32,DataTypeName=int',
                     u'ColumnOrdinal=1,ColumnSize=6,NumericPrecision=255,NumericScale=255,ProviderType=VarChar,IsLong=False,ProviderSpecificDataType=System.Data.SqlTypes.SqlString,DataTypeName=varchar'],
                    [u'753571', u'2tjpl'],
                    [u'753574', u'2szdz'],
                    [u'2809844', u'2v3f0']]}"""

        del jData,req,resp,jsonString

        # Nothing was returned from SDaccess
        if not "Table" in data:
            AddMsgAndPrint("\tWarning! NATMUSYM value was not returned for any of the MUKEY values ",2)
            return False

        # convert the data dictionary to a list of lists
        dataList = data["Table"]

        # Remove the first 2 items from dataList: fields and column metadata-columninfo
        """ [[u'753571', u'2tjpl'], [u'753574', u'2szdz'], [u'2809844', u'2v3f0']] """
        columnNames = dataList.pop(0)  # [u'mukey', u'natmusym']
        columnInfo = dataList.pop(0)

        # Warn user about a discrepancy in mukey count
        if len(mukeyList) != len(dataList):
            AddMsgAndPrint("\tWarning! NATMUSYM value was not returned for the following " + splitThousands(len(mukeyList) - len(dataList)) + " MUKEYS", 1)

            # subtract both lists to see which MUKEYS had no NATSYM
            iNoMatches = list(set(mukeyList) - set([f[0] for f in dataList]))
            AddMsgAndPrint("\n\t\t" + str(iNoMatches),2)

        # Add the 'NATMUSYM' field to inputFeature if not present
        if not "natmusym" in [f.name.lower() for f in arcpy.ListFields(featureLayer)]:
            arcpy.AddField_management(featureLayer,str(columnNames[1]).upper(),'TEXT','#','#',23,'National MU Symbol')

        AddMsgAndPrint("\nImporting NATMUSYM Values",0)
        arcpy.SetProgressorLabel("Importing NATMUSYM Values")
        arcpy.SetProgressor("step", "Importing NATMUSYM Values", 0, len(dataList),1)

        # itereate through mukey,natmusym values and update the NATMUSYM field
        # [[u'753571', u'2tjpl'], [u'753574', u'2szdz'], [u'2809844', u'2v3f0']]
        for rec in dataList:
            mukey,natmusym = rec[0],rec[1]

            expression = arcpy.AddFieldDelimiters(featureLayer,columnNames[0]) + " = '" + mukey + "'"
            with arcpy.da.UpdateCursor(featureLayer, columnNames[1], where_clause=expression) as cursor:

                for row in cursor:
                    row[0] = natmusym

                    cursor.updateRow(row)

            arcpy.SetProgressorPosition()

        arcpy.ResetProgressor()

        AddMsgAndPrint("\tSuccessfully populated 'NATMUSYM' values for " + splitThousands(len(dataList)) + " mapunits \n",0)
        return True

    except urllib2.HTTPError:
        errorMsg()
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
## ====================================== Main Body ==================================
# Import modules
import sys, string, os, locale, arcpy, traceback, urllib2, httplib, json, re
from arcpy import env

inputFeature = arcpy.GetParameterAsText(0)
#inputFeature = r'K:\SSURGO_FY17\2017_WSS_downloads_SSURGO_Region10\soil_wi025\spatial\soilmu_a_wi025.shp'

try:

	# Get list of unique mukeys for use in tabular request
    mukeyList = GetMukeys(inputFeature)

    # populate inputFeature with NATMUSYM
    if not getNATMUSYM(mukeyList, inputFeature):
        AddMsgAndPrint("\nFailed to update NATSYM field",2)

except:
    errorMsg()