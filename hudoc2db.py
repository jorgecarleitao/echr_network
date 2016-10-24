import glob
from utils import *
import psycopg2
import os
import json
import codecs
import string
from echr_json import JsonReader
from sql.sql import SqlString


#######################################################################
# Main
#######################################################################


PATH = 'D:\\echr\\'
##flist = filegetter(PATH, filetype = '*.json', subfolder='*\\')

jsr = JsonReader()
flist = []
print "reading files..."
for (dirname, subdirs, files) in os.walk(PATH):
    for f in files:
##        if dirname.find('jud')>0 or dirname.find('dec')>0:
        
        json_count = len(glob.glob(dirname+'\\*.json'))
        if f.find('.json') > 0:
            print f
            fp = open(os.path.join(dirname,f), 'r')
            js = json.load(fp)
            fp.close()

            if jsr.metaExtractor(js['metadata'], 'DOCNAME').find('Translation') < 0:
                #include english metadata files if they don't refer to translations
                flist.append(os.path.join(dirname,f))
##print flist

short_dict = {}
try:
    con = psycopg2.connect(database = 'icourtstemp', user='postgres', password = '1court$')
    cur = con.cursor()
##    con.autocommit=True
    for f in flist:
        print f
        result = jsr.readInfo(f)
        if not result:
            continue
        else:
            (case_id, lang, title, case_dict) = result
        preamble = ['CASE OF ', 'AFFAIRE ']
        for p in preamble:
            if title.strip().startswith(p):
                title = title[len(p):]
            
        if case_id in short_dict:
            if short_dict[case_id]["language"] == "FRENCH" and lang == "ENGLISH":
                short_dict[case_id]["language"] = "ENGLISH"
                short_dict[case_id]["title"] = title
        else:
            short_dict[case_id] = {}
            short_dict[case_id]["title"] = title
            short_dict[case_id]["language"] = lang
            
                
        print case_dict
        if case_dict == {}:
            continue
        sql = SqlString()
        
#         ins_case = sql.insert_case(appnostr=case_dict['case_id'], titlestr = short_dict[case_id]["title"], courtstr='2')
        ins_case = sql.insert_case_safe()
        print `ins_case`
        if lang == "ENGLISH":
            lang = "ENG"
        elif lang == "FRENCH":
            lang = "FRA"
        f = f.replace('D:', 'X:')
#         ins_case_doc = sql.insert_casedoc(
#                     docidstr=case_dict['doc_id'],
#                     datestr = case_dict['date'],
#                     titlestr = case_dict['title'].replace("'", "''"),
#                     #titlestr = lang_dict[case_id]["title"],
#                     doctypestr = case_dict['doctype'],
#                     pathstr = f,
#                     appnostr = case_dict['case_id'],
#                     langstr = lang,
#                     courtstr='2')
        ins_case_doc = sql.insert_casedoc_safe()        
        print `ins_case_doc`
        cur.execute(ins_case, (case_dict['case_id'], short_dict[case_id]["title"], '2', case_dict['case_id'], '2'))
        #case_doc(doc_id, date, title, doctype, case_id, court_id, path, lang)
        cur.execute(ins_case_doc, (case_dict['doc_id'], case_dict['date'], case_dict['title'], SqlString.doctypes[case_dict['doctype']], case_dict['case_id'], '2', f, lang, case_dict['doc_id']))
    con.commit()

except psycopg2.DatabaseError, e:
    if con:
        con.rollback()
    print "Error %s" %e

finally:
    if con:
        con.close()
        
print "Read " + str(len(flist)) + ".json files"
print 5*"-" + 'FINISHED' + 5*'-'
    
    

