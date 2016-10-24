import json
import os
import codecs

def transform(js):
        values = js['metadata']
        new_values = dict()

        for val in values:
                key = val['name']
                value = val['value']
                new_values[key] = value
        js['metadata'] = new_values
        
        return js
    
class JsonReader():
    def __init__(self):
        pass

    def metaExtractor(self, metaArray, metaname):
        val = [m['value'] for m in metaArray if m['name'] == metaname]
        return val[0].strip()

    def readInfo(self, jsonFile):
        '''
            read metadata file and
            returns a dictionary of metadata
        '''
        print '!!! json reader !!! '+jsonFile
        jf = codecs.open(jsonFile, 'r', encoding = 'utf-8')
        js = json.load(jf)
        jf.close()

        print js['itemid']
        
        jsdict = {}
        

        #t = [m[value] for m in js[metadata] if m[name] == "Title"]
        title = self.metaExtractor(js['metadata'], 'DOCNAME').upper()
        title = title.replace("'", "''")    
        
        if len(title)>500:
            title = title[:499]
        if title.find('TRANSLATION') < 0:
            #exclude translations
            jsdict['title'] = title
            appnostr = self.metaExtractor(js['metadata'], 'APPNO')
            #in case there is a list of appno's take only the first one
            appno = appnostr.split(';')[0].strip()
            
            if appno == '':
                #in some rare cases ECHR separates appnos by ';' only that the first one is empty!
                appno = appnostr.split(';')[1].strip()
            jsdict['case_id'] = appno
            
            doctype = self.metaExtractor(js['metadata'], 'DOCUMENTTYPE')
            jsdict['doctype'] = doctype
            court = self.metaExtractor(js['metadata'], 'ORIGINATINGBODY')
            if court.find("Grand")>0 and doctype[-3:] == 'JUD' :
                #distinguish the Grand Chamber judgements
                #notice court.find("Grand")>0 detects both 'Grand Chamber and Grande Chambre
                jsdict['doctype'] = 'GCJUD'
                
            #different document tpyes have dates at a different place in json
            if doctype[-3:] == 'DEC'  or doctype[-3:] == 'JP9':
                jsdict['date'] = self.metaExtractor(js['metadata'], 'DECISIONDATE')
            elif doctype[-3:] == 'JUD':
                jsdict['date'] = self.metaExtractor(js['metadata'], 'JUDGEMENTDATE')
            elif doctype[2:5] == 'RES':
                jsdict['date'] = self.metaExtractor(js['metadata'], 'RESOLUTIONDATE')
            else:
                print 'Unmatched document type possibly translation'
                return None
            
            jsdict['doc_id'] = self.metaExtractor(js['metadata'], 'UNIQUEITEMID')
            jsdict['caselaw'] = self.metaExtractor(js['metadata'], 'SCL')
            jsdict['keywords'] = self.metaExtractor(js['metadata'], 'KPTHESAURUS')
            jsdict['state'] = self.metaExtractor(js['metadata'], 'RESPONDENT')
            artlist= self.metaExtractor(js['metadata'], 'ARTICLE')
            
            jsdict['articles'] = [ s.strip() for s in artlist.split(';')]
            lang = self.metaExtractor(js['metadata'], 'METADATALANGUAGE').upper()
        else:
            print 'translation'
            return None
        return (jsdict['case_id'], lang, title, jsdict)
