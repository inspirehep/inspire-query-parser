"""
A collection of INSPIRE related keywords.

This dictionary has a twofold use.
Primarily, the parser uses its keys to generate INSPIRE related keywords (i.e. qualifiers) and secondly, the mapping it
provides is used by a visitor at a later phase to actually translate from the shortened variants to the canonical ones.
"""
INSPIRE_PARSER_KEYWORDS = {
    # Address
    'address': 'address',

    # Affiliation
    'affiliation': 'affiliation',
    'affil': 'affiliation',
    'aff': 'affiliation',
    'af': 'affiliation',
    'institution': 'affiliation',
    'inst': 'affiliation',

    # Author
    'author': 'author',
    'au': 'author',
    'a': 'author',

    # Author-Count
    'author-count': 'author-count',
    'authorcount': 'author-count',
    'ac': 'author-count',

    # Bulletin
    'bb': 'reportnumber',
    'bbn': 'reportnumber',
    'bull': 'reportnumber',
    'bulletin-bd': 'reportnumber',
    'bulletin-bd-no': 'reportnumber',
    'eprint': 'reportnumber',

    # Caption
    'caption': 'caption',

    # Citedby
    'citedby': 'citedby',

    # coden
    'bc': 'journal',
    'browse-only-indx': 'journal',
    'coden': 'journal',
    'journal-coden': 'journal',

    # Collaboration
    'collaboration': 'collaboration',
    'collab-name': 'collaboration',
    'cn': 'collaboration',

    # Collection
    'collection': 'collection',
    'tc': 'collection',
    'ty': 'collection',
    'type': 'collection',
    'type-code': 'collection',
    'scl': 'collection',
    'ps': 'collection',

    # Conference number
    'confnumber': 'confnumber',
    'conf-number': 'confnumber',
    'cnum': 'confnumber',

    # Country
    'country': 'country',
    'cc': 'country',

    # Date
    'date': 'year',
    'year': 'year',
    'd': 'year',

    # Date added
    'date-added': 'datecreated',
    'dadd': 'datecreated',
    'da': 'datecreated',

    # Date earliest
    'date-earliest': 'date-earliest',
    'de': 'date-earliest',

    # Date updated
    'date-updated': 'datemodified',
    'dupd': 'datemodified',
    'du': 'datemodified',

    # DOI
    'doi': 'doi',

    # Exact-Author
    'exact-author': 'exact-author',
    'exactauthor': 'exact-author',
    'ea': 'exact-author',

    # Experiment
    'experiment': 'experiment',
    'exp': 'experiment',

    # Field code
    'subject': 'subject',
    'f': 'subject',
    'fc': 'subject',
    'field': 'subject',
    'field-code': 'subject',

    # First-Author
    'first-author': 'first-author',
    'firstauthor': 'first-author',
    'fa': 'first-author',

    # Fulltext
    'fulltext': 'fulltext',
    'ft': 'fulltext',

    # Job related
    'job': 'title',
    'position': 'title',
    'region': 'region',
    'continent': 'region',
    'rank': 'rank',

    # Journal
    'journal': 'journal',
    'j': 'journal',
    'published_in': 'journal',
    'spicite': 'journal',
    'volume': 'journal',
    'vol': 'journal',

    # Journal year
    'journal-year': 'journal-year',
    'jy': 'journal-year',

    # Keyword
    'keyword': 'keyword',
    'k': 'keyword',
    'keywords': 'keyword',
    'kw': 'keyword',

    # Note
    'note': 'note',
    'notes': 'note',

    # Postal code
    'postalcode': 'postalcode',
    'zip': 'postalcode',

    # rawref
    'rawref': 'rawref',

    # recid
    'recid': 'recid',

    # Reference
    'reference': 'reference',
    'citation': 'reference',
    'jour-vol-page': 'reference',
    'jvp': 'reference',

    # Refersto operator
    'refersto': 'refersto',
    'refs': 'refersto',

    # Report number
    'reportnumber': 'reportnumber',
    'report-num': 'reportnumber',
    'report': 'reportnumber',
    'rept': 'reportnumber',
    'rn': 'reportnumber',
    'r': 'reportnumber',

    # Title
    'title': 'title',
    't': 'title',

    # Topcite
    'cited': 'cited',
    'topcit': 'cited',
    'topcite': 'cited',
}
