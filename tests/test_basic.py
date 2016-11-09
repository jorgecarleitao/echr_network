import unittest
import os.path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import crawler
import models


engine = create_engine('sqlite:///:memory:', echo=False)
Session = sessionmaker(bind=engine)


class TestGet(unittest.TestCase):

    def setUp(self):
        models.Base.metadata.create_all(engine)

    def tearDown(self):
        models.Base.metadata.drop_all(engine)

    def test_get(self):
        count, docs = crawler.retrieve_documents()

        self.assertTrue(count > 0)
        self.assertEqual(docs[0]['columns']['itemid'], '001-61414')

    def test_parse_articles(self):
        count, docs = crawler.retrieve_documents()

        articles = crawler.parse_articles(docs[0]['columns'])

        self.assertEqual(len(articles), 2)

    def test_process_document(self):

        session = Session()

        _, docs = crawler.retrieve_documents()

        crawler.process(docs, session)

        doc = session.query(models.Document).first()

        # test id
        self.assertEqual(doc.id, '001-61414')

        # test date
        self.assertEqual(doc.date.strftime('%d/%m/%Y'), '28/10/2003')

        # test case name
        self.assertEqual(doc.case_name, 'RAKEVICH V. RUSSIA')

        # test scl
        self.assertIn('Abdulaziz', doc.scl)
        self.assertIn('Wassink v. the Netherlands', doc.scl)

        # test
        self.assertEqual(doc.tags, 'CASELAW;JUDGMENTS;CHAMBER;ENG')

        # test articles creation
        self.assertEqual(session.query(models.Article).count(), 2)

        # test relations creation
        docs_refering_article_5 = session.query(models.Article)\
            .join(models.Article.documents)\
            .filter(models.Article.id == '5')\
            .count()
        self.assertEqual(docs_refering_article_5, 1)

        self.assertIn("judicial review of her detention was deficient in its scope, "
                      "fairness and speed. She also maintained", doc.html)

    def test_retrieve_html(self):
        count, docs = crawler.retrieve_documents()

        html = crawler.retrieve_html(docs[0]['columns']['itemid'])

        self.assertIn("judicial review of her detention was deficient in its scope, "
                      "fairness and speed. She also maintained", html)

    def test_retrieve_few(self):
        """
        Retrieve fewer items than one batch
        """
        session = Session()
        crawler.retrieve_and_save(session, 0, 10, 20)

        count = session.query(models.Document).count()

        self.assertEqual(count, 10)

    def test_retrieve_many(self):
        """
        Retrieve more items than one batch, number of items is not dividable by batch size
        """
        session = Session()

        crawler.retrieve_and_save(session, 0, 11, 2)

        count = session.query(models.Document).count()

        self.assertEqual(count, 11)

    def test_update_doc(self):
        session = Session()

        _, docs = crawler.retrieve_documents()

        crawler.process(docs, session)

        doc = session.query(models.Document).first()

        doc.html = 'test'
        doc.articles[:] = []
        session.add(doc)
        session.commit()

        _, docs = crawler.retrieve_documents()

        crawler.process(docs, session)

        doc = session.query(models.Document).first()
        self.assertNotEqual(len(doc.articles), 0)
        self.assertNotEqual(doc.html, 'test')

    def test_process_case_name(self):
        name = crawler.process_case_name('MOLDOVAN AND  OTHERS v ROMANIA (No. 2)')
        self.assertTrue('  ' not in name)

        self.assertTrue('No.' not in name)
        self.assertTrue('NO.' in name)
        self.assertTrue(' v ' not in name)
        self.assertTrue(' V ' in name)


class TestAuxiliary(unittest.TestCase):

    def setUp(self):
        models.Base.metadata.create_all(engine)

        if os.path.isfile('_cache/example.html'):
            os.remove('_cache/example.html')

    def test_url(self):
        # open without cache file
        data = crawler.open_url('http://www.example.com', 'example')

        self.assertTrue(os.path.isfile('_cache/example.html'))

        # open with cache file
        data1 = crawler.open_url('http://www.example.com', 'example')

        # open with cache file and reset it
        data2 = crawler.open_url('http://www.example.com', 'example', reset_cache=True)

        self.assertEqual(data, data1)
        self.assertEqual(data, data2)
