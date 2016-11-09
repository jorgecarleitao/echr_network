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
            ', NOS', ' OF ', ', 226', ', [GC]', ' [GC]']


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


def get_case(string):
    re_matches = re.findall('(\d+/\d{2})', string)
    if re_matches:
        return re_matches[0]
    else:
        return None


def get_year(string):
    try:
        re_matches = re.search(' (\d{4})([ -]|$)', string)
        return int(re_matches.groups()[0])
    except AttributeError:
        return None


def p_(docs):
    for doc in docs:
        print(doc.case, doc.tags, doc.date, doc.case_name)


def fix_custom_errors(ref):

    if ' SA ' in ref:
        ref = ref.replace(' SA ', ' S.A. ')
    if ' C.THE ' in ref:
        ref = ref.replace(' C.THE ', ' C. THE ')
    if ' 1ER ' in ref:
        ref = ref.replace(' 1ER ', ' 1 ')
    if ' 1ST ' in ref:
        ref = ref.replace(' 1ST ', ' 1 ')
    if '(FORMER ARTICLE 50)' in ref:
        ref = ref.replace('(FORMER ARTICLE 50)', '(ARTICLE 50)')
    if ' ,' in ref:
        ref = ref.replace(' ,', ',')

    if ref.startswith('GOLDER V. THE UNITED KINGDOM'):
        ref = ref.replace('JANUARY', 'FEBRUARY')

    starts_with_replace = {
        'JUDGEMENT ': '',
        'CASE OF ': '',
        'CASES OF ': '',
        ' C . ': ' V. ',
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

    scl = scl.replace(';pp', ',pp')
    scl = scl.replace(';p.', ',p.')
    scl = scl.replace(';§', ',§')
    scl = scl.replace(';no ', ',no ')
    scl = scl.replace(';ECHR ', ',ECHR ')
    scl = scl.replace(';and p. ', ',and p. ')

    return scl.split(';')


def parse_reference(ref, callback=lambda x, y: None):
    ref = ref.upper()
    # remove trailing spaces, see http://stackoverflow.com/a/2077944/931303
    ref = ' '.join(ref.split())

    ref = fix_custom_errors(ref)

    if 'SUNDAY TIMES' in ref and 'ARTICLE 50' in ref:
        return session.query(models.Document).filter_by(id='001-57583').first()

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

    date = get_date(ref)
    case = get_case(ref)

    matches = session.query(models.Document) \
        .filter(models.Document.tags.contains('ENG')) \
        .filter(~models.Document.tags.contains('FRE'))\
        .filter(~models.Document.case_name.contains('Translation'))
    old_matches = matches

    if case:
        matches = matches.filter(models.Document.case.contains(case))
        count = matches.count()
        callback(matches, case)

        if count == 1:
            return matches[0]
        elif count == 0:
            matches = old_matches
        else:
            old_matches = matches

    if date:
        matches = matches.filter_by(date=date)
        count = matches.count()
        callback(matches, date)

        if count == 1:
            return matches[0]
        elif count == 0:
            matches = old_matches
        else:
            old_matches = matches

    # pick year (before it is removed)
    year = get_year(ref)

    is_gc = False
    if '[GC]' in ref:
        is_gc = True

    for to_split in TO_SPLIT:
        if to_split in ref:
            ref = ref.split(to_split)[0]

    if ' (NO ' in ref:
        ref = ref.replace(' (NO ', ' (No. ')

    if is_gc:
        matches = matches.filter(models.Document.tags.contains('GRANDCHAMBER'))
        count = matches.count()
        callback(matches, 'GRANDCHAMBER')

        if count == 1:
            return matches[0]
        elif count == 0:
            matches = old_matches
        else:
            old_matches = matches

    # try including the year if no date is available
    if not date and year:
        matches = matches.filter(extract('year', models.Document.date) == year)
        count = matches.count()
        callback(matches, year)

        if count == 1:
            return matches[0]
        elif count == 0:
            matches = old_matches
        else:
            old_matches = matches

    if ' V ' in ref:
        ref = ref.replace(' V ', ' V. ')

    tmp = ref.split(' V. ')
    names = tmp[0]
    if len(tmp) == 1:
        names = tmp[0].split(',')[0]

    # try by names
    matches = matches.filter(models.Document.case_name.startswith(names))
    count = matches.count()
    callback(matches, names)

    if count == 1:
        return matches[0]
    elif count == 0:
        matches = old_matches
    else:
        old_matches = matches

    # try by country
    country = None
    if len(tmp) > 1:
        country = tmp[1].split(',')[0]

        matches = matches.filter(models.Document.case_name.endswith(country))
        count = matches.count()
        callback(matches, country)

        if count == 1:
            return matches[0]
        elif count == 0:
            matches = old_matches
        else:
            old_matches = matches

    # try full case name
    if country and names:
        case_name = '%s V. %s' % (names, country)

        matches = matches.filter(models.Document.case_name == case_name)
        count = matches.count()
        callback(matches, case_name)

        if count == 1:
            return matches[0]
        elif count == 0:
            matches = old_matches
        else:
            old_matches = matches

    # check if this is not a decision (it hits HUDOC so we left it as last resort)
    if case and is_decision(case):
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


def parse_all_references(caching=False):
    file_name = '_cache_refs/parsed_docs.json'

    parsed_docs = dict()

    # try to continue from previous runs
    if caching:
        try:
            with open(file_name, 'r') as fp:
                parsed_docs = json.load(fp)
        except IOError:
            pass

    # with text and in english and not fixed
    docs = session.query(models.Document) \
        .filter(~(models.Document.html == '')) \
        .filter(models.Document.tags.contains('ENG')) \
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
        with open(file_name, 'w') as fp:
            json.dump(parsed_docs, fp, indent=4, sort_keys=True)

        # update sql table for references
        doc.references[:] = []
        for ref in references:
            if ref not in doc.references:
                doc.references.append(ref)
        session.add(doc)
        session.commit()

    print(fails, total)
