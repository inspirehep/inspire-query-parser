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

from inspire_utils.name import generate_name_variations

from inspire_query_parser import parser
from inspire_query_parser.config import ES_MUST_QUERY, ES_SHOULD_QUERY
from inspire_query_parser.stateful_pypeg_parser import StatefulParser
from inspire_query_parser.visitors.elastic_search_visitor import \
    ElasticSearchVisitor
from inspire_query_parser.visitors.restructuring_visitor import \
    RestructuringVisitor


def _parse_query(query_str):
    stateful_parser = StatefulParser()
    restructuring_visitor = RestructuringVisitor()
    elastic_search_visitor = ElasticSearchVisitor()
    _, parse_tree = stateful_parser.parse(query_str, parser.Query)
    parse_tree = parse_tree.accept(restructuring_visitor)
    return parse_tree.accept(elastic_search_visitor)


def test_elastic_search_visitor_find_author_partial_value_ellis():
    query_str = 'FIN author:\'ellis\''
    expected_es_query = \
        {
            "query_string": {
                "analyze_wildcard": True,
                "fields": ["authors.full_name"],
                "query": "*ellis*",
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_author_exact_value_ellis():
    query_str = 'Find author "ellis"'
    expected_es_query = \
        {
            "term": {
                "authors.full_name": "ellis"
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_author_generic_search():
    query_str = 'f author Ellis'
    expected_es_query = \
        {
            "bool": {
                "filter": {
                    "bool": {
                        "should": [
                            {"term": {ElasticSearchVisitor.AUTHORS_ALL_NAME_VARIATIONS_FIELD: 'Ellis'}}
                        ]
                    }
                },
                "must": {
                    "match": {
                        "authors.full_name": "Ellis"
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_find_author_simple_value_ellis():
    author_name = 'Ellis, John'
    name_variations = generate_name_variations(author_name)
    query_str = 'f author ' + author_name
    expected_es_query = \
        {
            "bool": {
                "filter": {
                    "bool": {
                        "should": [
                            {
                                "term": {
                                    ElasticSearchVisitor.AUTHORS_SPECIFIC_NAME_VARIATIONS_FIELD:
                                        name_variation
                                }
                            }
                            for name_variation
                            in name_variations
                        ]
                    }
                },
                "must": {
                    "match": {
                        "authors.full_name": "Ellis, John"
                    }
                }
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_and_op_query():
    author_name = 'Ellis, John'
    name_variations = generate_name_variations(author_name)
    query_str = 'author:' + author_name + ' and title:boson'

    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "filter": {
                                "bool": {
                                    "should": [
                                        {
                                            "term": {
                                                ElasticSearchVisitor.AUTHORS_SPECIFIC_NAME_VARIATIONS_FIELD:
                                                    name_variation
                                            }
                                        }
                                        for name_variation
                                        in name_variations
                                    ]
                                }
                            },
                            "must": {
                                "match": {
                                    "authors.full_name": "Ellis, John"
                                }
                            }
                        }
                    },
                    {
                        "match": {
                            "titles.full_title": "boson"
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_or_op_query():
    author_name = 'Ellis, John'
    name_variations = generate_name_variations(author_name)

    query_str = 'author:' + author_name + ' or title:boson'
    expected_es_query = \
        {
            "bool": {
                "should": [
                    {
                        "bool": {
                            "filter": {
                                "bool": {
                                    "should": [
                                        {
                                            "term": {
                                                ElasticSearchVisitor.AUTHORS_SPECIFIC_NAME_VARIATIONS_FIELD:
                                                    name_variation
                                            }
                                        }
                                        for name_variation
                                        in name_variations
                                    ]
                                }
                            },
                            "must": {
                                "match": {
                                    "authors.full_name": "Ellis, John"
                                }
                            }
                        }
                    },
                    {
                        "match": {
                            "titles.full_title": "boson"
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
        "match": {
            "unknown_keyword": "bar"
        }
    }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_dotted_keyword_simple_value():
    query_str = 'dotted.keyword:bar'
    expected_es_query = {
        "match": {
            "dotted.keyword": "bar"
        }
    }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_value_query():
    query_str = 'foo bar'
    expected_es_query = {
        "match": {
            "_all": "foo bar"
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
                            "_all": "skands"
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
                        "term": {
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
                        "range": {
                            "earliest_date": {"gte": "2015", "lte": "2017"},
                            "imprints.date": {"gte": "2015", "lte": "2017"},
                            "preprint_date": {"gte": "2015", "lte": "2017"},
                            "publication_info.year": {"gte": "2015", "lte": "2017"},
                            "thesis_info.date": {"gte": "2015", "lte": "2017"},
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
    author_name = 'Ellis, John'
    name_variations = generate_name_variations(author_name)

    query_str = '-author ' + author_name
    expected_es_query = \
        {
            "bool": {
                "must_not": [{
                    "bool": {
                        "filter": {
                            "bool": {
                                "should": [
                                    {
                                        "term": {
                                            ElasticSearchVisitor.AUTHORS_SPECIFIC_NAME_VARIATIONS_FIELD:
                                                name_variation
                                        }
                                    }
                                    for name_variation
                                    in name_variations
                                ]
                            }
                        },
                        "must": {
                            "match": {
                                "authors.full_name": "Ellis, John"
                            }
                        }
                    }
                }]
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
        "regexp": {
            'authors.full_name': '^xi$'
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
                        "query_string": {
                            "analyze_wildcard": True,
                            "fields": ["authors.full_name"],
                            "query": "*alge",
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {
                                    "query_string": {
                                        "analyze_wildcard": True,
                                        "fields": ["authors.full_name"],
                                        "query": "*alge*",
                                    }
                                },
                                {
                                    "term": {
                                        "authors.full_name": "o*aigh"
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
    query_str = 'title and foo'
    expected_es_query = \
        {
            "query_string": {
                "default_field": "_all",
                "query": "title and foo"
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


@mock.patch(
    'inspire_query_parser.visitors.elastic_search_visitor.DEFAULT_ES_OPERATOR_FOR_MALFORMED_QUERIES', ES_MUST_QUERY
)
def test_elastic_search_visitor_with_query_with_malformed_part_and_default_malformed_query_op_as_must():

    query_str = 'title γ-radiation and author'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "titles.full_title": "γ-radiation"
                        }
                    },
                    {
                        "query_string": {
                            "default_field": "_all",
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
    query_str = 'title γ-radiation and author'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "titles.full_title": "γ-radiation"
                        }
                    }
                ],
                "should": [
                    {
                        "query_string": {
                            "default_field": "_all",
                            "query": "and author"
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_multi_match_when_es_field_is_a_list_and_simple_value():
    query_str = 'date 2000-10'
    expected_es_query = \
        {
            "multi_match": {
                "fields": [
                    "earliest_date",
                    "imprints.date",
                    "preprint_date",
                    "publication_info.year",
                    "thesis_info.date",
                ],
                "query": "2000-10",
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_multi_match_when_es_field_is_a_list_and_value_has_wildcard():
    query_str = 'date 2000-10-*'
    expected_es_query = \
        {
            "query_string": {
                "analyze_wildcard": True,
                "fields": [
                    "earliest_date",
                    "imprints.date",
                    "preprint_date",
                    "publication_info.year",
                    "thesis_info.date",
                ],
                "query": "2000-10-*",
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_multi_match_when_es_field_is_a_list_and_exact_match_value():
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
                        "term": {
                            "publication_info.year": "2000-10"
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


def test_elastic_search_visitor_with_multi_match_when_es_field_is_a_list_and_partial_match_value():
    query_str = 'date \'2000-10\''
    expected_es_query = \
        {
            "query_string": {
                "analyze_wildcard": True,
                "fields": [
                    "earliest_date",
                    "imprints.date",
                    "preprint_date",
                    "publication_info.year",
                    "thesis_info.date",
                ],
                "query": "*2000-10*",
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_multi_match_when_es_field_is_a_list_and_partial_match_value_with_wildcard():
    query_str = 'date \'2000-10-*\''
    expected_es_query = \
        {
            "query_string": {
                "analyze_wildcard": True,
                "fields": [
                    "earliest_date",
                    "imprints.date",
                    "preprint_date",
                    "publication_info.year",
                    "thesis_info.date",
                ],
                "query": "*2000-10-*",
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_multi_match_when_es_field_is_a_list_and_range_value():
    query_str = 'date 2000->2005'
    expected_es_query = \
        {
            "range": {
                "earliest_date": {"gte": "2000", "lte": "2005"},
                "imprints.date": {"gte": "2000", "lte": "2005"},
                "preprint_date": {"gte": "2000", "lte": "2005"},
                "publication_info.year": {"gte": "2000", "lte": "2005"},
                "thesis_info.date": {"gte": "2000", "lte": "2005"},
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_multi_match_when_es_field_is_a_list_and_gt_op():
    query_str = 'title γ-radiation and date > 2015'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "titles.full_title": "γ-radiation"
                        }
                    },
                    {
                        "range": {
                            "earliest_date": {"gt": "2015"},
                            "imprints.date": {"gt": "2015"},
                            "preprint_date": {"gt": "2015"},
                            "publication_info.year": {"gt": "2015"},
                            "thesis_info.date": {"gt": "2015"},
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_multi_match_when_es_field_is_a_list_and_gte_op():
    query_str = 'title γ-radiation and date 2015+'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "titles.full_title": "γ-radiation"
                        }
                    },
                    {
                        "range": {
                            "earliest_date": {"gte": "2015"},
                            "imprints.date": {"gte": "2015"},
                            "preprint_date": {"gte": "2015"},
                            "publication_info.year": {"gte": "2015"},
                            "thesis_info.date": {"gte": "2015"},
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_multi_match_when_es_field_is_a_list_and_lt_op():
    query_str = 'title γ-radiation and date < 2015'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "titles.full_title": "γ-radiation"
                        }
                    },
                    {
                        "range": {
                            "earliest_date": {"lt": "2015"},
                            "imprints.date": {"lt": "2015"},
                            "preprint_date": {"lt": "2015"},
                            "publication_info.year": {"lt": "2015"},
                            "thesis_info.date": {"lt": "2015"},
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_with_multi_match_when_es_field_is_a_list_and_lte_op():
    query_str = 'title γ-radiation and date 2015-'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "titles.full_title": "γ-radiation"
                        }
                    },
                    {
                        "range": {
                            "earliest_date": {"lte": "2015"},
                            "imprints.date": {"lte": "2015"},
                            "preprint_date": {"lte": "2015"},
                            "publication_info.year": {"lte": "2015"},
                            "thesis_info.date": {"lte": "2015"},
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query
