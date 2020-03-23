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


from __future__ import print_function, unicode_literals

import mock

from inspire_query_parser import parser, parse_query
from inspire_query_parser.config import ES_MUST_QUERY, ES_SHOULD_QUERY
from inspire_query_parser.stateful_pypeg_parser import StatefulParser
from inspire_query_parser.visitors.elastic_search_visitor import ElasticSearchVisitor
from inspire_query_parser.visitors.restructuring_visitor import RestructuringVisitor


def ordered(obj):
    # See https://stackoverflow.com/a/25851972
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj


def _parse_query(query_str):
    stateful_parser = StatefulParser()
    restructuring_visitor = RestructuringVisitor()
    elastic_search_visitor = ElasticSearchVisitor()
    _, parse_tree = stateful_parser.parse(query_str, parser.Query)
    parse_tree = parse_tree.accept(restructuring_visitor)
    return parse_tree.accept(elastic_search_visitor)


def test_elastic_search_visitor_find_institution_partial_value_cer():
    query_str = 'affautocomplete:cer*'
    expected_es_query = {
        "query_string": {
            "query": "cer*",
            "analyze_wildcard": True,
            "fields": [
                "affautocomplete"
            ]
        }
    }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_author_partial_value_ellis():
    query_str = 'FIN author:\'ellis\''
    expected_es_query = \
        {
            "nested": {
                "path": "authors",
                "query": {
                    "query_string": {
                        "analyze_wildcard": True,
                        "fields": ["authors.full_name"],
                        "query": "*ellis*",
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_author_exact_value_ellis():
    query_str = 'Find author "ellis"'
    expected_es_query = \
        {
            "nested": {
                "path": "authors",
                "query": {
                    "term": {
                        "authors.full_name": "ellis"
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_spires_identifier_simple_value():
    query_str = 'irn 3665763'
    expected_es_query = \
        {
            "term": {
                "external_system_identifiers.value.raw": "SPIRES-3665763"
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_exact_author_simple_value():
    query_str = 'ea Vures, John I.'
    expected_es_query = \
        {
            "nested": {
                "path": "authors",
                "query": {
                    "term": {
                        "authors.full_name_unicode_normalized": "vures, john i."
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_exact_author_simple_value_diacritics():
    query_str = 'ea Vurës, John I'
    expected_es_query = \
        {
            "nested": {
                "path": "authors",
                "query": {
                    "term": {
                        "authors.full_name_unicode_normalized": "vur\xebs, john i."
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_exact_author_partial_value():
    query_str = "ea 'Vures, John I.'"
    expected_es_query = \
        {
            "nested": {
                "path": "authors",
                "query": {
                    "term": {
                        "authors.full_name_unicode_normalized": "vures, john i."
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_exact_author_partial_value_diacritics():
    query_str = "ea 'Vurës, John I'"
    expected_es_query = \
        {
            "nested": {
                "path": "authors",
                "query": {
                    "term": {
                        "authors.full_name_unicode_normalized": "vur\xebs, john i."
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_exact_author_exact_value():
    query_str = 'ea "Vures, John I."'
    expected_es_query = \
        {
            "nested": {
                "path": "authors",
                "query": {
                    "term": {
                        "authors.full_name_unicode_normalized": "vures, john i."
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_exact_author_exact_value_diacritics():
    query_str = 'ea "Vurës, John I"'
    expected_es_query = \
        {
            "nested": {
                "path": "authors",
                "query": {
                    "term": {
                        "authors.full_name_unicode_normalized": "vur\xebs, john i."
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_exact_author_with_bai_simple_value_ellis():
    query_str = 'ea J.Ellis.4'
    expected_es_query = \
        {
            "nested": {
                "path": "authors",
                "query": {
                    "term": {
                        "authors.ids.value.search": "j.ellis.4"
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_exact_author_with_bai_simple_lowercase():
    query_str = 'ea j.ellis.4'
    expected_es_query = \
        {
            "nested": {
                "path": "authors",
                "query": {
                    "term": {
                        "authors.ids.value.search": "j.ellis.4"
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_exact_author_with_bai_exact_value_ellis():
    query_str = 'ea "J.Ellis.4"'
    expected_es_query = \
        {
            "nested": {
                "path": "authors",
                "query": {
                    "term": {
                        "authors.ids.value.search": "j.ellis.4"
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_exact_author_with_bai_partial_value_ellis():
    query_str = "ea 'J.Ellis.4'"
    expected_es_query = \
        {
            "nested": {
                "path": "authors",
                "query": {
                    "term": {
                        "authors.ids.value.search": "j.ellis.4"
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_journal_title_simple_value():
    query_str = 'j Phys.Lett.B'
    expected_es_query = \
        {
            "nested": {
                "path": "publication_info",
                "query": {
                    "match": {"publication_info.journal_title": "Phys.Lett.B"}
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_journal_title_and_new_style_vol_simple_value():
    query_str = 'j Phys.Lett.B,351'
    expected_es_query = \
        {
            "nested": {
                "path": "publication_info",
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"publication_info.journal_title": "Phys.Lett.B"}},
                            {"match": {"publication_info.journal_volume": "351"}}
                        ]
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_journal_title_and_old_style_vol_simple_value():
    query_str = 'j Phys.Lett.,B351'
    expected_es_query = \
        {
            "nested": {
                "path": "publication_info",
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"publication_info.journal_title": "Phys.Lett.B"}},
                            {"match": {"publication_info.journal_volume": "351"}}
                        ]
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_journal_title_and_vol_and_artid_or_start_page_simple_value():
    query_str = 'j Phys.Lett.B,351,123'
    expected_es_query = \
        {
            "nested": {
                "path": "publication_info",
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "publication_info.journal_title": "Phys.Lett.B"
                                }
                            },
                            {
                                "match": {
                                    "publication_info.journal_volume": "351"
                                }
                            },
                            {
                                "bool": {
                                    "should": [
                                        {
                                            "match": {
                                                "publication_info.page_start": "123"
                                            }
                                        },
                                        {
                                            "match": {
                                                "publication_info.artid": "123"
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert ordered(generated_es_query) == ordered(expected_es_query)


def test_elastic_search_visitor_exact_journal_query_is_the_same_as_simple_value():
    simple_value_query_str = 'j Phys.Lett.B,351,123'
    exact_value_query_str = 'j "Phys.Lett.B,351,123"'

    generated_simple_value_es_query = _parse_query(simple_value_query_str)
    generated_exact_value_es_query = _parse_query(exact_value_query_str)

    assert ordered(generated_simple_value_es_query) == ordered(generated_exact_value_es_query)


def test_elastic_search_visitor_partial_journal_query_is_the_same_as_simple_value():
    simple_value_query_str = 'j Phys.Lett.B,351,123'
    partial_value_query_str = "j 'Phys.Lett.B,351,123'"

    generated_simple_value_es_query = _parse_query(simple_value_query_str)
    generated_partial_value_es_query = _parse_query(partial_value_query_str)

    assert ordered(generated_simple_value_es_query) == ordered(generated_partial_value_es_query)


def test_elastic_search_visitor_and_op_query():
    query_str = 'subject: astrophysics and title:boson'

    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "facet_inspire_categories": {
                                "query": "astrophysics",
                                "operator": "and",
                            }
                        }
                    },
                    {
                        "match": {
                            "titles.full_title": {
                                "query": "boson",
                                "operator": "and",
                            }
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_or_op_query():
    query_str = 'subject: astrophysics or title boson'
    expected_es_query = \
        {
            "bool": {
                "should": [
                    {
                        "match": {
                            "facet_inspire_categories": {
                                "query": "astrophysics",
                                "operator": "and",
                            }
                        }
                    },
                    {
                        "match": {
                            "titles.full_title": {
                                "query": "boson",
                                "operator": "and",
                            }
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_unknown_keyword_simple_value():
    query_str = 'unknown_keyword:bar'
    expected_es_query = {
        "bool": {
            "should": [
                {
                    "match": {
                        "unknown_keyword": {
                            "query": "bar",
                            "operator": "and",
                        }
                    }
                },
                {
                    "match": {
                        "_all": {
                            "query": "unknown_keyword:bar",
                            "operator": "and",
                        }
                    }
                }
            ]
        }
    }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_unknown_keyword_simple_value_maybe_texkey():
    query_str = 'smith:2009xj'
    expected_es_query = {
        "bool": {
            "should": [
                {
                    "match": {
                        "smith": {
                            "query": "2009xj",
                            "operator": "and",
                        }
                    }
                },
                {
                    "term": {
                        "texkeys.raw": {
                            "value": "smith:2009xj",
                            "boost": 2.0,
                        }
                    }
                },
                {
                    "match": {
                        "_all": {
                            "query": "smith:2009xj",
                            "operator": "and",
                        }
                    }
                }
            ]
        }
    }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_dotted_keyword_simple_value():
    query_str = 'dotted.keyword:bar'
    expected_es_query = {
        "bool": {
            "should": [
                {
                    "match": {
                        "dotted.keyword": {
                            "query": "bar",
                            "operator": "and",
                        }
                    }
                },
                {
                    "match": {
                        "_all": {
                            "query": "dotted.keyword:bar",
                            "operator": "and",
                        }
                    }
                }
            ]
        }
    }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_value_query():
    query_str = 'foo bar'
    expected_es_query = {
        "match": {
            "_all": {
                "query": "foo bar",
                "operator": "and",
            }
        }
    }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_keyword_query_and_value_query():
    query_str = 'topcite 2+ and skands'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "range": {
                            "citation_count": {
                                "gte": "2",
                            }
                        }
                    },
                    {
                        "match": {
                            "_all": {
                                "query": "skands",
                                "operator": "and",
                            }
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_keyword_query_and_partial_value_query():
    query_str = 'topcite 2+ and \'skands\''
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "range": {
                            "citation_count": {
                                "gte": "2",
                            }
                        }
                    },
                    {
                        "query_string": {
                            "analyze_wildcard": True,
                            "default_field": "_all",
                            "query": "*skands*",
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_keyword_query_and_exact_value_query():
    query_str = 'topcite 2+ and "skands"'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "range": {
                            "citation_count": {
                                "gte": "2",
                            }
                        }
                    },
                    {
                        "match_phrase": {
                            "_all": "skands",
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_range_op():
    query_str = 'd 2015->2017 and cited:1->9'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "should": [
                                {"range": {"earliest_date": {"gte": "2015||/y", "lte": "2017||/y"}}},
                                {"range": {"imprints.date": {"gte": "2015||/y", "lte": "2017||/y"}}},
                                {"range": {"preprint_date": {"gte": "2015||/y", "lte": "2017||/y"}}},
                                {"nested": {"path": "publication_info", "query": {
                                    "range": {"publication_info.year": {"gte": "2015||/y", "lte": "2017||/y"}}
                                }}},
                                {"range": {"thesis_info.date": {"gte": "2015||/y", "lte": "2017||/y"}}},
                            ]
                        }
                    },
                    {
                        "range": {
                            "citation_count": {
                                "gte": "1",
                                "lte": "9"
                            }
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_not_op():
    query_str = '-subject astrophysics'
    expected_es_query = \
        {
            "bool": {
                "must_not": [
                    {
                        "match": {
                            "facet_inspire_categories": {
                                "query": "astrophysics",
                                "operator": "and",
                            }
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_gte_and_lt_op():
    query_str = 'cited 50+ and cited < 100'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "range": {
                            "citation_count": {
                                "gte": "50",
                            }
                        }
                    },
                    {
                        "range": {
                            "citation_count": {
                                "lt": "100"
                            }
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_regex_value():
    query_str = 'author /^xi$/'
    expected_es_query = {
        "nested": {
            "path": "authors",
            "query": {
                "regexp": {
                    'authors.full_name': '^xi$'
                }
            }
        }
    }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_wildcard_support():
    query_str = 'a *alge | a \'alge*\' | a "o*aigh"'
    expected_es_query = \
        {
            "bool": {
                "should": [
                    {
                        "nested": {
                            "path": "authors",
                            "query": {
                                "query_string": {
                                    "analyze_wildcard": True,
                                    "fields": ["authors.full_name"],
                                    "query": "*alge",
                                }
                            }
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {
                                    "nested": {
                                        "path": "authors",
                                        "query": {
                                            "query_string": {
                                                "analyze_wildcard": True,
                                                "fields": ["authors.full_name"],
                                                "query": "*alge*",
                                            }
                                        }
                                    }
                                },
                                {
                                    "nested": {
                                        "path": "authors",
                                        "query": {
                                            "term": {
                                                "authors.full_name": "o*aigh"
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_empty_query():
    query_str = '   '
    expected_es_query = {"match_all": {}}

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_malformed_query():
    query_str = 't: and t: electroweak'
    expected_es_query = \
        {
            "simple_query_string": {
                "fields": ["_all"],
                "query": "t and t electroweak"
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


@mock.patch(
    'inspire_query_parser.visitors.elastic_search_visitor.DEFAULT_ES_OPERATOR_FOR_MALFORMED_QUERIES', ES_MUST_QUERY
)
def test_elastic_search_visitor_with_query_with_malformed_part_and_default_malformed_query_op_as_must():
    query_str = 'subject astrophysics and: author:'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "facet_inspire_categories": {
                                "query": "astrophysics",
                                "operator": "and"
                            }
                        }
                    },
                    {
                        "simple_query_string": {
                            "fields": ["_all"],
                            "query": "and author"
                        }
                    }
                ],
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


@mock.patch(
    'inspire_query_parser.visitors.elastic_search_visitor.DEFAULT_ES_OPERATOR_FOR_MALFORMED_QUERIES', ES_SHOULD_QUERY
)
def test_elastic_search_visitor_with_query_with_malformed_part_and_default_malformed_query_op_as_should():
    query_str = 'subject astrophysics and author'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "facet_inspire_categories": {
                                "query": "astrophysics",
                                "operator": "and"
                            }
                        }
                    }
                ],
                "should": [
                    {
                        "simple_query_string": {
                            "fields": ["_all"],
                            "query": "and author"
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_date_multi_field_and_simple_value_handles_only_year_fields():
    query_str = 'date 2000-10'
    expected_es_query = \
        {
            "bool": {
                "should": [
                    {"range": {"earliest_date": {"gte": "2000-10||/M", "lt": "2000-11||/M"}}},
                    {"range": {"imprints.date": {"gte": "2000-10||/M", "lt": "2000-11||/M"}}},
                    {"range": {"preprint_date": {"gte": "2000-10||/M", "lt": "2000-11||/M"}}},
                    {"nested": {"path": "publication_info", "query": {
                        "range": {"publication_info.year": {"gte": "2000||/y", "lt": "2001||/y"}}
                    }}},
                    {"range": {"thesis_info.date": {"gte": "2000-10||/M", "lt": "2000-11||/M"}}},
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_date_multi_field_and_simple_value_handles_rollover_year():
    query_str = 'date 2017-12'
    expected_es_query = \
        {
            "bool": {
                "should": [
                    {"range": {"earliest_date": {"gte": "2017-12||/M", "lt": "2018-01||/M"}}},
                    {"range": {"imprints.date": {"gte": "2017-12||/M", "lt": "2018-01||/M"}}},
                    {"range": {"preprint_date": {"gte": "2017-12||/M", "lt": "2018-01||/M"}}},
                    {"nested": {"path": "publication_info", "query": {
                        "range": {"publication_info.year": {"gte": "2017||/y", "lt": "2018||/y"}}
                    }}},
                    {"range": {"thesis_info.date": {"gte": "2017-12||/M", "lt": "2018-01||/M"}}},
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_date_multi_field_and_simple_value_handles_rollover_month():
    query_str = 'date 2017-10-31'
    expected_es_query = \
        {
            "bool": {
                "should": [
                    {"range": {"earliest_date": {"gte": "2017-10-31||/d", "lt": "2017-11-01||/d"}}},
                    {"range": {"imprints.date": {"gte": "2017-10-31||/d", "lt": "2017-11-01||/d"}}},
                    {"range": {"preprint_date": {"gte": "2017-10-31||/d", "lt": "2017-11-01||/d"}}},
                    {"nested": {"path": "publication_info", "query": {
                        "range": {"publication_info.year": {"gte": "2017||/y", "lt": "2018||/y"}}
                    }}},
                    {"range": {"thesis_info.date": {"gte": "2017-10-31||/d", "lt": "2017-11-01||/d"}}},
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_date_multi_field_and_wildcard_value_suffix_in_day():
    query_str = 'date 2000-10-*'
    expected_es_query = \
        {
            "bool": {
                "should": [
                    {"range": {"earliest_date": {"gte": "2000-10||/M", "lt": "2000-11||/M"}}},
                    {"range": {"imprints.date": {"gte": "2000-10||/M", "lt": "2000-11||/M"}}},
                    {"range": {"preprint_date": {"gte": "2000-10||/M", "lt": "2000-11||/M"}}},
                    {"nested": {"path": "publication_info", "query": {
                        "range": {"publication_info.year": {"gte": "2000||/y", "lt": "2001||/y"}}
                    }}},
                    {"range": {"thesis_info.date": {"gte": "2000-10||/M", "lt": "2000-11||/M"}}},
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_date_multi_field_and_wildcard_value_suffix_in_month():
    query_str = 'date 2015-*'
    expected_es_query = \
        {
            "bool": {
                "should": [
                    {"range": {"earliest_date": {"gte": "2015||/y", "lt": "2016||/y"}}},
                    {"range": {"imprints.date": {"gte": "2015||/y", "lt": "2016||/y"}}},
                    {"range": {"preprint_date": {"gte": "2015||/y", "lt": "2016||/y"}}},
                    {"nested": {"path": "publication_info", "query": {
                        "range": {"publication_info.year": {"gte": "2015||/y", "lt": "2016||/y"}}
                    }}},
                    {"range": {"thesis_info.date": {"gte": "2015||/y", "lt": "2016||/y"}}},
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_date_multi_field_and_wildcard_value_suffix_as_month_part():
    query_str = 'date 2015-1*'
    expected_es_query = \
        {
            "bool": {
                "should": [
                    {"range": {"earliest_date": {"gte": "2015||/y", "lt": "2016||/y"}}},
                    {"range": {"imprints.date": {"gte": "2015||/y", "lt": "2016||/y"}}},
                    {"range": {"preprint_date": {"gte": "2015||/y", "lt": "2016||/y"}}},
                    {"nested": {"path": "publication_info", "query": {
                        "range": {"publication_info.year": {"gte": "2015||/y", "lt": "2016||/y"}}
                    }}},
                    {"range": {"thesis_info.date": {"gte": "2015||/y", "lt": "2016||/y"}}},
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_one_query_date_multi_field_and_wildcard_infix_generates_to_all_field():
    query_str = 'date: 2017-*-12'
    expected_es_query = \
        {
            "multi_match": {
                "fields": ["_all"],
                "query": "date 2017-*-12",
                "zero_terms_query": "all",
            }
        }

    generated_es_query = parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_two_queries_date_multi_field_and_wildcard_infix_drops_date():
    query_str = 'date: 2017-*-12 and title collider'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "titles.full_title": {
                                "query": "collider",
                                "operator": "and",
                            }
                        }
                    }
                ]
            }
        }

    generated_es_query = parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_date_multi_field_and_wildcard_value_suffix_in_year_drops_date_query():
    query_str = 'date 201* and title collider'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "titles.full_title": {
                                "query": "collider",
                                "operator": "and",
                            }
                        }
                    },
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_date_multi_field_and_wildcard_value_suffix_in_month_drops_date_query():
    query_str = 'date 2000-*-01 and title collider'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "titles.full_title": {
                                "query": "collider",
                                "operator": "and",
                            }
                        }
                    },
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_date_multi_field_and_exact_match_value():
    query_str = 'date "2000-10"'
    expected_es_query = \
        {
            "bool": {
                "should": [
                    {
                        "term": {
                            "earliest_date": "2000-10"
                        }
                    },
                    {
                        "term": {
                            "imprints.date": "2000-10"
                        }
                    },
                    {
                        "term": {
                            "preprint_date": "2000-10"
                        }
                    },
                    {
                        "nested": {
                            "path": "publication_info",
                            "query": {
                                "term": {
                                    "publication_info.year": "2000"
                                }
                            }
                        }
                    },
                    {
                        "term": {
                            "thesis_info.date": "2000-10"
                        }
                    },
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_date_multi_field_and_partial_value():
    query_str = "date '2000-10'"
    expected_es_query = \
        {
            "bool": {
                "should": [
                    {"range": {"earliest_date": {"gte": "2000-10||/M", "lt": "2000-11||/M"}}},
                    {"range": {"imprints.date": {"gte": "2000-10||/M", "lt": "2000-11||/M"}}},
                    {"range": {"preprint_date": {"gte": "2000-10||/M", "lt": "2000-11||/M"}}},
                    {"nested": {"path": "publication_info", "query": {
                        "range": {"publication_info.year": {"gte": "2000||/y", "lt": "2001||/y"}}
                    }}},
                    {"range": {"thesis_info.date": {"gte": "2000-10||/M", "lt": "2000-11||/M"}}},
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_date_multi_field_and_partial_value_with_wildcard():
    query_str = 'date \'2000-10-*\''
    expected_es_query = \
        {
            "bool": {
                "should": [
                    {"range": {"earliest_date": {"gte": "2000-10||/M", "lt": "2000-11||/M"}}},
                    {"range": {"imprints.date": {"gte": "2000-10||/M", "lt": "2000-11||/M"}}},
                    {"range": {"preprint_date": {"gte": "2000-10||/M", "lt": "2000-11||/M"}}},
                    {"nested": {"path": "publication_info", "query": {
                        "range": {"publication_info.year": {"gte": "2000||/y", "lt": "2001||/y"}}
                    }}},
                    {"range": {"thesis_info.date": {"gte": "2000-10||/M", "lt": "2000-11||/M"}}},
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_date_multi_field_and_range_op():
    query_str = 'date 2000-01->2001-01'
    expected_es_query = {
        "bool": {
            "should": [
                {"range": {"earliest_date": {"gte": "2000-01||/M", "lte": "2001-01||/M"}}},
                {"range": {"imprints.date": {"gte": "2000-01||/M", "lte": "2001-01||/M"}}},
                {"range": {"preprint_date": {"gte": "2000-01||/M", "lte": "2001-01||/M"}}},
                {"nested": {"path": "publication_info", "query": {
                    "range": {"publication_info.year": {"gte": "2000||/y", "lte": "2001||/y"}}
                }}},
                {"range": {"thesis_info.date": {"gte": "2000-01||/M", "lte": "2001-01||/M"}}},
            ]
        }
    }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_date_multi_field_range_within_same_year():
    # This kind of query works fine (regarding the ``publication_info.year``), since the range operator is including
    # its bounds, otherwise we would get no records.
    query_str = 'date 2000-01->2000-04'
    expected_es_query = {
        "bool": {
            "should": [
                {"range": {"earliest_date": {"gte": "2000-01||/M", "lte": "2000-04||/M"}}},
                {"range": {"imprints.date": {"gte": "2000-01||/M", "lte": "2000-04||/M"}}},
                {"range": {"preprint_date": {"gte": "2000-01||/M", "lte": "2000-04||/M"}}},
                {"nested": {"path": "publication_info", "query": {
                    "range": {"publication_info.year": {"gte": "2000||/y", "lte": "2000||/y"}}
                }}},
                {"range": {"thesis_info.date": {"gte": "2000-01||/M", "lte": "2000-04||/M"}}},
            ]
        }
    }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_multi_match_when_es_field_is_a_list_and_gt_op():
    query_str = 'subject astrophysics and date > 2015'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "facet_inspire_categories": {
                                "query": "astrophysics",
                                "operator": "and"
                            }
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {"range": {"earliest_date": {"gt": "2015||/y"}}},
                                {"range": {"imprints.date": {"gt": "2015||/y"}}},
                                {"range": {"preprint_date": {"gt": "2015||/y"}}},
                                {"nested": {"path": "publication_info", "query": {
                                    "range": {"publication_info.year": {"gt": "2015||/y"}}
                                }}},
                                {"range": {"thesis_info.date": {"gt": "2015||/y"}}},
                            ]
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_multi_match_when_es_field_is_a_list_and_gte_op():
    query_str = 'subject astrophysics and date 2015+'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "facet_inspire_categories": {
                                "query": "astrophysics",
                                "operator": "and"
                            }
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {"range": {"earliest_date": {"gte": "2015||/y"}}},
                                {"range": {"imprints.date": {"gte": "2015||/y"}}},
                                {"range": {"preprint_date": {"gte": "2015||/y"}}},
                                {"nested": {"path": "publication_info", "query": {
                                    "range": {"publication_info.year": {"gte": "2015||/y"}}
                                }}},
                                {"range": {"thesis_info.date": {"gte": "2015||/y"}}},
                            ]
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_date_multi_field_and_lt_op():
    query_str = 'subject astrophysics and date < 2015-08'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "facet_inspire_categories": {
                                "query": "astrophysics",
                                "operator": "and",
                            }
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {"range": {"earliest_date": {"lt": "2015-08||/M"}}},
                                {"range": {"imprints.date": {"lt": "2015-08||/M"}}},
                                {"range": {"preprint_date": {"lt": "2015-08||/M"}}},
                                {"nested": {"path": "publication_info", "query": {
                                    "range": {"publication_info.year": {"lt": "2015||/y"}}
                                }}},
                                {"range": {"thesis_info.date": {"lt": "2015-08||/M"}}},
                            ]
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_date_multi_field_and_lte_op():
    query_str = 'subject astrophysics and date 2015-08-30-'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "facet_inspire_categories": {
                                "query": "astrophysics",
                                "operator": "and",
                            }
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {"range": {"earliest_date": {"lte": "2015-08-30||/d"}}},
                                {"range": {"imprints.date": {"lte": "2015-08-30||/d"}}},
                                {"range": {"preprint_date": {"lte": "2015-08-30||/d"}}},
                                {"nested": {"path": "publication_info", "query": {
                                    "range": {"publication_info.year": {"lte": "2015||/y"}}
                                }}},
                                {"range": {"thesis_info.date": {"lte": "2015-08-30||/d"}}},
                            ]
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_date_malformed_drops_boolean_query_2nd_part():
    query_str = 'subject astrophysics and date > 2015_08'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "facet_inspire_categories": {
                                "query": "astrophysics",
                                "operator": "and",
                            }
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_date_malformed_drops_boolean_query_both_parts():
    query_str = 'date > 2015_08 and date < 2016_10'
    expected_es_query = {}  # Equivalent to match_all query.

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_drops_empty_body_boolean_queries():
    query_str = 'date > 2015_08 and date < 2016_10 and subject astrophysics'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "must": [
                                {
                                    "match": {
                                        "facet_inspire_categories": {
                                            "query": "astrophysics",
                                            "operator": "and",
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_handles_bai_simple_value():
    query_str = 'a A.Einstein.1'
    expected_es_query = \
        {
            "nested": {
                "path": "authors",
                "query": {
                    "match": {
                        "authors.ids.value.search": "A.Einstein.1"
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_handles_bai_exact_value():
    query_str = 'a "A.Einstein.1"'
    expected_es_query = \
        {
            "nested": {
                "path": "authors",
                "query": {
                    "term": {
                        "authors.ids.value.raw": "A.Einstein.1"
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_handles_partial_match_value_with_bai_value_and_partial_bai_value():
    query_str = "a 'A.Einstein.1' and a 'S.Mele'"
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "nested": {
                            "path": "authors",
                            "query": {
                                "query_string": {
                                    "analyze_wildcard": True,
                                    "fields": ["authors.ids.value.search"],
                                    "query": "*A.Einstein.1*"
                                }
                            }
                        }
                    },
                    {
                        "nested": {
                            "path": "authors",
                            "query": {
                                "query_string": {
                                    "analyze_wildcard": True,
                                    "fields": ["authors.ids.value.search", "authors.full_name"],
                                    "query": "*S.Mele*"
                                }
                            }
                        }
                    },
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_handles_wildcard_simple_and_partial_bai_like_queries():
    query_str = "a S.Mele* and 'S.Mel*'"
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "nested": {
                            "path": "authors",
                            "query": {
                                "query_string": {
                                    "analyze_wildcard": True,
                                    "fields": ["authors.ids.value.search", "authors.full_name"],
                                    "query": "S.Mele*"
                                }
                            }
                        }
                    },
                    {
                        "nested": {
                            "path": "authors",
                            "query": {
                                "query_string": {
                                    "analyze_wildcard": True,
                                    "fields": ["authors.ids.value.search", "authors.full_name"],
                                    "query": "*S.Mel*"
                                }
                            }
                        }
                    },
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_queries_also_bai_field_with_wildcard_if_author_name_contains_dot_and_no_spaces():
    query_str = 'a S.Mele'
    expected_es_query = \
        {
            "nested": {
                "path": "authors",
                "query": {
                    "query_string": {
                        "analyze_wildcard": True,
                        "fields": ["authors.ids.value.search", "authors.full_name"],
                        "query": "*S.Mele*"
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_queries_does_not_query_bai_field_if_name_contains_comma_and_dot():
    query_str = 'a gava,e.'

    generated_es_query = _parse_query(query_str)
    assert ElasticSearchVisitor.AUTHORS_BAI_FIELD not in str(generated_es_query)


def test_elastic_search_visitor_queries_does_not_query_bai_field_if_name_contains_trailing_dot():
    query_str = 'a mele.'

    generated_es_query = _parse_query(query_str)
    assert ElasticSearchVisitor.AUTHORS_BAI_FIELD not in str(generated_es_query)


def test_elastic_search_visitor_queries_does_not_query_bai_field_if_name_contains_prefix_dot():
    query_str = 'a .mele'

    generated_es_query = _parse_query(query_str)
    assert ElasticSearchVisitor.AUTHORS_BAI_FIELD not in str(generated_es_query)


def test_elastic_search_visitor_does_not_query_bai_field_if_name_contains_dot_and_spaces():
    query_str = 'a S. Mele'
    bai_field = "authors.ids.value.search"

    generated_es_query = _parse_query(query_str)
    assert bai_field not in str(generated_es_query)


def test_hack_to_split_initial_and_firstname_without_a_space():
    query_str = "a D.John Smith"
    expected_query = {
        "nested": {
            "path": "authors",
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "authors.last_name": {
                                    "operator": "AND",
                                    "query": "Smith",
                                }
                            }
                        },
                        {
                            "bool": {
                                "must": [
                                    {
                                        "match": {
                                            "authors.first_name.initials": {
                                                "analyzer": "names_initials_analyzer",
                                                "operator": "AND",
                                                "query": "D",
                                            }
                                        }
                                    },
                                    {
                                        "bool": {
                                            "should": [
                                                {
                                                    "match_phrase_prefix": {
                                                        "authors.first_name": {
                                                            "analyzer": "names_analyzer",
                                                            "query": "John",
                                                        }
                                                    }
                                                },
                                                {
                                                    "match": {
                                                        "authors.first_name": {
                                                            "analyzer": "names_initials_analyzer",
                                                            "operator": "AND",
                                                            "query": "John",
                                                        }
                                                    }
                                                },
                                            ]
                                        }
                                    },
                                ]
                            }
                        },
                    ]
                }
            },
        }
    }

    generated_es_query = _parse_query(query_str)
    assert ordered(generated_es_query) == ordered(expected_query)


def test_hack_to_split_two_initials_without_a_space():
    query_str = "a D.K. Smith"
    expected_query = {
        "nested": {
            "path": "authors",
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "authors.last_name": {
                                    "operator": "AND",
                                    "query": "Smith",
                                }
                            }
                        },
                        {
                            "bool": {
                                "must": [
                                    {
                                        "match": {
                                            "authors.first_name.initials": {
                                                "analyzer": "names_initials_analyzer",
                                                "operator": "AND",
                                                "query": "D",
                                            }
                                        }
                                    },
                                    {
                                        "match": {
                                            "authors.first_name.initials": {
                                                "analyzer": "names_initials_analyzer",
                                                "operator": "AND",
                                                "query": "K",
                                            }
                                        }
                                    },
                                ]
                            }
                        },
                    ]
                }
            },
        }
    }

    generated_es_query = _parse_query(query_str)
    assert ordered(generated_es_query) == ordered(expected_query)


def test_elastic_search_visitor_author_lastname_initial():
    query_str = "a ellis, j"
    expected_query = {
        "nested": {
            "path": "authors",
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "authors.last_name": {
                                    "operator": "AND",
                                    "query": "Ellis",
                                }
                            }
                        },
                        {
                            "match": {
                                "authors.first_name.initials": {
                                    "analyzer": "names_initials_analyzer",
                                    "operator": "AND",
                                    "query": "J",
                                }
                            }
                        },
                    ]
                }
            },
        }
    }

    generated_es_query = _parse_query(query_str)
    assert ordered(generated_es_query) == ordered(expected_query)


def test_elastic_search_visitor_author_lastname_firstname():
    query_str = "a ellis, john"

    expected_query = {
        "nested": {
            "path": "authors",
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "authors.last_name": {
                                    "operator": "AND",
                                    "query": "Ellis",
                                }
                            }
                        },
                        {
                            "bool": {
                                "should": [
                                    {
                                        "match_phrase_prefix": {
                                            "authors.first_name": {
                                                "analyzer": "names_analyzer",
                                                "query": "John",
                                            }
                                        }
                                    },
                                    {
                                        "match": {
                                            "authors.first_name": {
                                                "analyzer": "names_initials_analyzer",
                                                "operator": "AND",
                                                "query": "John",
                                            }
                                        }
                                    },
                                ]
                            }
                        },
                    ]
                }
            },
        }
    }
    generated_es_query = _parse_query(query_str)
    assert ordered(generated_es_query) == ordered(expected_query)


def test_elastic_search_visitor_author_lastname_firstname_without_comma():
    query_str = "a john ellis"

    expected_query = {
        "nested": {
            "path": "authors",
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "authors.last_name": {
                                    "operator": "AND",
                                    "query": "Ellis",
                                }
                            }
                        },
                        {
                            "bool": {
                                "should": [
                                    {
                                        "match_phrase_prefix": {
                                            "authors.first_name": {
                                                "analyzer": "names_analyzer",
                                                "query": "John",
                                            }
                                        }
                                    },
                                    {
                                        "match": {
                                            "authors.first_name": {
                                                "analyzer": "names_initials_analyzer",
                                                "operator": "AND",
                                                "query": "John",
                                            }
                                        }
                                    },
                                ]
                            }
                        },
                    ]
                }
            },
        }
    }
    generated_es_query = _parse_query(query_str)
    assert ordered(generated_es_query) == ordered(expected_query)


def test_elastic_search_visitor_author_lastname_firstname_without_commas_and_initials():
    query_str = "a john k. ellis"

    expected_query = {
        "nested": {
            "path": "authors",
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "authors.last_name": {
                                    "operator": "AND",
                                    "query": "Ellis",
                                }
                            }
                        },
                        {
                            "bool": {
                                "must": [
                                    {
                                        "bool": {
                                            "should": [
                                                {
                                                    "match_phrase_prefix": {
                                                        "authors.first_name": {
                                                            "analyzer": "names_analyzer",
                                                            "query": "John",
                                                        }
                                                    }
                                                },
                                                {
                                                    "match": {
                                                        "authors.first_name": {
                                                            "analyzer": "names_initials_analyzer",
                                                            "operator": "AND",
                                                            "query": "John",
                                                        }
                                                    }
                                                },
                                            ]
                                        }
                                    },
                                    {
                                        "match": {
                                            "authors.first_name.initials": {
                                                "analyzer": "names_initials_analyzer",
                                                "operator": "AND",
                                                "query": "K.",
                                            }
                                        }
                                    },
                                ]
                            }
                        },
                    ]
                }
            },
        }
    }

    generated_es_query = _parse_query(query_str)
    assert ordered(generated_es_query) == ordered(expected_query)


def test_elastic_search_visitor_author_lastname_firstname_with_commas_and_initials():
    query_str = "a ellis, john k."

    expected_query = {
        "nested": {
            "path": "authors",
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "authors.last_name": {
                                    "operator": "AND",
                                    "query": "Ellis",
                                }
                            }
                        },
                        {
                            "bool": {
                                "must": [
                                    {
                                        "bool": {
                                            "should": [
                                                {
                                                    "match_phrase_prefix": {
                                                        "authors.first_name": {
                                                            "analyzer": "names_analyzer",
                                                            "query": "John",
                                                        }
                                                    }
                                                },
                                                {
                                                    "match": {
                                                        "authors.first_name": {
                                                            "analyzer": "names_initials_analyzer",
                                                            "operator": "AND",
                                                            "query": "John",
                                                        }
                                                    }
                                                },
                                            ]
                                        }
                                    },
                                    {
                                        "match": {
                                            "authors.first_name.initials": {
                                                "analyzer": "names_initials_analyzer",
                                                "operator": "AND",
                                                "query": "K.",
                                            }
                                        }
                                    },
                                ]
                            }
                        },
                    ]
                }
            },
        }
    }
    generated_es_query = _parse_query(query_str)
    assert ordered(generated_es_query) == ordered(expected_query)


def test_elastic_search_visitor_with_simple_title():
    query_str = 't string theory'
    expected_es_query = \
        {
            "match": {
                "titles.full_title": {
                    "query": "string theory",
                    "operator": "and"
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_word_and_symbol():
    # Symbol being the "n-body".
    query_str = 't n-body separable'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "titles.full_title": {
                                "query": "n-body separable",
                                "operator": "and"
                            }
                        }
                    },
                    {
                        "match": {
                            "titles.full_title.search": "n-body"
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_word_and_two_symbols():
    # Symbol being the "n-body".
    query_str = 't n-body two-body separable'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "titles.full_title": {
                                "query": "n-body two-body separable",
                                "operator": "and"
                            }
                        }
                    },
                    {
                        "bool": {
                            "must": [
                                {
                                    "match": {
                                        "titles.full_title.search": "n-body"
                                    }
                                },
                                {
                                    "match": {
                                        "titles.full_title.search": "two-body"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_word_and_symbol_containing_unicode_characters():
    # Symbol being the "n-body".
    query_str = 't γ-radiation separable'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "titles.full_title": {
                                "query": "γ-radiation separable",
                                "operator": "and"
                            }
                        }
                    },
                    {
                        "match": {
                            "titles.full_title.search": "γ-radiation"
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_type_code_with_known_value_mapping_and_query_document_type():
    query_str = "tc c"
    expected_es_query = \
        {
            "match": {
                "document_type": {
                    "query": "conference paper",
                    "operator": "and"
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_type_code_with_known_value_mapping_and_query_publication_type():
    query_str = "tc i"
    expected_es_query = \
        {
            "match": {
                "publication_type": {
                    "query": "introductory",
                    "operator": "and"
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_type_code_with_known_value_mapping_and_query_core():
    query_str = "tc core"
    expected_es_query = \
        {
            "match": {
                "core": True
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_type_code_with_known_value_mapping_and_query_refereed():
    query_str = "tc p"
    expected_es_query = \
        {
            "match": {
                "refereed": True
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_type_code_with_unknown_value_searches_both_document_and_publication_type_fields():
    query_str = "tc note"
    expected_es_query = \
        {
            "bool": {
                "minimum_should_match": 1,
                "should": [
                    {
                        "match": {
                            "document_type": {
                                "query": "note",
                                "operator": "and"
                            }
                        }
                    },
                    {
                        "match": {
                            "publication_type": {
                                "query": "note",
                                "operator": "and"
                            }
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_type_code_with_known_exact_value_mapping_and_query_refereed():
    query_str = 'tc "p"'
    expected_es_query = \
        {
            "match": {
                "refereed": True
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_type_code_with_known_partial_value_mapping_and_query_refereed():
    query_str = "tc 'p'"
    expected_es_query = \
        {
            "match": {
                "refereed": True
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_nested_author_fields_query():
    query_str = 'authors.affiliations.value:CERN'
    expected_es_query = \
        {
            "nested": {
                "path": "authors",
                "query": {
                    "match": {
                        "authors.affiliations.value": {
                            "operator": "and",
                            "query": "CERN"
                        }
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_nested_publication_info_fields_query():
    query_str = 'publication_info.journal_title:JHEP'
    expected_es_query = \
        {
            "nested": {
                "path": "publication_info",
                "query": {
                    "bool": {
                        "should": [
                            {
                                "match": {
                                    "publication_info.journal_title": {
                                        "operator": "and",
                                        "query": "JHEP"
                                    }
                                }
                            },
                            {
                                "match": {
                                    "_all": {
                                        "operator": "and",
                                        "query": "publication_info.journal_title:JHEP"
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_nested_refersto_recid_nested_keyword_query():
    query_str = 'refersto:recid:123456'
    expected_es_query = \
        {
            'bool': {
                'must': [
                    {
                        'match': {
                            'references.record.$ref': '123456'
                        }
                    },
                    {
                        'match': {
                            '_collections': 'Literature'
                        }
                    }
                ],
                'must_not': [
                    {
                        'match': {
                            'related_records.relation': 'successor'
                        }
                    },
                    {
                        'match': {
                            'control_number': '123456'
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_affiliation_query():
    expected_es_query = \
        {
            "nested": {
                "path": "authors",
                "query": {
                    "match": {
                        "authors.affiliations.value": {
                            "operator": "and",
                            "query": "CERN"
                        }
                    }
                }
            }
        }

    queries = ['af:CERN', 'aff:CERN', 'affil:CERN', 'affiliation:CERN']
    for query in queries:
        generated_es_query = _parse_query(query)
        assert generated_es_query == expected_es_query


def test_elastic_search_visitor_type_code_legacy_compatible_case_insensitive():
    query_str = "collection ConferencePaper"
    expected_es_query = \
        {
            'match': {
                'document_type': {
                    'query': 'conference paper', 'operator': 'and'
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_type_code_legacy_compatible_book():
    query_str = "collection book"
    expected_es_query = \
        {
            'match': {
                'document_type': {
                    'query': 'book', 'operator': 'and'
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_type_code_legacy_compatible_conference_paper():
    query_str = "collection conferencepaper"
    expected_es_query = \
        {
            'match': {
                'document_type': {
                    'query': 'conference paper', 'operator': 'and'
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_type_code_legacy_compatible_citeable():
    query_str = "collection citeable"
    expected_es_query = \
        {
            'match': {
                'citeable': True
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_type_code_legacy_compatible_introductory():
    query_str = "collection introductory"
    expected_es_query = \
        {
            'match': {
                'publication_type': {
                    'query': 'introductory', 'operator': 'and'
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_type_code_legacy_compatible_lectures():
    query_str = "collection lectures"
    expected_es_query = \
        {
            'match': {
                'publication_type': {
                    'query': 'lectures', 'operator': 'and'
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_type_code_legacy_compatible_published():
    query_str = "collection published"
    expected_es_query = \
        {
            'match': {
                'refereed': True
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_type_code_legacy_compatible_review():
    query_str = "collection review"
    expected_es_query = \
        {
            'match': {
                'publication_type': {
                    'query': 'review', 'operator': 'and'
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_type_code_legacy_compatible_thesis():
    query_str = "collection thesis"
    expected_es_query = \
        {
            'match': {
                'document_type': {
                    'query': 'thesis', 'operator': 'and'
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_type_code_legacy_compatible_proceedings():
    query_str = "collection proceedings"
    expected_es_query = \
        {
            'match': {
                'document_type': {
                    'query': 'proceedings', 'operator': 'and'
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_PDG_keyword():
    query_str = 'keyword "S044:DESIG=1"'
    expected_es_query = {
        "match_phrase": {
            "keywords.value": "S044:DESIG=1",

        }
    }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query
