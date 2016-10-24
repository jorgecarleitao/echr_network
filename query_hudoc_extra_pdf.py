'''
Ultimate version of ECHR downloader
TODO: add query builder with dates, document types etc.
'''
#sends a request to the HUDOC search engine
#the response is JSON

import urllib2
import json
import time, sys
import string
import os
import logging
import codecs
from time import gmtime, strftime
from retrieve_doc import retrieve_doc, write_doc, retrieve_html, write_html, retrieve_json_for_docid, retrieve_pdf, write_pdf
from echr_json import transform 


class Log(object):

    def __init__(self):
        pass
    
    def log_config(self, appname, logname):
        self._logger = logging.getLogger(appname)
        #logging.basicConfig(format = "%(asctime)s -3s %(message)s")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False
        self._handler = logging.FileHandler(logname)
        self._handler.setFormatter(logging.Formatter("%(levelname)-10s - %(asctime)s %(message)s"))
        self._logger.addHandler(self._handler)
        
    def getLogger(self):
        return self._logger
    
    def getHandler(self):
        return self._handler
    
    def close(self):
        self._handler.flush()
        self._handler.close()
        
def echr_crawler(urlstring, mode='ALL'):
    ##################################################################
    # The first URL request can be used to scrape the entire website #
    # whereas the second one to scrape specific date range           #
    ##################################################################
    # http://hudoc.echr.coe.int/webservices/query/eng?q=NOT%20(DOCTYPE%3DPR%20OR%20DOCTYPE%3DHFCOMOLD%20OR%20DOCTYPE%3DHECOMOLD)%20AND%20(documentcollectionid%3D%22DECGRANDCHAMBER%22%20OR%20documentcollectionid%3D%22ADMISSIBILITY%22)%20AND%20(kpdate%3E%3D%222013-09-01T00%3A00%3A00.0Z%22)&s=&st=1&c=20&f=0&TID=hylabgeheb
    # 1.
    URLPREFIX = urlstring
    # 2. # URLPREFIX = 'http://hudoc.echr.coe.int/webservices/query/eng?q=NOT%20(DOCTYPE%3DPR%20OR%20DOCTYPE%3DHFCOMOLD%20OR%20DOCTYPE%3DHECOMOLD)%20AND%20(documentcollectionid%3D%22JUDGMENTS%22)'
    #      URLPREFIX = URLPREFIX + '%20AND%20(kpdate%3E%3D%222013-06-13T00%3A00%3A00.0Z%22%20AND%20kpdate%3C%3D%222013-07-31T00%3A00%3A00.0Z%22)&s=kpdate%20Ascending&st='
    # 3.  Download decisions of the Grand Chamber and Chamber Decisions 
    # URLPREFIX = 'http://hudoc.echr.coe.int/webservices/query/eng?q=NOT%20(DOCTYPE%3DPR%20OR%20DOCTYPE%3DHFCOMOLD%20OR%20DOCTYPE%3DHECOMOLD)%20AND%20(documentcollectionid%3D%22DECGRANDCHAMBER%22%20OR%20documentcollectionid%3D%22ADMISSIBILITY%22%20OR%20documentcollectionid%3D%22ADMISSIBILITYCOM%22)&s=&st={:d}&c=20&f=0&TID=obveqmytba'
    # 4. Download decisions after a date
    
    #URLPREFIX = 'http://hudoc.echr.coe.int/webservices/query/eng?q=NOT%20(DOCTYPE%3DPR%20OR%20DOCTYPE%3DHFCOMOLD%20OR%20DOCTYPE%3DHECOMOLD)%20AND%20(documentcollectionid%3D%22ADMISSIBILITYCOM%22%20OR%20documentcollectionid%3D%22DECCOMMISSION%22%20OR%20documentcollectionid%3D%22SCREENINGPANEL%22)&s=&st={:d}&c=20&f=0&TID=skgvdmzawl'
    #URLSUFFIX = '&c=20&f=0&TID=fptbfowrso'
    ROOT_PATH = 'D:\\echr\\2014\\'
     
    start = int(sys.argv[1])    #starting document
    pause = float(sys.argv[2])    #pause for some seconds between requests specified by argument
    documentCount = start
     
    log = Log()
    log.log_config('echr', 'echr_2014.log')
    logger = log.getLogger()
    handler = log.getHandler()
    
     
    try:
        #run an initial GET query to determine the document count
        #theurl = URLPREFIX + str(start) +URLSUFFIX
        theurl = URLPREFIX.format(start) 
        f = urllib2.urlopen(theurl)
        data = json.load(f)
        totaldocs = int(data["resultcount"])
        sys.stderr.write('Total documents are: %d\n' %totaldocs)
        #--- Testing code only ---
        #f.close()
         
        #FILE = open('response.json', "w")
        #FILE.write(data)
        #FILE.close()
        while documentCount <= totaldocs:
            theurl = URLPREFIX.format(start)
            f = urllib2.urlopen(theurl)
            data = json.load(f)
            #retrieve the 1st result and from the columns object
            #retrieve the ITEMID attribute
            for results in data["results"]:
                #we are not interested in documents where "DOCUMENTCOLLECTIONID": "CASELAW JUDGMENTS COMMITTEE ENG|FRA"
                #those are documents that correspond to committee judgements
                doc_id = results["columns"]["ITEMID"]
                logger.info("Processing document count:" + str(documentCount))
                sys.stderr.write("Processing document count:" + str(documentCount)+"\n")
                 
                #if results["columns"]["HASDOCX"] == "1":
                if results["columns"]["HASHTML"] == "1" or results["columns"]["HASPDF"] == "1":
                    appno = string.split(results["columns"]["APPNO"], " ")
                    appno = string.replace(appno[0], '/', '_')
                    p = ROOT_PATH+ appno +"\\"

     
                    name = results["columns"]["DOCNAME"]
                    if name.lower().find('translation') > 0:
                        documentCount += 1
                        continue
                     
                    invalidChars = ['\"',
                                    '[',
                                    ']',
                                    '/',
                                    '|',
                                    '<',
                                    '>',
                                    '*',
                                    ';']
                    for ch in invalidChars:
                        if string.find(name, ch) >= 0:
                            name = string.replace(name, ch, '')
                            
                    judg_type = results["columns"]["DOCTYPE"]
                    
                    #Redirect file to the appropriate directory
                    #based on the document type (decision or judgment)
                    if judg_type == "HEDEC" or judg_type == "HFDEC" or judg_type == "HEJP9" or judg_type == "HFJP9":
                        logger.debug('This is a decision text for case:'+appno);
                        p += 'dec\\'
                        
                    elif judg_type == "HEJUD" or judg_type == "HFJUD":
                        p += 'jud\\'
                    
                    elif judg_type == "HERES54" or judg_type == 'HFRES54' or judg_type == 'HFRES32' or judg_type == 'HERES32' :
                        p += 'res\\'
                    else:
                        logger.warning("Document doesn't have one of the recognized DOCUMENTTYPES can be a translation")
                        continue
                    
                    
                    if not os.path.exists(p):
                        os.makedirs(p)

                    if len(p + '\\' + name) > 255:
                        name = name[:255-len(p + '\\' + name)-1]
                    logger.info("Case name: "+ name)

                    if os.path.exists(p+doc_id+'.json'):
                        #decision exists skip!
                        logger.debug("Skipped name: "+ name + " doc_id "+ doc_id)
                        print "Skipped "+ " doc_id "+ doc_id
                        time.sleep(pause)
                        documentCount += 1
                        continue
                    
                    
                    if mode == 'ALL':
                        data = retrieve_doc(doc_id)
                        if data is None:
                            logger.info("Case name: "+ name +" was not found" )
                            continue
                        else:
                            logger.info("Writing doc for:"+appno)
                            sys.stderr.write("Writing doc for:"+appno+"\n")
                            write_doc(p, name, data)
                         
                        time.sleep(pause)
                        data = retrieve_html(doc_id)
                        if data is None:
                            logger.info("Case name: "+ name +" was not found" )
                            continue
                        else:
                            logger.info("Writing html for:"+appno)
                            write_html(p, name, data)

                        if results["columns"]["HASHTML"] == "0" and results["columns"]["HASPDF"] == "1":
                            data = retrieve_pdf(doc_id)
                            logger.info("Writing pdf for:"+appno)
                            write_pdf(p,name,data)
                            
                    
                    FILE = codecs.open(p+doc_id+'.json', 'w', encoding = 'UTF-8')
                    metadata = retrieve_json_for_docid(doc_id)
                    metadata = transform(metadata)
                    json.dump(metadata, FILE, indent = 2)
                    FILE.close()
                else:
                    logger.info( "Case id " + doc_id + " has no document attached" )
                    
                time.sleep(pause)
                documentCount += 1
            start += 500 #increment start to fetch next 20 documents
        #while        
    except urllib2.HTTPError, e:
        logger.critical('!!! ERROR %s!!!' % e.code)
    finally:
        print '='*3 + ' END ' + '='*3
        print 'Documents are dowloaded in ' + ROOT_PATH
        log.close()


