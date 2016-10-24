
import urllib2, sys, string
import json
import codecs

def write_doc(p, filename, data):
    #writes a Microsoft Word file with name 'filename' to the p indicated by 'p'
    
    fullpath = p+filename+".docx"        
    fullpath.encode('utf-8')
    
    FILE = open(fullpath, "wb")
    FILE.write(data)
    FILE.close()    
    return

def write_pdf(p, filename, data):
    #writes a pdf file with name 'filename' to the p indicated by 'p'
    
    fullpath = p+filename+".pdf"        
    fullpath.encode('utf-8')
    
    FILE = open(fullpath, "wb")
    FILE.write(data)
    FILE.close()    
    return

def retrieve_doc (doc_id):
    #retrieves a docx file that can be found at a specific url
    theurl = 'http://hudoc.echr.coe.int/webservices/content/docx/' + doc_id + '?TID=fvncppldbw'
    retrieved = False
    while not retrieved:
        try:
            f = urllib2.urlopen(theurl)
            data = f.read()
            f.close()
            retrieved = True
            print 'Fetched '+doc_id+ ' successfully'
            return data
        except urllib2.HTTPError, e:
            print '!!! ERROR %s!!!' % e.code + ' on document id: '+ doc_id
            return None
            #code = e.code
            
            #if (code == 400) or (code == 404):
            #    #retrieved = False
            #    #possibly a network error occured
            #    #pause and continue after a few seconds
            #    pause = 30
            #    sys.stderr.write("Unbound local error, possibly due to network disconnection\n")
            #    sys.stderr.write("Retry to connect in %d seconds" % pause)
            #    time.sleep(pause)
            #
    
    
def write_html(p, filename, data):
    fullpath = p+filename+".html"
    fullpath.encode('utf-8')
    
    FILE = open(fullpath, "w")
    #inject some custom HTML code before and after response text
    FILE.write("""<!DOCTYPE HTML PUBLIC '-//IETF//DTD HTML//EN'>
        <html>
        <head>
        <meta http-equiv='Content-Type'
        content='text/html; charset=UTF-8'>
        </head>
        <body>
        """)
    FILE.write(data)
    FILE.write("""
                </body>
                </html>
                """)
    
    FILE.close()    
    
    return

def retrieve_html(doc_id):
    url = 'http://hudoc.echr.coe.int/webservices/content/eng/body/html/' + doc_id + '?TID=ihnvgvpach'
    try:
    
        f = urllib2.urlopen(url)
        data = f.read()
        f.close()
        return data
    except urllib2.HTTPError, e:
        print '!!! ERROR %s!!!' % e.code + ' on document id: '+ doc_id
        return None

def retrieve_html_from_url(url):
    
    try:
    
        f = urllib2.urlopen(url)
        data = f.read()
        f.close()
        return data
    except urllib2.HTTPError, e:
        print '!!! ERROR %s!!!' % e.code + ' on document url: '+ url
        return None    

def retrieve_pdf(doc_id):
    url = 'http://hudoc.echr.coe.int/webservices/content/pdf/' + doc_id + '?TID=fvncppldbw'
    try:
        f = urllib2.urlopen(url)
        data = f.read()
        f.close()
        print 'Fetched '+url+ ' successfully'
        return data
    except urllib2.HTTPError, e:
        print '!!! ERROR %s!!!' % e.code 
        return None

def retrieve_json_for_docid(doc_id):
    META_URL = "http://hudoc.echr.coe.int/webservices/content/metadata/{docid}?TID=obveqmytba"
    f = urllib2.urlopen(META_URL.format(docid=doc_id))
    metadata = json.load(f)
    return metadata
