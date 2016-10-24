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
from retrieve_doc import retrieve_doc, write_doc, retrieve_html, write_html, retrieve_json_for_docid, retrieve_pdf

# def log(mesg):
#     print '['+strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ']' + mesg.encode('utf-8') + ' - '
#     return

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
        
def echr_crawler(mode='ALL'):
    ##################################################################
    # The first URL request can be used to scrape the entire website #
    # whereas the second one to scrape specific date range           #
    ##################################################################
    # http://hudoc.echr.coe.int/webservices/query/eng?q=NOT%20(DOCTYPE%3DPR%20OR%20DOCTYPE%3DHFCOMOLD%20OR%20DOCTYPE%3DHECOMOLD)%20AND%20(documentcollectionid%3D%22DECGRANDCHAMBER%22%20OR%20documentcollectionid%3D%22ADMISSIBILITY%22)%20AND%20(kpdate%3E%3D%222013-09-01T00%3A00%3A00.0Z%22)&s=&st=1&c=20&f=0&TID=hylabgeheb
    # 1.
    URLPREFIX = 'http://hudoc.echr.coe.int/webservices/query/eng?q=NOT%20(DOCTYPE%3DPR%20OR%20DOCTYPE%3DHFCOMOLD%20OR%20DOCTYPE%3DHECOMOLD)%20AND%20(documentcollectionid%3D%22JUDGMENTS%22%20OR%20documentcollectionid%3D%22DECISIONS%22)&s=&st={:d}&c=500&f=0&TID=pctgykraqv'
    # 2. # URLPREFIX = 'http://hudoc.echr.coe.int/webservices/query/eng?q=NOT%20(DOCTYPE%3DPR%20OR%20DOCTYPE%3DHFCOMOLD%20OR%20DOCTYPE%3DHECOMOLD)%20AND%20(documentcollectionid%3D%22JUDGMENTS%22)'
    #      URLPREFIX = URLPREFIX + '%20AND%20(kpdate%3E%3D%222013-06-13T00%3A00%3A00.0Z%22%20AND%20kpdate%3C%3D%222013-07-31T00%3A00%3A00.0Z%22)&s=kpdate%20Ascending&st='
    # 3.  Download decisions of the Grand Chamber and Chamber Decisions 
    # URLPREFIX = 'http://hudoc.echr.coe.int/webservices/query/eng?q=NOT%20(DOCTYPE%3DPR%20OR%20DOCTYPE%3DHFCOMOLD%20OR%20DOCTYPE%3DHECOMOLD)%20AND%20(documentcollectionid%3D%22DECGRANDCHAMBER%22%20OR%20documentcollectionid%3D%22ADMISSIBILITY%22%20OR%20documentcollectionid%3D%22ADMISSIBILITYCOM%22)&s=&st={:d}&c=20&f=0&TID=obveqmytba'
    # 4. Download decisions after a date
    
    #URLPREFIX = 'http://hudoc.echr.coe.int/webservices/query/eng?q=NOT%20(DOCTYPE%3DPR%20OR%20DOCTYPE%3DHFCOMOLD%20OR%20DOCTYPE%3DHECOMOLD)%20AND%20(documentcollectionid%3D%22ADMISSIBILITYCOM%22%20OR%20documentcollectionid%3D%22DECCOMMISSION%22%20OR%20documentcollectionid%3D%22SCREENINGPANEL%22)&s=&st={:d}&c=20&f=0&TID=skgvdmzawl'
    #URLSUFFIX = '&c=20&f=0&TID=fptbfowrso'
    ROOT_PATH = 'X:\\echr\\'
     
    start = int(sys.argv[1])    #starting document
    pause = float(sys.argv[2])    #pause for some seconds between requests specified by argument
    documentCount = start
     
    log = Log()
    log.log_config('echr', 'echr_additional.log')
    logger = log.getLogger()
    handler = log.getHandler()
    fp = open('list.txt', 'w')

            
     
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
                if results["columns"]["HASHTML"] == "0" and results["columns"]["HASPDF"] == "1":
                    appno = string.split(results["columns"]["APPNO"], " ")
                    appno = string.replace(appno[0], '/', '_')
                    title = results["columns"]["DOCNAME"]
                    if title.lower().find('translation') > 0:
                        documentCount += 1
                        continue
                    logger.info('Found pdf for '+appno)
                    
                    print 'Found pdf for '+appno
                    fp.write(doc_id + '-'+ appno + '\n')
                documentCount += 1
                time.sleep(pause)
            start += 500 #increment start to fetch next 20 documents
        #while        
    except urllib2.HTTPError, e:
        logger.critical('!!! ERROR %s!!!' % e.code)
    finally:
        log.close()
        fp.close()


if __name__ == '__main__':
    echr_crawler('ALL')
    
# Testing some boilerplate code
#     log = Log()
#     
#     log.log_config('echr', sys.argv[1])
#     logger = log.getLogger()
#     handler = log.getHandler()
#     logger.info("Hello World of logs")


    
