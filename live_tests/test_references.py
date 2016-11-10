import unittest
import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from create_network import parse_reference, is_decision, parse_references, p_, get_meta, DocumentNotFoundError
import models

engine = create_engine('postgresql://echr:echr@localhost/echr', echo=False)
Session = sessionmaker(bind=engine)


class TestGetMeta(unittest.TestCase):
    """
    Tests the function create_network.get_meta, that converts a single (text) reference to a set of meta-data.
    """
    def test_1(self):
        ref = 'Golder v. the United Kingdom, 21 January 1975, §§ 34 in fine and 35-36, Series A no. 18'

        meta = get_meta(ref)

        self.assertEqual(meta['case_name'], 'Golder v. the United Kingdom'.upper())

        self.assertEqual(meta['date'], datetime.date(1975, 1, 21))
        self.assertEqual(meta['country'], 'the United Kingdom'.upper())
        self.assertEqual(meta['names'], ['GOLDER'])

    def test_no_country(self):
        ref = 'Ari and Others, 3 April 2007'
        meta = get_meta(ref)

        self.assertEqual(meta['names'], ['ARI', 'OTHERS'])
        self.assertEqual(meta['country'], None)
        self.assertEqual(meta['date'], datetime.date(2007, 4, 3))

    def test_1a(self):
        ref = 'Kressin v. Germany, no. 21061/06, 22 December 2009'
        meta = get_meta(ref)

        self.assertEqual(meta['cases'], ['21061/06'])
        self.assertEqual(meta['case_name'], 'Kressin v. Germany'.upper())
        self.assertEqual(meta['date'], datetime.date(2009, 12, 22))
        self.assertEqual(meta['country'], 'Germany'.upper())
        self.assertEqual(meta['names'], ['KRESSIN'])

    def test_2_names(self):
        ref = 'Ruiz Torija and Hiro Balani v. Spain, arrêts du 9 December 1994, ' \
              'Series A nos 303-A and 303-B, p. 12, §§ 29 and 30, and pp. 29 and 30, §§ 27 and 28'

        meta = get_meta(ref)

        self.assertEqual(meta['date'], datetime.date(1994, 12, 9))
        self.assertEqual(meta['case_name'], 'Ruiz Torija and Hiro Balani v. Spain'.upper())
        self.assertEqual(meta['country'], 'SPAIN')
        self.assertEqual(meta['names'], ['Ruiz Torija'.upper(), 'Hiro Balani'.upper()])

    def test_3_names(self):
        ref = 'Lutz, Englert and Nölkenbockhoff v. Germany, 25 August 1987, Series A no. 123'
        meta = get_meta(ref)

        self.assertEqual(meta['date'], datetime.date(1987, 8, 25))
        self.assertEqual(meta['case_name'], 'Lutz, Englert and Nölkenbockhoff v. Germany'.upper())
        self.assertEqual(meta['country'], 'GERMANY')
        self.assertEqual(meta['names'], ['LUTZ', 'Englert'.upper(), 'Nölkenbockhoff'.upper()])

    def test_many_names(self):
        ref = 'Schmautzer, Umlauft, Gradinger, Pramstaller, Palaoro and Pfarrmeier v. Austria, ' \
              'judgments of 23 October 1995, Series A nos. 328 A-C and 329 A-C'
        meta = get_meta(ref)

        self.assertEqual(meta['date'], datetime.date(1995, 10, 23))
        self.assertEqual(meta['case_name'], 'Schmautzer, Umlauft, Gradinger, Pramstaller, '
                                            'Palaoro and Pfarrmeier v. Austria'.upper())
        self.assertEqual(meta['country'], 'AUSTRIA')
        self.assertEqual(meta['names'], ['Schmautzer'.upper(),
                                         'Umlauft'.upper(),
                                         'Gradinger'.upper(),
                                         'Pramstaller'.upper(),
                                         'Palaoro'.upper(),
                                         'Pfarrmeier'.upper()])

    def test_others(self):
        ref = 'Dogan and Others v. Turkey, nos. 8803-8811/02, 8813/02 and 8815-8819/02, § 93, ECHR 2004-VI (extracts)'
        meta = get_meta(ref)

        self.assertEqual(meta['date'], None)
        self.assertEqual(meta['year'], 2004)
        self.assertEqual(meta['case_name'], 'Dogan and Others v. Turkey'.upper())
        self.assertEqual(meta['country'], 'TURKEY')
        self.assertEqual(meta['names'], ['Dogan'.upper(), 'Others'.upper()])

    def test_cant_split_of(self):
        ref = 'Jehovah’s Witnesses of Moscow v. Russia, no. 302/02, § 135, ECHR 2010-...'
        meta = get_meta(ref)

        self.assertEqual(meta['date'], None)
        self.assertEqual(meta['year'], 2010)
        self.assertEqual(meta['case_name'], 'Jehovah\'s Witnesses of Moscow v. russia'.upper())
        self.assertEqual(meta['cases'], ['302/02'])
        self.assertEqual(meta['country'], 'RUSSIA')

    def test_with_case_in_name(self):
        ref = 'Wemhoff Case, Comm. Report 01.04.66, Eur. Court H.R., Series B no. 5, pp. 89, 273-274'
        meta = get_meta(ref)

        self.assertEqual(meta['date'], None)
        self.assertEqual(meta['year'], None)
        self.assertEqual(meta['case_name'], None)
        self.assertEqual(meta['names'], ['WEMHOFF'])

    def test_get_date(self):
        ref = 'Păduraru v. Romania, no. 63252/00, § 88, ECHR 2005-XII'
        meta = get_meta(ref)

        self.assertEqual(meta['date'], None)
        self.assertEqual(meta['year'], 2005)
        self.assertEqual(meta['cases'], ['63252/00'])
        self.assertEqual(meta['case_name'], 'Păduraru v. Romania'.upper())


