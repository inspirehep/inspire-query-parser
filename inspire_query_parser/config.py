# -*- coding: utf-8 -*-
#
# This file is part of INSPIRE.
# Copyright (C) 2014-2017 CERN.
#
# INSPIRE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INSPIRE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with INSPIRE. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""
A collection of INSPIRE related keywords.

This dictionary has a twofold use.
Primarily, the parser uses its keys to generate INSPIRE related keywords (i.e. qualifiers) and secondly, provides
a normalization of the shortened keywords to their full version.
"""
from __future__ import unicode_literals

INSPIRE_PARSER_KEYWORDS = {
    # Abstract
    'abstract': 'abstract',

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
    'name': 'author',

    # Author-Count
    'author-count': 'author-count',
    'authorcount': 'author-count',
    'ac': 'author-count',

    # Cataloguer
    'cat': 'cataloguer',

    # Caption
    'caption': 'caption',

    # Cite, i.e. records that cite the given search term
    # Cite and c: SPIRES syntax while reference is INVENIO syntax
    'cite': 'cite',
    'c': 'cite',
    'reference': 'cite',

    # Citedby related
    'citedby': 'citedby',  # nested keyword query

    # Cited by excluding self sites, e.g. citedbyexcludingselfcites:author:M.E.Peskin.1
    'citedbyexcludingselfcites': 'citedbyexcludingselfcites',
    'citedbyx': 'citedbyexcludingselfcites',

    # Cited excluding self sites, e.g. citedexcludingselfcites:50+
    'citedexcludingselfcites': 'citedexcludingselfcites',
    'cx': 'citedexcludingselfcites',

    # Collaboration
    'collaboration': 'collaboration',
    'cn': 'collaboration',

    # Conference number
    'cnum': 'confnumber',

    # Control number
    'control_number': 'control_number',
    'recid': 'control_number',

    # Country
    'country': 'country',
    'cc': 'country',

    # Date
    'date': 'date',
    'd': 'date',
    # From queries dataset, users seem to use year and date interchangeably.
    'year': 'date',

    # Date added
    'date-added': 'date-added',
    'dadd': 'date-added',
    'da': 'date-added',

    # Date earliest
    'date-earliest': 'date-earliest',
    'de': 'date-earliest',

    # Date updated
    'date-updated': 'date-updated',
    'dupd': 'date-updated',
    'du': 'date-updated',

    # DOI
    'doi': 'doi',

    # ePrint
    'bb': 'eprint',
    'bull': 'eprint',
    'eprint': 'eprint',

    # Exact-Author
    'exact-author': 'exact-author',
    'exactauthor': 'exact-author',
    'ea': 'exact-author',

    # Experiment
    'experiment': 'experiment',
    'exp': 'experiment',

    # Field-code
    'fc': 'field-code',
    'field-code': 'field-code',

    # First-Author
    'first-author': 'first-author',
    'firstauthor': 'first-author',
    'fa': 'first-author',

    # Fulltext
    'fulltext': 'fulltext',
    'ft': 'fulltext',

    # SPIRES identifiers
    'irn': 'irn',

    # Job related
    'position': 'title',
    'region': 'region',
    'continent': 'region',
    'rank': 'rank',

    # Journal related
    'coden': 'journal',
    'journal': 'journal',
    'j': 'journal',
    'published_in': 'journal',
    'volume': 'volume',
    'vol': 'volume',

    # Journal year
    'journal-year': 'journal-year',
    'jy': 'journal-year',

    # Keyword
    # keyword is Invenio style, while the rest are from SPIRES syntax.
    'keyword': 'keyword',
    'keywords': 'keyword',
    'kw': 'keyword',
    'k': 'keyword',

    # Primary archive
    'primarch': 'primarch',

    # rawref
    'rawref': 'rawref',

    # Reference
    'citation': 'reference',
    'jour-vol-page': 'reference',
    'jvp': 'reference',

    # Refersto operator
    # Nested keyword query
    'refersto': 'refersto',

    # Refers to excluding self cites, e.g. referstoexcludingselfcites:author:M.E.Peskin.1
    # Nested keyword queries
    'referstoexcludingselfcites': 'referstoexcludingselfcites',
    'referstox': 'referstoexcludingselfcites',

    # Report number
    'reportnumber': 'reportnumber',
    'report-num': 'reportnumber',
    'report': 'reportnumber',
    'rept': 'reportnumber',
    'rn': 'reportnumber',
    'r': 'reportnumber',

    # Subject
    'subject': 'subject',

    # Title
    'title': 'title',
    'ti': 'title',
    't': 'title',

    # texkey
    'texkey': 'texkeys',

    # Topcite, i.e. citation count
    # Cited used to be for Invenio style syntax while topcite for SPIRES
    'cited': 'topcite',
    'topcit': 'topcite',
    'topcite': 'topcite',

    # Type-Code
    'type-code': 'type-code',
    'type': 'type-code',
    'tc': 'type-code',
    'ty': 'type-code',
    'scl': 'type-code',
    'ps': 'type-code',
    'collection': 'type-code',  # Queries for this one include "collection published" only
}

INSPIRE_KEYWORDS_SET = set(INSPIRE_PARSER_KEYWORDS.values())

# #### Date specifiers #####
DATE_TODAY_REGEX_PATTERN = 'today'
DATE_YESTERDAY_REGEX_PATTERN = 'yesterday'
DATE_LAST_MONTH_REGEX_PATTERN = 'last\s+month'
DATE_THIS_MONTH_REGEX_PATTERN = 'this\s+month'

DATE_SPECIFIERS_COLLECTION = (
    DATE_TODAY_REGEX_PATTERN,
    DATE_YESTERDAY_REGEX_PATTERN,
    DATE_THIS_MONTH_REGEX_PATTERN,
    DATE_LAST_MONTH_REGEX_PATTERN
)
# #####

ES_MUST_QUERY = "must"
ES_SHOULD_QUERY = "should"
DEFAULT_ES_OPERATOR_FOR_MALFORMED_QUERIES = ES_MUST_QUERY
