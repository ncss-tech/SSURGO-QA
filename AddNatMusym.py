#-------------------------------------------------------------------------------
# Name:        AddNATMusym
#              Add National Mapunit Symbol
#
# Author: Adolfo.Diaz
# e-mail: adolfo.diaz@wi.usda.gov
# phone: 608.662.4422 ext. 216
#
# Created:     2/21/2017
# Last Modified: 2/21/2017

# Code copied from SDA_CustomQuery script and modified to get NationalMusym from Soil Data Access
# Steve Peaslee 10-18-2016

# Completely modified by Adolfo Diaz 02/21/2017 to update a user specific feature layer.
# Due to limitations from SDMaccess in terms of the number of mukeys it can accept the total
# number of mukeys need to be split into lists of no more than 1000 mukeys.
#

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

## ================================================================================================================
def GetUniqueValues(theInput,theField):
    # Create a list of unique values from spatial layer for use in SDA query

    try:
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

        AddMsgAndPrint("\nCompiling a list of unique" + theField + " values from " + splitThousands(featureCount) + " polygons")

        valueList = list()

        arcpy.SetProgressor("step", "Compiling a list of unique" + theField + "values", 0, featureCount,1)
        if featureCount:

            with arcpy.da.SearchCursor(theInput, [theField]) as cur:
                for rec in cur:

                    if bAreaSym:
                        if not len(rec[0]) == 5:
                            AddMsgAndPrint("\t" + str(rec[0]) + " is not a valid AREASYMBOL",2)
                            continue

                    if not rec[0] in valueList:
                        valueList.append(rec[0])

                    arcpy.SetProgressorPosition()
            arcpy.ResetProgressor()

            AddMsgAndPrint("\tThere are " + splitThousands(len(valueList)) + " unique" + theField + " values")

        else:
            AddMsgAndPrint("\n\tThere are no features in layer.  Empty Geometry. EXITING",2)
            sys.exit()

        if not len(valueList):
            AddMsgAndPrint("\n\tThere were no" + theField + " values in layer. EXITING",2)
            sys.exit()

        # if number of Areasymbols exceed 300 than parse areasymbols
        # into lists containing no more than 300 areasymbols
        if bAreaSym:
            if len(valueList) > 300:
                return parseMukeysIntoLists(valueList,300)
            else:
                return valueList
        else:
            return parseMukeysIntoLists(valueList)

    except:
        errorMsg()
        AddMsgAndPrint("\nCould not retrieve list of unique values from " + theField + " field",2)
        sys.exit()

## ===============================================================================================================
def parseValuesIntoLists(valueList,limit=1000):
    """ This function will parse values into manageable chunks that will be sent to the SDaccess query.
        This function returns a list containing lists of values comprised of no more than what
        the 'limit' is set to. Default Limit set to 1000, this will be used if the value list is
        made up of MUKEYS.  Limit will be set to 300 if value list contains areasymbols"""

    try:
        arcpy.SetProgressorLabel("\nDetermining the number of requests to send to SDaccess Server")

        i = 0 # Total Count
        j = 0 # Mukey count; resets whenever the 'limit' is reached.

        listOfValueStrings = list()  # List containing lists of values
        tempValueList = list()

        for value in valueList:
            i+=1
            j+=1
            tempValueList.append(value)

            # End of mukey list has been reached
            if i == len(valueList):
                listOfValueStrings.append(tempValueList)

            # End of mukey list NOT reached
            else:
                # max limit has been reached; reset tempValueList
                if j == limit:
                    listOfValueStrings.append(tempValueList)
                    tempMukeyList = []
                    j=0

        del i,j,tempValueList

        if not len(listOfValueStrings):
            AddMsgAndPrint("\tCould not Parse value list into manageable sets",2)
            sys.exit()

        else:
            AddMsgAndPrint("\t" + str(len(listOfValueStrings)) + " request(s) are needed to obtain NATSYM values for this layer")
            return listOfMukeyStrings

    except:
        AddMsgAndPrint("Unhandled exception (parseValuesIntoLists)", 2)
        errorMsg()
        sys.exit()

