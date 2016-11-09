import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from create_network import parse_reference, is_decision, parse_references, p_
import models

engine = create_engine('postgresql://echr:echr@localhost/echr', echo=False)
Session = sessionmaker(bind=engine)


class TestReferences(unittest.TestCase):

    def callback(self, x, arg):
        """
        Helper function for understanding what failed. Pass it to the function `parse_reference` as a caller.
        """
        print(x.count(), arg)
        p_(x[:20])

    def get_doc(self, doc_id):
        session = Session()
        return session.query(models.Document).filter_by(id=doc_id).first()

    def test_is_decision(self):
        self.assertTrue(is_decision('47158/10'))
        self.assertFalse(is_decision('62614/13'))

    def test_custom_errors(self):
        ref = 'Golder v. the United Kingdom, 21 January 1975, §§ 34 in fine and 35-36, Series A no. 18'

        bla = parse_reference(ref)
        self.assertEqual(bla.case_name, 'Golder v. the United Kingdom'.upper())

    def test_wrong_vs(self):
        ref = 'Hokkanen v  Finland, 23 September 1994, §§ 55-58, Series A no. 299‑A'

        doc = parse_reference(ref)
        self.assertEqual(doc.case_name, 'Hokkanen v. Finland'.upper())

    def test_empty_ref(self):
        doc = self.get_doc('001-110266')

        refs, t = parse_references(doc)
        self.assertTrue(t > 0)
        self.assertEqual(len(refs), t)

    def test_ignore_cited_above(self):
        doc = self.get_doc('001-107596')

        refs, t = parse_references(doc)
        self.assertEqual(t, 28)
        self.assertEqual(len(refs), t)

    def test_typo_calogero(self):
        ref = 'alogero Diana v. Italy, 15 November 1996, Reports 1996-V, p. 1775, § 28'

        doc = parse_reference(ref)
        self.assertTrue(doc.case_name.startswith('CALOGERO DIANA'))

    def test_typo_hartley(self):
        ref = 'Fox, Campbell and Heartley v. the United Kingdom, 30 August 1990, § 40, Series A no. 182'

        doc = parse_reference(ref)
        self.assertTrue('HARTLEY' in doc.case_name)

    def test_typo_union(self):
        ref = "Swedish Engine Drivers'Union v. Sweden, 6 February 1976, §§ 37, 39, 40, Series A no. 20"

        doc = parse_reference(ref)
        self.assertTrue('Drivers\' Union'.upper() in doc.case_name)

    def test_ref_with_pp(self):
        doc = self.get_doc('001-89410')

        refs, t = parse_references(doc)
        self.assertTrue(t > 0)
        self.assertEqual(len(refs), t)

    def test_pugliese(self):
        ref = 'Pugliese (II) judgment of 24 May 1991, Series A no 206-A'

        doc = parse_reference(ref)
        self.assertEqual(doc.case_name, 'PUGLIESE V. ITALY (NO. 2)')

    def test_sunday_times(self):
        ref = 'Sunday Times judgment of 6 November 1980, Series A no. 38, p. 16, para. 35'

        doc = parse_reference(ref)
        self.assertEqual(doc.case_name, 'THE SUNDAY TIMES V. THE UNITED KINGDOM (ARTICLE 50)')

    def test_sunday_2(self):
        ref = 'Sunday Times v. the United Kingdom (former Article 50), ' \
              'judgment of 6 November 1989, Series A no. 38, p. 9, § 15'

        doc = parse_reference(ref)
        self.assertEqual(doc.case_name, 'THE SUNDAY TIMES V. THE UNITED KINGDOM (ARTICLE 50)')

    def test_sunday_3(self):
        ref = 'Sunday Times v. the United Kingdom judgment (Article 50)' \
              ' of 6 November 1989, Series A no. 38, p. 9, § 15'

        doc = parse_reference(ref)
        self.assertEqual(doc.case_name, 'THE SUNDAY TIMES V. THE UNITED KINGDOM (ARTICLE 50)')

    def test_ref_starts_with_digit(self):
        doc = self.get_doc('001-57484')

        parse_references(doc)

    def test_name_without_country(self):
        ref = 'Ari and Others, 3 April 2007'

        doc = parse_reference(ref)
        self.assertEqual(doc.case_name, 'Ari and Others v. turkey'.upper())

    def test_wrong_case_no(self):
        ref = 'Ogur v. Turkey [GC], no. 21954/93, §§ 91-92, ECHR 1999-III'

        doc = parse_reference(ref)
        self.assertEqual(doc.case_name, 'OĞUR v. Turkey'.upper())

    def test_no_country(self):
        ref = 'Ari and Others, 3 April 2007'

        doc = parse_reference(ref)
        self.assertEqual(doc.case_name, 'Ari and Others v. Turkey'.upper())

    def test_particular_case(self):
        ref = 'X v. the United Kingdom, no. 5269/71, Yearbook, Vol. 15, pp. 564-574'

        doc = parse_reference(ref)
        self.assertEqual(doc.case_name, 'X. v. the United Kingdom'.upper())

    def test_wrong_name_redfearn(self):
        ref = 'Redfern v. the United Kingdom, no. 28482/94, 10 September 1997'

        doc = parse_reference(ref)
        self.assertEqual(doc.case_name, 'REDFEARN V. THE UNITED KINGDOM')

    def test_2_hits(self):
        ref = 'Dogan and Others v. Turkey, nos. 8803-8811/02, 8813/02 and 8815-8819/02, § 142, ECHR 2004-...(extracts)'

        doc = parse_reference(ref)
        print(doc)

    def test_invalid_reference(self):
        doc = self.get_doc('001-58128')

        refs, t = parse_references(doc)
        self.assertEqual(len(refs), t)

    def test_case_name_needed(self):
        ref = 'Aslan v. Turkey, report of the Commission of 22 May 1997'

        doc = parse_reference(ref)
        self.assertEqual(doc.case_name, 'ASLAN V. TURKEY')
