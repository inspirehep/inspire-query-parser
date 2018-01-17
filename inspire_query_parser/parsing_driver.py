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

"""This module provides the public API of INSPIRE query parser."""

from __future__ import absolute_import, print_function, unicode_literals

import logging

import six

from inspire_query_parser.parser import Query
from inspire_query_parser.stateful_pypeg_parser import StatefulParser
from inspire_query_parser.utils.format_parse_tree import emit_tree_format
from inspire_query_parser.visitors.elastic_search_visitor import \
    ElasticSearchVisitor
from inspire_query_parser.visitors.restructuring_visitor import \
    RestructuringVisitor

logger = logging.getLogger(__name__)


def parse_query(query_str):
    """
    Drives the whole logic, by parsing, restructuring and finally, generating an ElasticSearch query.

    Args:
        query_str (six.text_types): the given query to be translated to an ElasticSearch query

    Returns:
        six.text_types: Return an ElasticSearch query.

    Notes:
        In case there's an error, an ElasticSearch `multi_match` query is generated with its `query` value, being the
        query_str argument.
    """
    def _generate_match_all_fields_query():
        # Strip colon character (special character for ES)
        stripped_query_str = ' '.join(query_str.replace(':', ' ').split())
        return {'multi_match': {'query': stripped_query_str, 'fields': ['_all'], 'zero_terms_query': 'all'}}

    if not isinstance(query_str, six.text_type):
        query_str = six.text_type(query_str.decode('utf-8'))

    logger.info('Parsing: "' + query_str + '\".')

    parser = StatefulParser()
    rst_visitor = RestructuringVisitor()
    es_visitor = ElasticSearchVisitor()

    try:
        unrecognized_text, parse_tree = parser.parse(query_str, Query)

        if unrecognized_text:  # Usually, should never happen.
            msg = 'Parser returned unrecognized text: "' + unrecognized_text + \
                  '" for query: "' + query_str + '".'

            if query_str == unrecognized_text and parse_tree is None:
                # Didn't recognize anything.
                logger.warn(msg)
                return _generate_match_all_fields_query()
            else:
                msg += 'Continuing with recognized parse tree.'
            logger.warn(msg)

    except SyntaxError as e:
        logger.warn('Parser syntax error (' + six.text_type(e) + ') with query: "' + query_str +
                    '". Continuing with a match_all with the given query.')
        return _generate_match_all_fields_query()

    # Try-Catch-all exceptions for visitors, so that search functionality never fails for the user.
    try:
        restructured_parse_tree = parse_tree.accept(rst_visitor)
        logger.debug('Parse tree: \n' + emit_tree_format(restructured_parse_tree))

    except Exception as e:
        logger.exception(
            RestructuringVisitor.__name__ + " crashed" + (": " + six.text_type(e) + ".") if six.text_type(e) else '.'
        )
        return _generate_match_all_fields_query()

    try:
        es_query = restructured_parse_tree.accept(es_visitor)
    except Exception as e:
        logger.exception(
            ElasticSearchVisitor.__name__ + " crashed" + (": " + six.text_type(e) + ".") if six.text_type(e) else '.'
        )
        return _generate_match_all_fields_query()

    if not es_query:
        # Case where an empty query was generated (i.e. date query with malformed date, e.g. "d < 200").
        return _generate_match_all_fields_query()

    return es_query