## ===================================================================================
def getNATMUSYM(listsOfValues, featureLayer):
    """POST REST which uses urllib and JSON to send query to SDM Tabular Service and
       returns data in JSON format.  Sends a list of values (either MUKEYs or Areasymbols)
       and returns NATSYM values.  If MUKEYS are submitted a pair of values are returned
       [MUKEY,NATMUSYM].  If areasymbols are submitted than a list of all of MUKEY,NATSYM
       pairs that pertain to that areasymbol are returned.
       Adds NATMUSYM field to inputFeature layer if not present and populates."""

    try:

        AddMsgAndPrint("\nSubmitting " + str(len(listsOfValues)) + " request(s) to the SDMaccess")
        arcpy.SetProgressor("step", "Sending tabular request to Soil Data Mart Access", 0, len(listsOfValues),1)

        # Total Count of values
        iNumOfValues = 0
        iRequestNum = 1

        # master mukey:natmusym,muname dictionary
        natmusymDict = dict()

        # SDMaccess URL
        URL = "https://sdmdataaccess.nrcs.usda.gov/Tabular/SDMTabularService/post.rest"

        """ ---------------------------------------- Iterate through lists of MUKEYS to submit requests for natsym ------------------------------"""
        # Iterate through each MUKEY list that has been parsed for no more than 1000 mukeys
        for valueList in listsOfValues:

            arcpy.SetProgressorLabel("Requesting NATSYM values for " + str(len(valueList)) + " mukeys. Request " + str(iRequestNum) + " of " + str(len(listsOfValues)))

            iNumOfValues+=len(valueList)
            iRequestNum+=1

            # convert the list into a comma seperated string
            values = ",".join(valueList)

            # use this query if submitting natsym request by areasymbol
            if bAreaSym:
                sQuery = 'SELECT mapunit.mukey, nationalmusym, muname '\
                          'FROM sacatalog' \
                          'INNER JOIN legend ON legend.areasymbol = sacatalog.areasymbol AND sacatalog.areasymbol IN ("' + values + '")' \
                          'INNER JOIN mapunit ON mapunit.lkey = legend.lkey'

            else:
                # 'SELECT m.mukey, m.nationalmusym as natmusym from mapunit m where mukey in (753574,2809844,753571)'
                sQuery = "SELECT m.mukey, m.nationalmusym as natmusym from mapunit m where mukey in (" + values + ")"
                sQuery = "SELECT m.mukey, m.nationalmusym, m.muname as natmusym from mapunit m where mukey in (" + values + ")"
                #sQuery = "SELECT m.mukey, m.nationalmusym as natmusym from legend AS l INNER JOIN mapunit AS m ON l.lkey=m.mukey AND m.mukey in (" + mukeys + ")"

            # Create request using JSON, return data as JSON
            dRequest = dict()
            dRequest["FORMAT"] = "JSON"
            #dRequest["FORMAT"] = "JSON+COLUMNNAME+METADATA"
            dRequest["QUERY"] = sQuery
            jData = json.dumps(dRequest)

            # Send request to SDA Tabular service using urllib2 library
            req = urllib2.Request(URL, jData)

            """ --------------------------------------  Try connecting to SDaccess to read JSON response - You get 3 tries ------------------------"""
            try:
                resp = urllib2.urlopen(req)
            except:
                try:
                    AddMsgAndPrint("\t2nd attempt at requesting data")
                    resp = urllib2.urlopen(req)

                except:
                    try:
                        AddMsgAndPrint("\t3rd attempt at requesting data")
                        resp = urllib2.urlopen(req)

                    except URLError, e:
                        AddMsgAndPrint(sQuery)
                        if hasattr(e, 'reason'):
                            AddMsgAndPrint("\n\t" + URL,2)
                            AddMsgAndPrint("\tURL Error: " + str(e.reason), 2)

                        elif hasattr(e, 'code'):
                            AddMsgAndPrint("\n\t" + URL,2)
                            AddMsgAndPrint("\t" + e.msg + " (errorcode " + str(e.code) + ")", 2)

                        return False

                    except socket.timeout, e:
                        AddMsgAndPrint("\n\t" + URL,2)
                        AddMsgAndPrint("\tServer Timeout Error", 2)
                        return False

                    except socket.error, e:
                        AddMsgAndPrint("\n\t" + URL)
                        AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)
                        return False

                    except httplib.BadStatusLine:
                        AddMsgAndPrint("\n\t" + URL)
                        AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)
                        return False

            jsonString = resp.read()
            data = json.loads(jsonString)

            """{u'Table': [[u'mukey', u'natmusym',u'muname'],
                        [u'ColumnOrdinal=0,ColumnSize=4,NumericPrecision=10,NumericScale=255,ProviderType=Int,IsLong=False,ProviderSpecificDataType=System.Data.SqlTypes.SqlInt32,DataTypeName=int',
                         u'ColumnOrdinal=1,ColumnSize=6,NumericPrecision=255,NumericScale=255,ProviderType=VarChar,IsLong=False,ProviderSpecificDataType=System.Data.SqlTypes.SqlString,DataTypeName=varchar'],
                        [u'753571', u'2tjpl'],
                        [u'753574', u'2szdz'],
                        [u'2809844', u'2v3f0']]}"""

            # Nothing was returned from SDaccess
            if not "Table" in data:
                AddMsgAndPrint("\tWarning! NATMUSYM value were not returned for any of the " + field + "  values.  Possibly OLD mukey values.",2)
                continue

            # Add the mukey:natmusym Values to the master dictionary
            for pair in data["Table"]:
                natmusymDict[pair[0]] = (pair[1],pair[2])

            del jData,req,resp,jsonString,data

