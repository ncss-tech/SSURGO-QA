# Code copied from SDA_CustomQuery script and modified to get NationalMusym from Soil Data Access
# Steve Peaslee 10-18-2016


## ===================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    #
    #Split the message on \n first, so that if it's multiple lines, a GPMessage will be added for each line
    try:
        #print msg

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
    # Create list of MUKEY values from spatial layer for use in SDA query

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
            raise MyError, "Unknown data type: " + theDataType.lower()

        mukeyField = FindField(theFC,"MUKEY")
        mukeyList = list()

        if not mukeyField:
            AddMsgAndPrint("\t\"MUKEY\" field is missing! -- Cannot get MUKEY Values.  EXITING!",2)
            sys.exit(0)

        if featureCount > 0:

            with arcpy.da.SearchCursor(theInput, [mukeyField], sql_clause=(None, "ORDER BY MUKEY")) as cur:
                for rec in cur:
                    if not rec[0] in mukeyList:
                        mukeyList.append(rec[0])

            AddMsgAndPrint("\tThere are " + splitThousands(len(mukeyList)) + "unique MUKEY values", 1)
            return mukeyList

        else:
            AddMsgAndPrint("\n\tThere are no features in layer.  Empty Geometry. EXITING",2)
            sys.exit()

        if not len(mukeyList):
            AddMsgAndPrint("\n\tThere are no MUKEYS in layer. EXITING",2)

        return mukeyList

    except:
        errorMsg()
        AddMsgAndPrint("\nCould not retrieve list of MUKEYs",2)
        sys.exit()

