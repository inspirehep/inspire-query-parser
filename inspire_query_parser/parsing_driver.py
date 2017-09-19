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

from inspire_query_parser import ast
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
    """
    def _generate_empty_query_parse_tree():
        return ast.EmptyQuery(None)

    logger.info('Parsing: "' + query_str + '\".')

    parser = StatefulParser()
    rst_visitor = RestructuringVisitor()
    es_visitor = ElasticSearchVisitor()

    try:
        unrecognized_text, parse_tree = parser.parse(query_str, Query)

        if unrecognized_text:  # Usually, should never happen.
            msg = 'Parser returned unrecognized text: "' + unrecognized_text + \
                  '" for query: "' + query_str + '". '

            if query_str == unrecognized_text and parse_tree is None:
                # Didn't recognize anything.
                msg += 'Continuing with an empty query.'
                parse_tree = _generate_empty_query_parse_tree()
            else:
                msg += 'Continuing with recognized parse tree.'

            logger.warn(msg)

    except SyntaxError:
        logger.warn('Parser syntax error with query: "' + query_str + '". Continuing with an empty query.')
        parse_tree = _generate_empty_query_parse_tree()

    restructured_parse_tree = parse_tree.accept(rst_visitor)
    logger.debug('Parse tree: \n' + emit_tree_format(restructured_parse_tree))

    es_query = restructured_parse_tree.accept(es_visitor)

    return es_query
