#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Adolfo.Diaz
#
# Created:     06/04/2017
# Copyright:   (c) Adolfo.Diaz 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

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
def splitThousands(someNumber):
    """ will determine where to put a thousands seperator if one is needed.
        Input is an integer.  Integer with or without thousands seperator is returned."""

    try:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(someNumber)[::-1])[::-1]

    except:
        errorMsg()
        return someNumber


import sys, string, os, locale, arcpy, traceback, urllib2, httplib, json, re, socket
from urllib2 import urlopen, URLError, HTTPError
from arcpy import env

if __name__ == '__main__':

    # Total Count of values
    iNumOfValues = 0
    iRequestNum = 1

    # master mukey:natmusym,muname dictionary
    natmusymDict = dict()

    URL = "https://sdmdataaccess.nrcs.usda.gov/Tabular/SDMTabularService/post.rest"

    sQuery = 'SELECT mapunit.mukey, nationalmusym, muname '\
             'FROM sacatalog '\
             'INNER JOIN legend ON legend.areasymbol = sacatalog.areasymbol AND sacatalog.areasymbol IN (\'WI025\') '\
             'INNER JOIN mapunit ON mapunit.lkey = legend.lkey'

##    sQuery = "SELECT m.mukey, m.nationalmusym as natmusym from mapunit m where mukey in ('2809839')"
##    sQuery = "SELECT mukey, nationalmusym, muname as natmusym from mapunit m where mukey in ('2809839')"

    dRequest = dict()
    dRequest["FORMAT"] = "JSON"
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

            except socket.timeout, e:
                AddMsgAndPrint("\n\t" + URL,2)
                AddMsgAndPrint("\tServer Timeout Error", 2)

            except socket.error, e:
                AddMsgAndPrint("\n\t" + URL)
                AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)

            except httplib.BadStatusLine:
                AddMsgAndPrint("\n\t" + URL)
                AddMsgAndPrint("\tNASIS Reports Website connection failure", 2)

    jsonString = resp.read()
    data = json.loads(jsonString)

    # Nothing was returned from SDaccess
    if not "Table" in data:
        AddMsgAndPrint("\tWarning! NATMUSYM value were not returned for any of the " + field + "  values.  Possibly OLD mukey values.",2)
        sys.exit()

    # Add the mukey:natmusym Values to the master dictionary
    for pair in data["Table"]:
        natmusymDict[pair[0]] = (pair[1],pair[2])

    del jData,req,resp,jsonString

    """ --------------------------------------  Check the number of mukeys submitted vs. natmusym values received -----------------------------"""
    # Warn user about a discrepancy in mukey count
    if iNumOfValues != len(natmusymDict):
        AddMsgAndPrint("\tWarning! Values were not returned for " + splitThousands(len(valueList) - len(dataList)) + " MUKEYS", 1)

        # subtract both lists to see which MUKEYS had no NATSYM
        iNoMatches = list(set(valueList) - set([f[0] for f in dataList]))
        AddMsgAndPrint("\n\t\t" + str(iNoMatches),2)
