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
This module encapsulates the ElasticSearch visitor logic, that receives the output of the parser and restructuring
visitor and converts it to an ElasticSearch query.
"""

from __future__ import absolute_import, unicode_literals

import logging

from inspire_utils.helpers import force_list

from inspire_query_parser import ast
from inspire_query_parser.config import (DEFAULT_ES_OPERATOR_FOR_MALFORMED_QUERIES,
                                         ES_MUST_QUERY)
from inspire_query_parser.visitors.visitor_impl import Visitor

logger = logging.getLogger(__name__)


class ElasticSearchVisitor(Visitor):
    """Converts a parse tree to an ElasticSearch query.

    Notes:
        The ElasticSearch query follows the 2.4 version DSL specification.
    """
    def _generate_query_string_query(self, value, fieldnames, analyze_wildcard):
        if not fieldnames:
            field_specifier, field_specifier_value = 'default_field', '_all'
        else:
            field_specifier = 'fields'
            field_specifier_value = fieldnames if isinstance(fieldnames, list) else [fieldnames]

        query = {
            'query_string': {
                'query': value,
                field_specifier: field_specifier_value,
            }
        }
        if analyze_wildcard:
            query['query_string']['analyze_wildcard'] = True

        return query

    def _generate_boolean_query(self, node):
        """Helper for generating a boolean query."""
        condition_a = node.left.accept(self)
        condition_b = node.right.accept(self)

        return \
            {
                'bool': {
                    ('must' if isinstance(node, ast.AndOp) else 'should'): [
                        condition_a,
                        condition_b
                    ]
                }
            }

    def _generate_range_queries(self, fieldnames, operator_value_pairs):
        """Generates ElasticSearch range query.

        Args:
            fieldnames (list): The fieldnames on which the search is the range query is targeted on,
            operator_value_pairs (dict): Contains (range_operator, value) pairs.
                The range_operator should be one of those supported by ElasticSearch (e.g. 'gt', 'lt', 'ge', 'le').
                The value should be of type int or string.

        Notes:
            If the value type is not compatible, a warning is logged and the value is converted to string.
        """
        return {
            'range': {
                fieldname: operator_value_pairs for fieldname in fieldnames
            }
        }

    def visit_empty_query(self, node):
        return {'match_all': {}}

    def visit_value_query(self, node):
        return {
            'match': {
                "_all": node.op.value
            }
        }

    def visit_malformed_query(self, node):
        return {
            'query_string': {
                'default_field': '_all',
                'query': ' '.join(node.children)
            }
        }

    def visit_query_with_malformed_part(self, node):
        query = {
                'bool': {
                    'must': [
                        node.left.accept(self),
                    ],
                }
            }

        if DEFAULT_ES_OPERATOR_FOR_MALFORMED_QUERIES == ES_MUST_QUERY:
            query['bool']['must'].append(node.right.accept(self))
        else:
            query['bool']['should'] = [node.right.accept(self)]

        return query

    def visit_not_op(self, node):
        return {
            'bool': {
                'must_not': [node.op.accept(self)]
            }
        }

    def visit_and_op(self, node):
        return self._generate_boolean_query(node)

    def visit_or_op(self, node):
        return self._generate_boolean_query(node)

    def visit_keyword_op(self, node):
        # For this visitor, the decision on which type of ElasticSearch query to generate, relies mainly on the leaves.
        # Thus, the fieldname is propagated to them, so that they generate query type, depending on their type.
        fieldname = node.left.accept(self)
        return node.right.accept(self, fieldname)

    def visit_range_op(self, node, fieldnames):
        return self._generate_range_queries(force_list(fieldnames), {'gte': node.left.value, 'lte': node.right.value})

    def visit_greater_than_op(self, node, fieldnames):
        return self._generate_range_queries(force_list(fieldnames), {'gt': node.op.value})

    def visit_greater_equal_than_op(self, node, fieldnames):
        return self._generate_range_queries(force_list(fieldnames), {'gte': node.op.value})

    def visit_less_than_op(self, node, fieldnames):
        return self._generate_range_queries(force_list(fieldnames), {'lt': node.op.value})

    def visit_less_equal_than_op(self, node, fieldnames):
        return self._generate_range_queries(force_list(fieldnames), {'lte': node.op.value})

    # TODO Cannot be completed as of yet.
    def visit_nested_keyword_op(self, node):
        raise NotImplementedError('Nested keyword queries aren\'t implemented yet.')

    def visit_keyword(self, node):
        # TODO This is a temporary solution for handling the Inspire keyword to ElasticSearch fieldname mapping, since
        # TODO Inspire mappings aren't in their own repository. Currently using the `records-hep` mapping.

        keyword_to_fieldname = {
            'author': 'authors.full_name',
            'author-count': 'author_count',
            'citedby': 'citedby',
            'collaboration': 'collaborations.value',
            'date': [
                'earliest_date',
                'imprints.date',
                'preprint_date',
                'publication_info.year',
                'thesis_info.date',
            ],
            'doi': 'dois.value.raw',
            'eprint': 'arxiv_eprints.value.raw',
            'refersto': 'references.recid',
            'reportnumber': 'report_numbers.value.fuzzy',
            'subject': 'facet_inspire_categories',
            'title': 'titles.full_title',
            'type-code': 'document_type',
            'topcite': 'citation_count',
        }

        # If no keyword is found, return the original node value (case of an unknown keyword).
        return keyword_to_fieldname.get(node.value, node.value)

    def visit_value(self, node, fieldnames=None):
        if not fieldnames:
            fieldnames = '_all'

        if node.contains_wildcard:
            return self._generate_query_string_query(node.value, fieldnames, True)
        else:
            if isinstance(fieldnames, list):
                return {
                    'multi_match': {
                        'fields': fieldnames,
                        'query': node.value,
                    }
                }
            else:
                return {
                    'match': {
                        fieldnames: node.value,
                    }
                }

    def visit_exact_match_value(self, node, fieldnames=None):
        """Generates a term query (exact search in ElasticSearch)."""
        if not fieldnames:
            fieldnames = '_all'

        if isinstance(fieldnames, list):
            return {
                'bool': {
                    'should': [{'term': {field: node.value}} for field in fieldnames]
                }
            }
        else:
            return {
                'term': {
                    fieldnames: node.value,
                }
            }

    def visit_partial_match_value(self, node, fieldnames=None):
        """Generates a query which looks for a substring of the node's value in the given fieldname."""
        # Add wildcard token as prefix and suffix.
        value = ('' if node.value.startswith(ast.GenericValue.WILDCARD_TOKEN) else '*') + \
            node.value + \
            ('' if node.value.endswith(ast.GenericValue.WILDCARD_TOKEN) else '*')

        return self._generate_query_string_query(value, fieldnames, True)

    def visit_regex_value(self, node, fieldname):
        return {
            'regexp': {
                fieldname: node.value
            }
        }
