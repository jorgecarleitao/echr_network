import urllib.request
import urllib.error
import json
import datetime

import models


# select everything:
SELECT_ALL = 'itemid,applicability,appno,article,conclusion,decisiondate,docname,documentcollectionid,' \
             'documentcollectionid2,doctype,externalsources,importance,introductiondate,issue,judgementdate,' \
             'kpthesaurus,meetingnumber,originatingbody,publishedby,referencedate,kpdate,reportdate,representedby,' \
             'resolutiondate,resolutionnumber,respondent,rulesofcourt,separateopinion,scl,typedescription,ecli'
SELECT_NONE = 'itemid'

META_URL = 'http://hudoc.echr.coe.int/app/query/results' \
      '?query=(contentsitename=ECHR) AND (documentcollectionid:"GRANDCHAMBER" OR documentcollectionid:"CHAMBER")' \
      '&select={select}' + \
      '&sort=&start={start}&length={count}'
META_URL = META_URL.replace(' ', '%20')
META_URL = META_URL.replace('"', '%22')

HTML_URL = 'http://hudoc.echr.coe.int/app/conversion/docx/html/body?library=ECHR&id={doc_id}'


def open_url(url, file_id, reset_cache=False):
    file_name = '_cache/' + file_id + ".html"

    if not reset_cache:
        try:
            with open(file_name) as f:
                return f.read()
        except IOError:
            reset_cache = True

    if reset_cache:
        response = urllib.request.urlopen(url)

        data = response.read()
        encoding = response.info().get_content_charset('utf-8')
        data = data.decode(encoding)

        with open(file_name, "w") as f:
            f.write(data)

        return data


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        return instance


def retrieve_html(doc_id):
    url = HTML_URL.format(doc_id=doc_id)

    return open_url(url, 'doc_%s' % doc_id)


def retrieve_documents(start=0, count=1, select=SELECT_ALL):
    url = META_URL.format(start=start, count=count, select=select)

    data = open_url(url, 'doc_list_%d_%d_all' % (start, count))

    json_object = json.loads(data)

    return json_object["resultcount"], json_object['results']


def parse_articles(doc):

    articles = []
    articles_ids = doc['article'].split(';')
    for article_id in articles_ids:
        try:
            article_id = int(article_id)  # consider only main articles
            #x = get_or_create(session, models.Article, id=article_id)
            articles.append(article_id)
        except ValueError:
            continue

    return articles


def process(docs, session):
    for doc_object in docs:
        json_object = doc_object['columns']
        doc_id = json_object['itemid']
        # todo: pass this to logger
        print(doc_id)

        html = retrieve_html(doc_id)

        doc = models.Document(id=doc_id, scl=json_object['scl'],
                              html=html,
                              case=json_object['appno'],
                              date=parse_date(json_object['kpdate']),
                              case_name=json_object['docname'].replace('CASE OF ', '').replace('v.', 'V.'),
                              tags=json_object['documentcollectionid2'])

        for article_id in parse_articles(json_object):
            article = get_or_create(session, models.Article, id=article_id)
            doc.articles.append(article)

        # merge: if doc already exists in db, update it.
        session.merge(doc)
        session.commit()


def retrieve_and_save(session, start=0, max_docs=None, batch_size=500):

    assert batch_size <= 500, "Batch size must be smaller than 500. " \
                              "The server returns a 400 (Bad request) with more."

    documents_to_retrieve, _ = retrieve_documents()

    if max_docs is not None:
        documents_to_retrieve = min(max_docs-start, documents_to_retrieve)

    batches = documents_to_retrieve//batch_size

    for batch in range(batches):
        _, docs = retrieve_documents(start, batch_size)

        process(docs, session)

        start += batch_size
        documents_to_retrieve -= batch_size

    if documents_to_retrieve > 0:
        assert(documents_to_retrieve < batch_size)

        _, docs = retrieve_documents(start, documents_to_retrieve)
        process(docs, session)


def parse_date(date_string):
    # '29/01/2004 00:00:00'
    return datetime.datetime.strptime(date_string, '%d/%m/%Y %H:%M:%S').date()