class TestParseReferences(unittest.TestCase):

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

    def test_year_needed(self):
        ref = 'Schüth v. Germany, no 1620/03, § 67, ECHR 2010'

        doc = parse_reference(ref)
        self.assertEqual(doc.case_name, 'SCHÜTH V. GERMANY')
        self.assertEqual(doc.date.year, 2010)

    def test_year_needed_2(self):
        ref = 'Dogan and Others v. Turkey, nos. 8803-8811/02, 8813/02 and 8815-8819/02, § 142, ECHR 2004-...(extracts)'

        doc = parse_reference(ref)
        self.assertEqual(doc.date.year, 2004)
        self.assertEqual(doc.case_name, 'DOĞAN AND OTHERS V. TURKEY')

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

    def test_invalid_reference(self):
        doc = self.get_doc('001-58128')

        refs, t = parse_references(doc)
        self.assertEqual(len(refs), t)

    def test_case_name_needed(self):
        ref = 'Aslan v. Turkey, report of the Commission of 22 May 1997'

        with self.assertRaises(DocumentNotFoundError):
            parse_reference(ref)

    def test_strange(self):
        ref = 'Valenzuela Contreras c. Spain, 30 July 1998, § 46 iii), Reports 1998-V'
        parse_reference(ref)

    def test_wemhoff_case(self):
        ref = 'Wemhoff Case, Comm. Report 01.04.66, Eur. Court H.R., Series B no. 5, pp. 89, 273-274'
        doc = parse_reference(ref)

        self.assertEqual(doc.case_name, 'WEMHOFF V. GERMANY')
        self.assertEqual(doc.date.year, 1968)

    def test_wrong_month(self):
        """
        This reference is not found by full date, but only by year because the date is wrong.
        """
        ref = 'Zanghì judgment of 19 January 1991, Series A no 194-C, p. 48, para. 26'
        doc = parse_reference(ref)

        self.assertEqual(doc.case_name, 'ZANGHÌ V. ITALY')
        self.assertEqual(doc.date.year, 1991)

    def test_with_date(self):
        ref = 'Păduraru v. Romania, no. 63252/00, § 88, ECHR 2005-XII'
        doc = parse_reference(ref)

        self.assertEqual(doc.case_name, 'PĂDURARU V. ROMANIA')
        self.assertEqual(doc.date.year, 2005)