if __name__ == '__main__':
    urlstring = 'http://hudoc.echr.coe.int/app/query/results?query='
    urlstring += '((((((((((((((((((((%20contentsitename%3AECHR%20AND%20(NOT%20(doctype%3DPR%20OR%20doctype%3DHFCOMOLD%20OR%20doctype%3DHECOMOLD))%20AND%20((languageisocode%3D%22ENG%22)%20OR%20(languageisocode%3D%22FRE%22))%20AND%20((documentcollectionid%3D%22JUDGMENTS%22)%20OR%20(documentcollectionid%3D%22DECISIONS%22)%20OR%20(documentcollectionid%3D%22RESOLUTIONS%22))%20AND%20(kpdate%3E%3D%222014-03-01T00%3A00%3A00.0Z%22%20AND%20kpdate%3C%3D%222014-12-31T00%3A00%3A00.0Z%22))%20XRANK(cb%3D14)%20doctypebranch%3AGRANDCHAMBER)%20XRANK(cb%3D13)%20doctypebranch%3ADECGRANDCHAMBER)%20XRANK(cb%3D12)%20doctypebranch%3ACHAMBER)%20XRANK(cb%3D11)%20doctypebranch%3AADMISSIBILITY)%20XRANK(cb%3D10)%20doctypebranch%3ACOMMITTEE)%20XRANK(cb%3D9)%20doctypebranch%3AADMISSIBILITYCOM)%20XRANK(cb%3D8)%20doctypebranch%3ADECCOMMISSION)%20XRANK(cb%3D7)%20doctypebranch%3ACOMMUNICATEDCASES)%20XRANK(cb%3D6)%20doctypebranch%3ACLIN)%20XRANK(cb%3D5)%20doctypebranch%3AADVISORYOPINIONS)%20XRANK(cb%3D4)%20doctypebranch%3AREPORTS)%20XRANK(cb%3D3)%20doctypebranch%3AEXECUTION)%20XRANK(cb%3D2)%20doctypebranch%3AMERITS)%20XRANK(cb%3D1)%20doctypebranch%3ASCREENINGPANEL)%20XRANK(cb%3D4)%20importance%3A1)%20XRANK(cb%3D3)%20importance%3A2)%20XRANK(cb%3D2)%20importance%3A3)%20XRANK(cb%3D1)%20importance%3A4)%20XRANK(cb%3D2)%20languageisocode%3AENG)%20XRANK(cb%3D1)%20languageisocode%3AFRE&select=sharepointid,Rank,itemid,docname,doctype,application,appno,conclusion,importance,originatingbody,typedescription,kpdate,kpdateAsText,documentcollectionid,documentcollectionid2,languageisocode,extractedappno,isplaceholder,doctypebranch,respondent,respondentOrderEng,ecli'                
    urlstring +='&sort=&start={:d}&length=500&rankingModelId=4180000c-8692-45ca-ad63-74bc4163871b'
     
    
    #===========================================================================
    # urlstring +='(documentcollectionid%3D%22RESOLUTIONS%22)'
    # urlstring +='&s=&st={:d}&c=500&f=0&TID=pctgykraqv'
    #===========================================================================
    
    echr_crawler(urlstring, mode='ALL')
    



    
