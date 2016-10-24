'''
definitions of common reusable sql statements
'''

class SqlString():
    doctypes = {'HEJUD':'JUDGEMENT', 'HFJUD':'JUDGEMENT', 'GCJUD': 'GC_JUDGEMENT',
                    'HEDEC':'DECISION', 'HFDEC':'DECISION', 
                    'HEJP9':'DECISION', 'HFJP9':'DECISION',
                     'HFRES54': 'RESOLUTION_EXECUTION', 'HERES54': 'RESOLUTION_EXECUTION',
                     'HFRES32': 'RESOLUTION_MERITS', 'HERES32': 'RESOLUTION_MERITS',}

    def __init__(self):
        pass
    def insert_case(self,appnostr, titlestr, courtstr='2'):
        sql = u'''INSERT INTO "cases" 
                            SELECT '{appno}',
                                '{title}',
                                {court}
                                WHERE NOT EXISTS(
                                SELECT case_id
                                FROM "cases"
                                WHERE case_id = '{appno}'
                                AND court_id = '{court}'
                                );
                            
                '''
        return sql.format(appno=appnostr, title = titlestr, court = courtstr)

    def insert_case_safe(self):
        sql = u'''INSERT INTO "cases" 
                            SELECT %s,
                                %s,
                                %s
                                WHERE NOT EXISTS(
                                SELECT case_id
                                FROM "cases"
                                WHERE case_id = %s
                                AND court_id = %s
                                );
                            
                '''
        return sql

    
    def insert_casedoc(self,docidstr, datestr, titlestr,
                       doctypestr, pathstr, appnostr, langstr, courtstr='2', ):
        
        doctypestr = self.doctypes[doctypestr]
            
        sql = u'''INSERT INTO
                case_doc(doc_id, date, title, doctype, case_id, court_id, path, lang)
                SELECT
                '{docid}',
                '{date}',
                '{title}',
                '{doctype}',
                '{case_id}',
                '{court_id}',
                '{path}',
                '{lang}'
                 WHERE NOT EXISTS(
                        SELECT doc_id
                        FROM "case_doc"
                        WHERE doc_id = '{docid}'
                        );
            '''
        return sql.format(docid=docidstr,
                          date=datestr,
                          title = titlestr,
                          doctype=doctypestr,
                          case_id = appnostr,
                          court_id=courtstr,
                          path = pathstr,
                          lang = langstr)

    def insert_casedoc_safe(self):
        

            
        sql = u'''INSERT INTO
                case_doc(doc_id, date, title, doctype, case_id, court_id, path, lang)
                SELECT
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
                 WHERE NOT EXISTS(
                        SELECT doc_id
                        FROM "case_doc"
                        WHERE doc_id = %s
                        );
            '''
        return sql
    
    def search_doc_by_appno_date(self, appnostr, datestr):
        sql = u'''
                SELECT * FROM "case_doc"
                WHERE 
                case_doc.case_id 
                IN(
                SELECT 
                  cases.case_id AS case_id
                FROM "cases"
                WHERE 
                  public.cases.case_id = '{appno}'
                )
                '''
        if datestr != None:
            sql +='''
            AND
                case_doc.date = '{date}';
                '''
            return sql.format(appno = appnostr, date = datestr )
        else:
            sql += ';'
            return sql.format(appno = appnostr)
    

##if __name__ == '__main__':
##    s = SqlString()
##    st = s.insert_casedoc('001-1234', '01/01/2011', 'yannis v. greece', 'HFJUD', 'X:/echr/10012_03/jud/', '10012_03')
##    print st