##        # Remove the first 2 items from dataList: fields and column metadata-columninfo
##        """ [[u'753571', u'2tjpl'], [u'753574', u'2szdz'], [u'2809844', u'2v3f0']] """
##        columnNames = dataList.pop(0)  # [u'mukey', u'natmusym']
##        columnInfo = dataList.pop(0)

        """ --------------------------------------  Check the number of mukeys submitted vs. natmusym values received -----------------------------"""
        # Warn user about a discrepancy in mukey count
        if iNumOfValues != len(natmusymDict):
            AddMsgAndPrint("\tWarning! NATMUSYM value was not returned for the following " + splitThousands(len(valueList) - len(dataList)) + " MUKEYS", 1)

            # subtract both lists to see which MUKEYS had no NATSYM
            iNoMatches = list(set(valueList) - set([f[0] for f in dataList]))
            AddMsgAndPrint("\n\t\t" + str(iNoMatches),2)

        """ --------------------------------------------------  Add NATMUSYM to the Feature Layer ---------------------------------------------------"""
        # Add the 'NATMUSYM' field to inputFeature if not present
        if not "natmusym" in [f.name.lower() for f in arcpy.ListFields(featureLayer)]:
            arcpy.AddField_management(featureLayer,'NATMUSYM','TEXT','#','#',23,'National MU Symbol')

        mukeyField = FindField(featureLayer,"MUKEY")

        AddMsgAndPrint("\nImporting NATMUSYM Values",0)
        arcpy.SetProgressor("step", "Importing NATMUSYM Values into " + os.path.basename(featureLayer) + " layer", 0, len(natmusymDict),1)

        # itereate through mukey,natmusym values and update the NATMUSYM field
        # [[u'753571', u'2tjpl'], [u'753574', u'2szdz'], [u'2809844', u'2v3f0']]
        for rec in natmusymDict:

            mukey,natmusym = rec,natmusymDict[rec]
            arcpy.SetProgressorLabel("Importing NATMUSYM Values: " + mukey + " : " + natmusym)

            expression = arcpy.AddFieldDelimiters(featureLayer,mukeyField) + " = '" + mukey + "'"
            with arcpy.da.UpdateCursor(featureLayer, 'NATMUSYM', where_clause=expression) as cursor:

                for row in cursor:
                    row[0] = natmusym

                    cursor.updateRow(row)

            arcpy.SetProgressorPosition()

        arcpy.ResetProgressor()

        AddMsgAndPrint("\tSuccessfully populated 'NATMUSYM' values for " + splitThousands(int(arcpy.GetCount_management(featureLayer).getOutput(0))) + " polygons \n",0)
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
import sys, string, os, locale, arcpy, traceback, urllib2, httplib, json, re, socket
from urllib2 import urlopen, URLError, HTTPError
from arcpy import env

if __name__ == '__main__':

    inputFeature = arcpy.GetParameterAsText(0)
    #inputFeature = r'C:\Temp\Export_Output.shp'

    try:
        try:
            FindField(theInput,"AREASYMBOL")
            field = "AREASYMBOL"
            bAreaSym = True
        except:
            try:
                FindField(theInput,"MUKEY")
                field = "MUKEY"
                bAreaSym = False
            except:
                AddMsgAndPrint("\t\"AREASYMBOL\" and \"MUKEY\" fields are missing! -- Need one or the other to continue.  EXITING!",2)
                sys.exit()

    	# Get list of unique mukeys for use in tabular request
        uniqueValueList = GetUniqueValues(inputFeature,field)

        # populate inputFeature with NATMUSYM
        if not getNATMUSYM(uniqueValueList, inputFeature):
            AddMsgAndPrint("\nFailed to update NATSYM field",2)

    except:
