import re
import datetime
import json

from sqlalchemy import create_engine, extract, desc
from sqlalchemy.orm import sessionmaker
import models


month_to_number = {
    'JANUARY': 1, 'FEBRUARY': 2, 'MARCH': 3, 'APRIL': 4,
    'MAY': 5, 'JUNE': 6, 'JULY': 7, 'AUGUST': 8, 'SEPTEMBER': 9,
    'OCTOBER': 10, 'NOVEMBER': 11, 'DECEMBER': 12
}

TO_SPLIT = [', JUDGMENT', ' JUDGMENT', ', APPLICATION', ', NO.', ' NO. ', ', NOS.',
            ', NOS', ', 226', ', [GC]', ' [GC]']

TO_REPLACE = {' SA ': ' S.A. ', ' C.THE ': ' V. THE ',
              ' 1ER ': ' 1 ', ' 1ST ': ' 1 ',
              '(FORMER ARTICLE 50)': '(ARTICLE 50)',
              ' ,': ',',
              ' (NO ': ' (No. ',
              ' V ': ' V. ',
              '’': '\'',
              ' C. ': ' V. ',
              ' C . ': ' V. '}

DECISION_WORDS = ['DECISION', '(DEC.)', '(DEC)', ' DEC. ', '(DECS)', '(DECS.)']

engine = create_engine('postgresql://echr:echr@localhost/echr', echo=False)
Session = sessionmaker(bind=engine)

session = Session()


class DocumentNotFoundError(Exception):
    def __init__(self, matches):
        self.matches = matches


class InvalidReference(Exception):
    pass


def is_decision(case):
    """
    Given a case id, it checks whether it is a decision by hitting the HUDOC db.
    If it is, returns True and False otherwise.
    """
    # see crawler.META_URL
    import urllib.request
    url = 'http://hudoc.echr.coe.int/app/query/results?' \
          'query=(contentsitename=ECHR) AND (documentcollectionid2:"DECISIONS") AND (appno:"{case}")' \
          '&select=itemid&sort=&start=0&length=500'
    url = url.format(case=case).replace(' ', '%20').replace('"', '%22')

    response = urllib.request.urlopen(url)
    data = response.read()
    encoding = response.info().get_content_charset('utf-8')
    data = data.decode(encoding)
    data = json.loads(data)

    if int(data['resultcount']) > 0:
        return True

    return False


def get_date(string):
    x = string[:]
    for month in month_to_number:
        if month in x:
            x = x.replace(month, str(month_to_number[month]))

    try:
        x = tuple(map(int, re.search('(\d{1,2}) (\d{1,2}) (\d{4})', x).groups()))
        return datetime.date(x[2], x[1], x[0])
    except AttributeError:
        return None
    except:
        print("ERROR: date '%s' is invalid." % string)
        return None


def get_cases(string):
    return re.findall('(\d+/\d{2})', string)


def get_year(string):
    matches = re.findall(' (\d{4})([ \-,]|$)', string)
    if not matches:
        return None
    else:
        return int(matches[-1][0])


def p_(docs):
    for doc in docs:
        print(doc.id, doc.case, doc.tags, doc.date, doc.case_name)


