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

from __future__ import absolute_import, unicode_literals

import mock

from inspire_utils.name import generate_name_variations

from inspire_query_parser.parsing_driver import parse_query


def test_driver_with_simple_query():
    author_name = 'Ellis, John'
    name_variations = generate_name_variations(author_name)

    query_str = 'author: ' + author_name
    expected_es_query = {
        "bool": {
            "filter": {
                "bool": {
                    "should": [
                        {"term": {"authors.name_variations.specific": name_variation}}
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

    es_query = parse_query(query_str)

    assert es_query == expected_es_query


@mock.patch('inspire_query_parser.parsing_driver.StatefulParser')
def test_driver_with_nothing_recognized(mocked_parser):
    query_str = 'unrecognized query'
    expected_es_query = {
        'multi_match': {
            'query': 'unrecognized query',
            'fields': ['_all'],
            'zero_terms_query': 'all'
        }
    }

    mocked_parser.return_value.parse.return_value = ('unrecognized query', None)

    es_query = parse_query(query_str)

    assert es_query == expected_es_query


@mock.patch('inspire_query_parser.parsing_driver.StatefulParser')
def test_driver_with_syntax_error(mocked_parser):
    query_str = 'query with syntax error'
    expected_es_query = {
        'multi_match': {
            'query': 'query with syntax error',
            'fields': ['_all'],
            'zero_terms_query': 'all'
        }
    }

    mocked_parser.return_value.parse.side_effect = SyntaxError()

    es_query = parse_query(query_str)

    assert es_query == expected_es_query


@mock.patch('inspire_query_parser.parsing_driver.RestructuringVisitor')
def test_driver_with_rst_visitor_error(mocked_rst_visitor):
    query_str = 'foo'
    expected_es_query = {
        'multi_match': {
            'query': 'foo',
            'fields': ['_all'],
            'zero_terms_query': 'all'
        }
    }
    mocked_rst_visitor.return_value.visit.side_effect = Exception('Something went wrong with visit_value')
    mocked_rst_visitor.__name__ = 'MockedRestructuringVisitor'

    es_query = parse_query(query_str)

    assert es_query == expected_es_query


@mock.patch('inspire_query_parser.parsing_driver.ElasticSearchVisitor')
def test_driver_with_es_visitor_error(mocked_es_visitor):
    query_str = 'foo'
    expected_es_query = {
        'multi_match': {
            'query': 'foo',
            'fields': ['_all'],
            'zero_terms_query': 'all'
        }
    }
    mocked_es_visitor.return_value.visit.side_effect = Exception('Something went wrong with visit_value')
    mocked_es_visitor.__name__ = 'MockedElasticSearchVisitor'

    es_query = parse_query(query_str)

    assert es_query == expected_es_query
