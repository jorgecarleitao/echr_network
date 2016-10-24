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
from echr_json import transform
from time import gmtime, strftime
from retrieve_doc import retrieve_doc, write_doc, retrieve_html, write_html, retrieve_json_for_docid, retrieve_pdf, write_pdf

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
        
def echr_crawler(urlstring, logname, mode='ALL', start=1, pause=1.0):
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
    ROOT_PATH = 'D:\\echr\\summaries\\'
     
    documentCount = start
     
    log = Log()
    log.log_config('echr', logname)
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
                logger.info("This has id:" + results["columns"]["ITEMID"] + " and title:" + results["columns"]["DOCNAME"])
                
                documentCount += 1

                name = doc_id
                
                #if results["columns"]["HASDOCX"] == "1":
                if results["columns"]["HASHTML"] == "1" or results["columns"]["HASPDF"] == "1":
                    appno = string.split(results["columns"]["APPNO"], " ")
                    appno = string.replace(appno[0], '/', '_')
                    lang = results["columns"]["LANGUAGEISOCODE"]
                    
                    #GET DATE AND CONVERT IT TO yyymmdd                    
                    date = results["columns"]["KPDATE"]
                    date = date.split("T")[0].replace("-","")
                    
                    #make a path that consists of the root path, application number, sum_<lang>, date in yyyymmdd
                    p = os.path.join(ROOT_PATH, appno, 'sum_'+lang[:2].lower(), date)
                    
                    logger.info("Processing case: " + doc_id + " of date " + date)
                    
                    if not os.path.exists(p):
                        os.makedirs(p)
                   

                    if os.path.exists(p+doc_id+'.json'):
                        #decision exists skip!
                        logger.debug("Skipped doc_id: "+ doc_id)
                        print "Skipped "+ " doc_id "+ doc_id
                        time.sleep(pause)
                        #documentCount += 1
                        continue
                    
                    

                    if results["columns"]["HASHTML"] == "0":
                        data = retrieve_doc(doc_id)
                        if data is None:
                            logger.info("Word for docid: "+ doc_id +" was not found" )
                            continue
                        else:
                            logger.info("Writing doc for:"+appno)
                            sys.stderr.write("Writing doc for:"+appno+"\n")
                            write_doc(p+'\\', name, data)
                    else: 
                        time.sleep(pause)
                        data = retrieve_html(doc_id)
                        if data is None:
                            logger.info("Html for "+ name +" was not found" )
                            continue
                        else:
                            logger.info("Writing html for:"+appno)
                            write_html(p+'\\', name, data)
                        
                    if mode == 'ALL':
                        if results["columns"]["HASHTML"] == "0" and results["columns"]["HASPDF"] == "1":
                            data = retrieve_pdf(doc_id)
                            if data is None:
                                logger.info("Dodn't fin pdf for:" + doc_id )
                                continue
                            else:
                                logger.info("Writing pdf for:"+appno)
                                write_pdf(p+'\\',name,data)
                            
                    
                    #===========================================================
                    # FILE = codecs.open(p+doc_id+'.json', 'w', encoding = 'UTF-8')
                    # metadata = transform(retrieve_json_for_docid(doc_id))
                    # json.dump(metadata, FILE, indent = 4)
                    # logger.info('Wrote json for:' + doc_id)
                    # FILE.close()
                    #===========================================================
                else:
                    logger.info( "Case id " + doc_id + " has no document attached" )
                    
                time.sleep(pause)
                #documentCount += 1
            start += 500 #increment start to fetch next documents
        #while        
    except urllib2.HTTPError, e:
        logger.critical('!!! ERROR %s!!!' % e.code)
    finally:
        print '='*3 + ' END ' + '='*3
        print 'Documents are dowloaded in ' + ROOT_PATH
        log.close()


if __name__ == '__main__':
    urlstring = 'http://hudoc.echr.coe.int/webservices/query/eng?'
    urlstring += 'q=NOT%20(DOCTYPE%3DPR%20OR%20DOCTYPE%3DHFCOMOLD%20OR%20DOCTYPE%3DHECOMOLD)%20AND%20(documentcollectionid%3D%22CLIN%22)&s=kpdate%20Ascending&st={0}&c=500&f=0&TID=dxddtcwhox'
    

    # urlstring += 'q=NOT%20(DOCTYPE%3DPR%20OR%20DOCTYPE%3DHFCOMOLD%20OR%20DOCTYPE%3DHECOMOLD)'
    # urlstring += '(languageisocode%3D%22ENG%22%20OR%20languageisocode%3D%22FRA%22)%20AND%20'
    # urlstring +='(documentcollectionid%3D%22RESOLUTIONS%22)%20AND%20'
    # urlstring +='(kpdate%3E%3D%222013-09-27T00%3A00%3A00.0Z%22%20AND%20kpdate%3C%3D%222013-12-31T00%3A00%3A00.0Z%22)'
    start = int(sys.argv[1])
    pause = float(sys.argv[2]) 
    echr_crawler(urlstring, logname = 'summaries.log', mode='ALL', start=start, pause=pause )
    

    