def fix_custom_errors(ref):
    ref = ref.upper()
    # remove trailing spaces, see http://stackoverflow.com/a/2077944/931303
    ref = ' '.join(ref.split())

    for to_replace in TO_REPLACE:
        if to_replace in ref:
            ref = ref.replace(to_replace, TO_REPLACE[to_replace])

    starts_with_replace = {
        'JUDGEMENT ': '',
        'CASE OF ': '',
        'CASES OF ': '',
        'European Commission of Human Rights, '.upper(): '',
        'SUNDAY TIMES': 'THE SUNDAY TIMES',
        'FOX, CAMPBELL AND HEARTLEY': 'FOX, CAMPBELL AND HARTLEY',
        'ALOGERO DIANA': 'CALOGERO DIANA',
        'PUGLIESE (II)': 'PUGLIESE V. ITALY (NO. 2)',
        'TEKIN': 'TEKİN',
        'DEMIR': 'DEMİR',
        'YAGCI': 'YAĞCI',
        'Ya?c? and Sarg?n'.upper(): 'YAĞCI AND SARGIN',
        'EDITIONS PÉRISCOPE': 'ÉDITIONS PÉRISCOPE',
        'NÖLCKENBOCKHOFF': 'NÖLKENBOCKHOFF',
        'HOLY MONASTERIES': 'THE HOLY MONASTERIES',
        'LES SAINTS MONASTÈRES': 'THE HOLY MONASTERIES',
        'Holy Monasteries (The)'.upper(): 'THE HOLY MONASTERIES',
        'BASKAYA': 'BAŞKAYA',
        'SOCIALIST PARTI': 'SOCIALIST PARTY',
        'Party socialiste'.upper(): 'SOCIALIST PARTY',
        'Tre Traktörer AB'.upper(): 'TRE TRAKTÖRER AKTIEBOLAG',
        'Conka v. Belgium'.upper(): 'ČONKA V. BELGIUM',
        'KADRIYE YILDIZ': 'KADRİYE YILDIZ',
        'Swedish Engine Drivers\'Union'.upper(): 'SWEDISH ENGINE DRIVERS\' UNION',
        'Swedish Engine Drivers’ Union v. Sweden'.upper(): 'SWEDISH ENGINE DRIVERS\' UNION',
        'Swedish Engine Drivers Union'.upper(): 'SWEDISH ENGINE DRIVERS\' UNION',
        'El Bouchaïdi'.upper(): 'EL BOUJAÏDI',
        'JAN AKE': 'JAN-AKE',
        'JAN ÅKE': 'JAN-AKE',
        'JAN-ÅKE': 'JAN-AKE',
        'CAKICI': 'ÇAKICI',
        'BRIGANDI': 'BRIGANDÌ',
        'LOPEZ OSTRA': 'LÓPEZ OSTRA',
        'Bladet Tromsø'.upper(): 'BLADET TROMSO',
        'ISGRÓ': 'ISGRÒ',
        'Stran Greek Re?neries'.upper(): 'STRAN GREEK REFINERIES',
        'Znaghì'.upper(): 'ZANGHÌ',
        'Akdivar'.upper(): 'AKDİVAR',
        'Aksoy,'.upper(): 'AKSOY V. TURKEY,',
        'ÖGUR': 'OĞUR',
        'Ogur v. Turkey'.upper(): 'OĞUR V. TURKEY',
        'Valašinas v. Lithuania'.upper(): 'VALASINAS V. LITHUANIA',
        'Çiçek v. Turkey'.upper(): 'CICEK V. TURKEY',
        'Tolstoy Myloslavsky v. Grande-Bretagne'.upper(): 'TOLSTOY MILOSLAVSKY V. THE UNITED KINGDOM',
        'Macir v. Turkey'.upper(): 'MACİR V. TURKEY',
        'X v. the United Kingdom'.upper(): 'X. V. THE UNITED KINGDOM',
        'Redfern v. the United Kingdom'.upper(): 'REDFEARN V. THE UNITED KINGDOM',
        'Gentilhomme, Schaff-Benhadji and Zerouki v. France'.upper():
            'GENTILHOMME, SCHAZFF-BENHADJI AND ZEROUKI V. FRANCE',
        'Mastromattéo v. Italy'.upper(): 'MASTROMATTEO V. ITALY',
        'Górski v. Poland'.upper(): 'GORSKI V. POLAND',
        'Z. and Others v. the United Kingdom'.upper(): 'Z AND OTHERS V. THE UNITED KINGDOM',
        'Gnahoré v. France'.upper(): 'GNAHORE V. FRANCE',
        'Ciricosta et Viola v. Italy'.upper(): 'CIRICOSTA AND VIOLA V. ITALY',
        '21 February 984'.upper(): '21 February 1984',
        'Hakansson and Sturesson'.upper(): 'HÅKANSSON AND STURESSON V. SWEDEN',
        'B. v. France'.upper(): 'BELDJOUDI V. FRANCE',
        'Boden v. Sweden'.upper(): 'BODÉN V. SWEDEN',
        'Yasa v. Turkey'.upper(): 'YAŞA V. TURKEY',
        'Ringeisen case'.upper(): 'RINGEISEN V. AUSTRIA',
        'Stögmüller case'.upper(): 'STÖGMÜLLER V. AUSTRIA',
        'Neumeister case'.upper(): 'NEUMEISTER v. AUSTRIA',
        'Tre Traktorer AB'.upper(): 'TRE TRAKTÖRER AKTIEBOLAG V. SWEDEN',
        'Köning v. Germany'.upper(): 'KÖNIG V. GERMANY',
        'Ergi v. Turkey'.upper(): 'ERGİ V. TURKEY',
        'RUIZ MATEOS': 'RUIZ-MATEOS',
        'Valašinas v. Lithuania'.upper(): 'VALASINAS V. LITHUANIA',
    }

    for string in starts_with_replace:
        if ref.startswith(string):
            ref = ref.replace(string, starts_with_replace[string])
            break

    if ref.startswith('OĞUR V. TURKEY'):
        ref = ref.replace('21954/93', '21594/93')

    return ref


def get_references(scl):
    if not scl:
        return []

    # in doc 001-71465 there are no refs in scl.
    if scl.startswith('Violation de l\'art. 6-1'):
        return []
    elif scl.startswith('§§') and ';' not in scl:
        return []

    scl = scl.replace(';,', ',,')
    scl = scl.replace(';pp', ',pp')
    scl = scl.replace(';p.', ',p.')
    scl = scl.replace(';§', ',§')
    scl = scl.replace(';no ', ',no ')
    scl = scl.replace(';ECHR ', ',ECHR ')
    scl = scl.replace(';and p. ', ',and p. ')

    return scl.split(';')


