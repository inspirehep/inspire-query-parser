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
import re

from inspire_utils.helpers import force_list

from inspire_utils.name import generate_name_variations
from pypeg2 import whitespace

from inspire_query_parser import ast
from inspire_query_parser.config import (DEFAULT_ES_OPERATOR_FOR_MALFORMED_QUERIES,
                                         ES_MUST_QUERY)
from inspire_query_parser.visitors.visitor_impl import Visitor

logger = logging.getLogger(__name__)


class FieldVariations(object):
    search = 'search'
    raw = 'raw'


class ElasticSearchVisitor(Visitor):
    """Converts a parse tree to an ElasticSearch query.

    Notes:
        The ElasticSearch query follows the 2.4 version DSL specification.
    """

    # ##### Configuration #####
    # TODO This is a temporary solution for handling the Inspire keyword to ElasticSearch fieldname mapping, since
    # TODO Inspire mappings aren't in their own repository. Currently using the `records-hep` mapping.
    KEYWORD_TO_ES_FIELDNAME = {
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
    """Mapping from keywords to ElasticSearch fields.

    Note:
        If a keyword should query multiple fields, then it's value in the mapping should be a list. This will generate
        a ``multi_match`` query. Otherwise a ``match`` query is generated.
    """

    AUTHORS_NAME_VARIATIONS_FIELD = 'authors.name_variations'
    AUTHORS_BAI_FIELD = 'authors.ids.value'
    BAI_REGEX = re.compile(r'^((\w|-|\')+\.)+\d+$', re.UNICODE | re.IGNORECASE)
    # ################

    # #### Helpers ####
    def _generate_fieldnames_if_bai_query(self, node_value, bai_field_variation, query_bai_field_if_dots_in_name):
        """Generates new fieldnames in case of BAI query.

        Args:
            node_value (six.text_type): The node's value (i.e. author name).
            bai_field_variation (six.text_type): Which field variation to query ('search' or 'raw').
            query_bai_field_if_dots_in_name (bool): Whether to query BAI field (in addition to author's name field)
                if dots exist in the name and name contains no whitespace.

        Returns:
            list: Fieldnames to query on, in case of BAI query or None, otherwise.

        Raises:
            ValueError, if ``field_variation`` is not one of ('search', 'raw').
        """
        if bai_field_variation not in (FieldVariations.search, FieldVariations.raw):
            raise ValueError('Non supported field variation "{}".'.format(bai_field_variation))

        if ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['author'] and \
                ElasticSearchVisitor.BAI_REGEX.match(node_value):
            return [ElasticSearchVisitor.AUTHORS_BAI_FIELD + '.' + bai_field_variation]

        elif not whitespace.search(node_value) and \
                query_bai_field_if_dots_in_name and \
                ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['author'] and \
                '.' in node_value:
            # Case of partial BAI, e.g. ``J.Smith``.
            return [ElasticSearchVisitor.AUTHORS_BAI_FIELD + '.' + bai_field_variation] + \
                   force_list(ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['author'])

        else:
            return None

    def _generate_author_query(self, author_name):
        """Generates a match and a filter query handling specifically authors.

        Notes:
            The match query is generic enough to return many results. Then, using the filter clause we truncate these
            so that we imitate legacy's behaviour on return more "exact" results. E.g. Searching for `Smith, John`
            shouldn't return papers of 'Smith, Bob'.
        """
        name_variations = generate_name_variations(author_name)

        return {
            "bool": {
                "filter": {
                    "bool": {
                        "should": [
                            {"term": {ElasticSearchVisitor.AUTHORS_NAME_VARIATIONS_FIELD: name_variation}}
                            for name_variation in name_variations
                        ]
                    }
                },
                "must": {
                    "match": {
                        ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['author']: author_name
                    }
                }
            }
        }

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
    # ################

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

    def visit_nested_keyword_op(self, node):  # TODO Cannot be completed as of yet.
        raise NotImplementedError('Nested keyword queries aren\'t implemented yet.')

    def visit_keyword(self, node):
        # If no keyword is found, return the original node value (case of an unknown keyword).
        return ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME.get(node.value, node.value)

    def visit_value(self, node, fieldnames=None):
        if not fieldnames:
            fieldnames = '_all'

        if node.contains_wildcard:
            bai_fieldnames = self._generate_fieldnames_if_bai_query(
                node.value,
                bai_field_variation=FieldVariations.search,
                query_bai_field_if_dots_in_name=True
            )

            return self._generate_query_string_query(node.value,
                                                     fieldnames=bai_fieldnames or fieldnames,
                                                     analyze_wildcard=True)
        else:
            if isinstance(fieldnames, list):
                return {
                    'multi_match': {
                        'fields': fieldnames,
                        'query': node.value,
                    }
                }
            else:
                if ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['author'] == fieldnames:
                    bai_fieldnames = self._generate_fieldnames_if_bai_query(
                        node.value,
                        bai_field_variation=FieldVariations.search,
                        query_bai_field_if_dots_in_name=True
                    )
                    if bai_fieldnames:
                        if len(bai_fieldnames) == 1:
                            return {"match": {bai_fieldnames[0]: node.value}}
                        else:
                            # Not an exact BAI pattern match, but node's value looks like BAI (no spaces and dots),
                            # e.g. `S.Mele`. In this case generate a partial match query.
                            return self.visit_partial_match_value(node, bai_fieldnames)

                    return self._generate_author_query(node.value)

                return {
                    'match': {
                        fieldnames: node.value,
                    }
                }

    def visit_exact_match_value(self, node, fieldnames=None):
        """Generates a term query (exact search in ElasticSearch)."""
        if not fieldnames:
            fieldnames = ['_all']
        else:
            fieldnames = force_list(fieldnames)

        bai_fieldnames = self._generate_fieldnames_if_bai_query(
            node.value,
            bai_field_variation=FieldVariations.raw,
            query_bai_field_if_dots_in_name=False
        )

        term_queries = [{'term': {field: node.value}} for field in (bai_fieldnames or fieldnames)]
        if len(term_queries) > 1:
            return {'bool': {'should': term_queries}}
        else:
            return term_queries[0]

    def visit_partial_match_value(self, node, fieldnames=None):
        """Generates a query which looks for a substring of the node's value in the given fieldname."""
        # Add wildcard token as prefix and suffix.
        value = \
            ('' if node.value.startswith(ast.GenericValue.WILDCARD_TOKEN) else '*') + \
            node.value + \
            ('' if node.value.endswith(ast.GenericValue.WILDCARD_TOKEN) else '*')

        bai_fieldnames = self._generate_fieldnames_if_bai_query(
            node.value,
            bai_field_variation=FieldVariations.search,
            query_bai_field_if_dots_in_name=True
        )

        return self._generate_query_string_query(value,
                                                 fieldnames=bai_fieldnames or fieldnames,
                                                 analyze_wildcard=True)

    def visit_regex_value(self, node, fieldname):
        return {
            'regexp': {
                fieldname: node.value
            }
        }