## ================================================================================================================
def AddNewFields(outputShp, columnNames, columnInfo):
    # Add new fields from SDA data to the output featureclass
    #
    # ColumnNames and columnInfo come from the Attribute query JSON string
    # MUKEY would normally be included in the list, but it should already exist in the output featureclass
    #
    try:
        # Dictionary: SQL Server to FGDB
        dType = dict()

        dType["int"] = "long"
        dType["smallint"] = "short"
        dType["bit"] = "short"
        dType["varbinary"] = "blob"
        dType["nvarchar"] = "text"
        dType["varchar"] = "text"
        dType["char"] = "text"
        dType["datetime"] = "date"
        dType["datetime2"] = "date"
        dType["smalldatetime"] = "date"
        dType["decimal"] = "double"
        dType["numeric"] = "double"
        dType["float"] ="double"

        # numeric type conversion depends upon the precision and scale
        dType["numeric"] = "float"  # 4 bytes
        dType["real"] = "double" # 8 bytes

        # Iterate through list of field names and add them to the output table
        i = 0

        # ColumnInfo contains:
        # ColumnOrdinal, ColumnSize, NumericPrecision, NumericScale, ProviderType, IsLong, ProviderSpecificDataType, DataTypeName
        #PrintMsg(" \nFieldName, Length, Precision, Scale, Type", 1)

        joinFields = list()
        outputTbl = os.path.join("IN_MEMORY", "QueryResults")
        #outputTbl = os.path.join(env.scratchGDB, "QueryResults")
        arcpy.CreateTable_management(os.path.dirname(outputTbl), os.path.basename(outputTbl))


        for i, fldName in enumerate(columnNames):
            vals = columnInfo[i].split(",")
            length = int(vals[1].split("=")[1])
            precision = int(vals[2].split("=")[1])
            scale = int(vals[3].split("=")[1])
            dataType = dType[vals[4].lower().split("=")[1]]

            if not fldName.lower() == "mukey":
                joinFields.append(fldName)

            arcpy.AddField_management(outputTbl, fldName, dataType, precision, scale, length)
            PrintMsg("\tAdding field " + fldName + " to in-memory table")

        if arcpy.Exists(outputTbl):
            arcpy.JoinField_management(outputShp, "mukey", outputTbl, "mukey", joinFields)
            return columnNames

        else:
            return []

    except:
        errorMsg()
        return []

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
def AttributeRequest(theURL, mukeyList, outputShp, sQuery):
    # POST REST which uses urllib and JSON
    #
    # Send query to SDM Tabular Service, returning data in JSON format

    try:
        outputValues = []  # initialize return values (min-max list)

        AddMsgAndPrint(" \nRequesting tabular data for " + splitThousands(len(mukeyList)) + " map units...")
        arcpy.SetProgressorLabel("Sending tabular request to Soil Data Access...")

        # convert the list into a comma seperated string
        mukeys = ",".join(mukeyList)

        sQuery = "SELECT m.mukey, m.nationalmusym as natmusym from mapunit m where mukey in (" + mukeys + ")"

        # Tabular service to append to SDA URL
        theURL = "https://sdmdataaccess.nrcs.usda.gov"
        url = theURL + "/Tabular/SDMTabularService/post.rest"

        dRequest = dict()
        dRequest["FORMAT"] = "JSON+COLUMNNAME+METADATA"
        dRequest["QUERY"] = sQuery

        # Create SDM connection to service using HTTP
        jData = json.dumps(dRequest)

        # Send request to SDA Tabular service
        req = urllib2.Request(url, jData)
        resp = urllib2.urlopen(req)
        jsonString = resp.read()

        #PrintMsg(" \njsonString: " + str(jsonString), 1)
        data = json.loads(jsonString)
        del jsonString, resp, req

        if not "Table" in data:
            raise MyError, "Query failed to select anything: \n " + sQuery

        dataList = data["Table"]     # Data as a list of lists. Service returns everything as string.

        # Get column metadata from first two records
        columnNames = dataList.pop(0)
        columnInfo = dataList.pop(0)

        if len(mukeyList) != len(dataList):
            PrintMsg(" \nWarning! Only returned data for " + str(len(dataList)) + " mapunits", 1)

        PrintMsg(" \nImporting attribute data...", 0)
        newFields = AddNewFields(outputShp, columnNames, columnInfo)

        if len(newFields) == 0:
            raise MyError, ""

        ratingField = newFields[-1]  # last field in query will be used to symbolize output layer

        if len(newFields) == 0:
            raise MyError, ""

        # Create list of outputShp fields to populate (everything but OID)
        desc = arcpy.Describe(outputShp)

        fields = desc.fields
        fieldList = list()

        for fld in fields:
            fldName = fld.name.upper()
            ratingType = fld.type

            if not fld.type == "OID" and not fldName.startswith("SHAPE"):
                fieldList.append(fld.name)

        # The rating field must be included in the query output or the script will fail. This
        # is a weak spot, but it is mostly for demonstration of symbology and map legends.
        #if ratingField in columnNames:
        #    outputIndx = columnNames.index(ratingField)  # Use to identify attribute that will be mapped

        #else:
        #    raise MyError, "Failed to find output field '" + ratingField + "' in " + ", ".join(columnNames)


        # Reading the attribute information returned from SDA Tabular service
        #
        arcpy.SetProgressorLabel("Importing attribute data...")

        dMapunitInfo = dict()
        mukeyIndx = -1
        for i, fld in enumerate(columnNames):
            if fld.upper() == "MUKEY":
                mukeyIndx = i
                break

        if mukeyIndx == -1:
            raise MyError, "MUKEY column not found in query data"

        #PrintMsg(" \nColumnNames (" + str(mukeyIndx) + ") : " + ", ".join(columnNames))
        #PrintMsg(" \n" + str(fieldList), 1)
        noMatch = list()
        cnt = 0

        for rec in dataList:
            try:
                mukey = rec[mukeyIndx]
                dMapunitInfo[mukey] = rec
                #PrintMsg("\t" + mukey + ":  " + str(rec), 1)

            except:
                errorMsg()
                PrintMsg(" \n" + ", ".join(columnNames), 1)
                PrintMsg(" \n" + str(rec) + " \n ", 1)
                raise MyError, "Failed to save " + str(columnNames[i]) + " (" + str(i) + ") : " + str(rec[i])

        # Write the attribute data to the featureclass table
        #
        with arcpy.da.UpdateCursor(outputShp, columnNames) as cur:
            for rec in cur:
                try:
                    mukey = rec[mukeyIndx]
                    newrec = dMapunitInfo[mukey]
                    #PrintMsg(str(newrec), 0)
                    cur.updateRow(newrec)

                except:
                    if not mukey in noMatch:
                        noMatch.append(mukey)

        if len(noMatch) > 0:
            PrintMsg(" \nNo attribute data for mukeys: " + str(noMatch), 1)


        arcpy.SetProgressorLabel("Finished importing attribute data")

        return True

    except MyError, e:
        # Example: raise MyError, "This is an error message"
        PrintMsg(str(e), 2)
        return False

    except urllib2.HTTPError:
        errorMsg()
        PrintMsg(" \n" + sQuery, 1)
        return False

    except:
        errorMsg()
        return False

## ===================================================================================
## ====================================== Main Body ==================================
# Import modules
import sys, string, os, locale, arcpy, traceback, urllib2, httplib, json
from arcpy import env

inputFeature = arcpy.GetParameterAsText(0)

try:

	# Get list of mukeys for use in tabular request
    mukeyList = GetMukeys(inputFeature)

    ratingValues = AttributeRequest(sdaURL, mukeyList, outputShp, sQuery)

except MyError, e:
    # Example: raise MyError, "This is an error message"
    PrintMsg(str(e), 2)

except:
    errorMsg()