def get_meta(ref):
    meta = {'date': None,
            'cases': None,
            'case_name': None,
            'country': None,
            'names': None,
            'year': None,
            'is_gc': None,
            'doc_id': None,
            }

    ref = ref.upper()
    # remove trailing spaces, see http://stackoverflow.com/a/2077944/931303
    ref = ' '.join(ref.split())

    ref = fix_custom_errors(ref)

    if ref in ('\n', '', ' '):
        raise InvalidReference
    elif 'CITED ABOVE' in ref:
        raise InvalidReference
    elif ref[:1].isdigit():
        raise InvalidReference
    elif ref.startswith('OVEMBER 1996') or ref.startswith('UDGMENT OF') or ref.startswith('f 24 April 1998'):
        raise InvalidReference

    # ignore refs to decisions
    if any(word in ref for word in DECISION_WORDS):
        raise InvalidReference

    if 'SUNDAY TIMES' in ref and 'ARTICLE 50' in ref:
        meta['doc_id'] = '001-57583'
        return meta  # short circuit because id uniquely identifies it.

    meta['date'] = get_date(ref)
    meta['cases'] = get_cases(ref)
    meta['year'] = get_year(ref)

    if '[GC]' in ref:
        meta['is_gc'] = True

    first_part = ref
    for to_split in TO_SPLIT:
        if to_split in first_part:
            first_part = first_part.split(to_split)[0]

    parts = first_part.split(' V. ')
    names = parts[0]
    if len(parts) == 2:
        country = parts[1].split(',')[0]
        meta['case_name'] = '%s V. %s' % (names, country)
        meta['names'] = re.split(', | AND ', names)
        meta['country'] = country
    if len(parts) == 1:
        meta['names'] = re.split(', | AND ', names.split(',')[0])

        # if it is of the form "X case", remove " case"
        if len(meta['names']) == 1 and meta['names'][0].endswith(' CASE'):
            meta['names'][0] = meta['names'][0].replace(' CASE', '')

    # if get_year failed to find it for some reason.
    if meta['year'] is None and meta['date']:
        meta['year'] = meta['date'].year

    return meta


def build_and(attr, cases):
    x = attr.contains(cases[0])
    for case in cases[1:]:
        x &= attr.contains(case)
    return x


def parse_reference(ref, callback=lambda x, y: None):
    meta = get_meta(ref)

    trials = [
        ('doc_id', lambda x: models.Document.id == x),
        ('cases', lambda x: build_and(models.Document.case, x)),
        ('case_name', lambda x: models.Document.case_name == x),
        ('names', lambda x: build_and(models.Document.case_name, x)),
        ('country', lambda x: models.Document.case_name.contains(x)),
        ('date', lambda x: models.Document.date == x),
        ('year', lambda x: extract('year', models.Document.date) == x)
    ]

    matches = session.query(models.Document) \
        .filter(models.Document.tags.contains('ENG')) \
        .filter(~models.Document.tags.contains('FRE'))\
        .filter(~models.Document.case_name.contains('Translation'))
    old_matches = matches

    if meta['is_gc']:
        matches = matches.filter(models.Document.tags.contains('GRANDCHAMBER'))
        callback(matches, 'GRANDCHAMBER')
        old_matches = matches

    for attr, condition in trials:
        if meta[attr]:
            matches = matches.filter(condition(meta[attr]))
            count = matches.count()
            callback(matches, meta[attr])

            if count == 1:
                return matches[0]
            elif count == 0:
                matches = old_matches
            else:
                old_matches = matches

    # check if this is not a decision (because it hits HUDOC, we left it here at the end)
    if meta['cases'] and any(map(is_decision, meta['cases'])):
        raise InvalidReference

    raise DocumentNotFoundError(matches.all())


def parse_references(doc):
    refs = get_references(doc.scl)

    total = 0
    references = []
    for ref_string in refs:
        try:
            ref = parse_reference(ref_string)
            references.append(ref)
            total += 1
        except DocumentNotFoundError as e:
            total += 1
            print('FAILED: %s' % doc.id)
            print(ref_string)
            p_(e.matches[:20])
        except InvalidReference:
            pass

    return references, total


def parse_all_references(use_json=False, populate_json=False, populate_db=False):
    file_name = '_temp_network.json'

    parsed_docs = dict()

    # try to continue from previous runs
    if use_json:
        try:
            with open(file_name, 'r') as fp:
                parsed_docs = json.load(fp)
        except IOError:
            pass

    # judgements with text, in english and not parsed
    docs = session.query(models.Document) \
        .filter(~(models.Document.html == '')) \
        .filter(models.Document.tags.contains('ENG')) \
        .filter(models.Document.tags.contains('JUDGMENTS')) \
        .order_by(desc('date')) \
        .filter(~models.Document.id.in_(list(parsed_docs.keys())))

    total = 0
    fails = 0
    for doc in docs:
        references, t = parse_references(doc)

        total += t
        fails += t - len(references)

        if len(references) != t:
            print(fails, total)

        # list(set(...)) to remove duplicates
        parsed_docs[doc.id] = list(set([ref.id for ref in references]))

        # save in json
        if populate_json:
            with open(file_name, 'w') as fp:
                json.dump(parsed_docs, fp, indent=4, sort_keys=True)

        # update sql table for references
        if populate_db:
            doc.references[:] = []
            for ref in references:
                if ref not in doc.references:
                    doc.references.append(ref)
            session.add(doc)
            session.commit()

    print(fails, total)
