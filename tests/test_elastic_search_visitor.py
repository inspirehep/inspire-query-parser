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

import pytest

from inspire_query_parser import parser
from inspire_query_parser.stateful_pypeg_parser import StatefulParser
from inspire_query_parser.utils.format_parse_tree import emit_tree_format
from inspire_query_parser.visitors.elastic_search_visitor import \
    ElasticSearchVisitor
from inspire_query_parser.visitors.restructuring_visitor import \
    RestructuringVisitor


def _parse_query(query_str):
    print("Parsing: " + query_str)
    stateful_parser = StatefulParser()
    restructuring_visitor = RestructuringVisitor()
    elastic_search_visitor = ElasticSearchVisitor()
    _, parse_tree = stateful_parser.parse(query_str, parser.Query)
    parse_tree = parse_tree.accept(restructuring_visitor)
    print("RST: \n" + emit_tree_format(parse_tree))
    return parse_tree.accept(elastic_search_visitor)


def test_elastic_search_visitor_find_author_partial_value_ellis():
    query_str = 'FIN author:\'ellis\''
    expected_es_query = \
        {
            "query_string": {
                "allow_leading_wildcard": True,
                "default_field": "authors.full_name",
                "query": "*ellis*"
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


def test_elastic_search_visitor_find_author_simple_value_ellis():
    query_str = 'f author ellis'
    expected_es_query = \
        {
            "match": {
                "authors.full_name": "ellis"
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_and_op_query():
    query_str = 'author:ellis and title:boson'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "match": {
                            "authors.full_name": "ellis"
                        }
                    },
                    {
                        "match": {
                            "titles.title": "boson"
                        }
                    }
                ]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_or_op_query():
    query_str = 'author:ellis or title:boson'
    expected_es_query = \
        {
            "bool": {
                "should": [
                    {
                        "match": {
                            "authors.full_name": "ellis"
                        }
                    },
                    {
                        "match": {
                            "titles.title": "boson"
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


def test_elastic_search_visitor_range_op():
    query_str = 'd 2015->2017 and cited:1->9'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "range": {
                            "earliest_date": {
                                "gte": "2015",
                                "lte": "2017"
                            }
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
    query_str = '-author ellis'
    expected_es_query = \
        {
            "bool": {
                "must_not": [{
                    "match": {
                        "authors.full_name": "ellis"
                    }
                }]
            }
        }

    generated_es_query = _parse_query(query_str)
    assert generated_es_query == expected_es_query


def test_elastic_search_visitor_gt_and_lt_op():
    query_str = 'date > 2000-10 and date < 2000-12'
    expected_es_query = \
        {
            "bool": {
                "must": [
                    {
                        "range": {
                            "earliest_date": {
                                "gt": "2000-10",
                            }
                        }
                    },
                    {
                        "range": {
                            "earliest_date": {
                                "lt": "2000-12"
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
                        "wildcard": {
                            "authors.full_name": "*alge"
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {
                                    "query_string": {
                                        "allow_leading_wildcard": True,
                                        "default_field": "authors.full_name",
                                        "query": "*alge*"
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


# TODO Cannot be completed as of yet.
# def test_elastic_search_visitor_nested_keyword_query():
#     query_str = 'referstox:author:Ellis, J'
#     expected_es_queries = [
#         {
#             "query": {
#                 "match": {
#                     "authors.full_name": "Ellis, J"
#                 }
#             }
#         },
#         {
#
#         }
#     ]
#
#     generated_es_queries = _parse_query(query_str)
#     assert len(generated_es_queries) == len(expected_es_queries) and \
#         generated_es_queries[0] == expected_es_queries[0] and \
#         generated_es_queries[1] == expected_es_queries[1]
