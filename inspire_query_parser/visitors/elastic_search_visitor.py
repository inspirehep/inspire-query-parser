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

from itertools import product
import logging
from pypeg2 import whitespace
import re
import six
from unicodedata import normalize

from inspire_utils.helpers import force_list
from inspire_utils.name import normalize_name

from inspire_query_parser import ast
from inspire_query_parser.config import (
    DEFAULT_ES_OPERATOR_FOR_MALFORMED_QUERIES,
    ES_MUST_QUERY,
)
from inspire_query_parser.utils.visitor_utils import (
    ES_RANGE_EQ_OPERATOR,
    _truncate_date_value_according_on_date_field,
    _truncate_wildcard_from_date,
    author_name_contains_fullnames,
    generate_minimal_name_variations,
    update_date_value_in_operator_value_pairs_for_fieldname,
)
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
        'irn': 'external_system_identifiers.value.raw',
        'exact-author': 'authors.full_name_unicode_normalized',
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
    TYPECODE_VALUE_TO_FIELD_AND_VALUE_PAIRS_MAPPING = {
        'b': ('document_type', 'book'),
        'c': ('document_type', 'conference paper'),
        'core': ('core', True),
        'i': ('publication_type', 'introductory'),
        'l': ('publication_type', 'lectures'),
        'p': ('refereed', True),
        'r': ('publication_type', 'review'),
        't': ('document_type', 'thesis'),
    }
    """Mapping from type-code query values to field and value pairs.

    Note:
        These are going to be used for querying (instead of the given value).
    """

    AUTHORS_NAME_VARIATIONS_FIELD = 'authors.name_variations'
    AUTHORS_BAI_FIELD = 'authors.ids.value'
    BAI_REGEX = re.compile(r'^((\w|-|\')+\.)+\d+$', re.UNICODE | re.IGNORECASE)

    TITLE_SYMBOL_INDICATING_CHARACTER = ['-', '(', ')']
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

        normalized_author_name = normalize_name(node_value).strip('.')

        if ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['author'] and \
                ElasticSearchVisitor.BAI_REGEX.match(node_value):
            return [ElasticSearchVisitor.AUTHORS_BAI_FIELD + '.' + bai_field_variation]

        elif not whitespace.search(normalized_author_name) and \
                query_bai_field_if_dots_in_name and \
                ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['author'] and \
                '.' in normalized_author_name:
            # Case of partial BAI, e.g. ``J.Smith``.
            return [ElasticSearchVisitor.AUTHORS_BAI_FIELD + '.' + bai_field_variation] + \
                   force_list(ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['author'])

        else:
            return None

    def _generate_author_query(self, author_name):
        """Generates a query handling specifically authors.

        Notes:
            The match query is generic enough to return many results. Then, using the filter clause we truncate these
            so that we imitate legacy's behaviour on returning more "exact" results. E.g. Searching for `Smith, John`
            shouldn't return papers of 'Smith, Bob'.

            Additionally, doing a ``match`` with ``"operator": "and"`` in order to be even more exact in our search, by
            requiring that ``full_name`` field contains both
        """
        name_variations = [name_variation.lower()
                           for name_variation
                           in generate_minimal_name_variations(author_name)]

        # When the query contains sufficient data, i.e. full names, e.g. ``Mele, Salvatore`` (and not ``Mele, S`` or
        # ``Mele``) we can improve our filtering in order to filter out results containing records with authors that
        # have the same non lastnames prefix, e.g. 'Mele, Samuele'.
        if author_name_contains_fullnames(author_name):
            specialized_author_filter = [
                {
                    'bool': {
                        'must': [
                            {
                                'term': {ElasticSearchVisitor.AUTHORS_NAME_VARIATIONS_FIELD: names_variation[0]}
                            },
                            {
                                'match': {
                                    ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['author']: {
                                        'query': names_variation[1],
                                        'operator': 'and'
                                    }
                                }
                            }
                        ]
                    }
                } for names_variation
                in product(name_variations, name_variations)
            ]

        else:
            # In the case of initials or even single lastname search, filter with only the name variations.
            specialized_author_filter = [
                {'term': {ElasticSearchVisitor.AUTHORS_NAME_VARIATIONS_FIELD: name_variation}}
                for name_variation in name_variations
            ]

        return {
            'bool': {
                'filter': {
                    'bool': {
                        'should': specialized_author_filter
                    }
                },
                'must': {
                    'match': {
                        ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['author']: author_name
                    }
                }
            }
        }

    def _generate_exact_author_query(self, author_name_or_bai):
        """Generates a term query handling authors and BAIs.

        Notes:
            If given value is a BAI, search for the provided value in the raw field variation of
            `ElasticSearchVisitor.AUTHORS_BAI_FIELD`.
            Otherwise, the value will be procesed in the same way as the indexed value (i.e. lowercased and normalized
            (inspire_utils.normalize_name and then NFKC normalization).
            E.g. Searching for 'Smith, J.' is the same as searching for: 'Smith, J', 'smith, j.', 'smith j', 'j smith',
            'j. smith', 'J Smith', 'J. Smith'.
        """
        if ElasticSearchVisitor.BAI_REGEX.match(author_name_or_bai):
            return self._generate_term_query(
                '.'.join((ElasticSearchVisitor.AUTHORS_BAI_FIELD, FieldVariations.raw)),
                author_name_or_bai
            )
        else:
            author_name = normalize('NFKC', normalize_name(author_name_or_bai)).lower()
            return self._generate_term_query(
                ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['exact-author'],
                author_name
            )

    def _generate_date_with_wildcard_query(self, date_value):
        """Helper for generating a date keyword query containing a wildcard.

        Returns:
            (dict): The date query containing the wildcard or an empty dict in case the date value is malformed.

        The policy followed here is quite conservative on what it accepts as valid input. Look into
        :meth:`inspire_query_parser.utils.visitor_utils._truncate_wildcard_from_date` for more information.
        """
        if date_value.endswith(ast.GenericValue.WILDCARD_TOKEN):
            try:
                date_value = _truncate_wildcard_from_date(date_value)
            except ValueError:
                # Drop date query.
                return {}

            return self._generate_range_queries(self.KEYWORD_TO_ES_FIELDNAME['date'],
                                                {ES_RANGE_EQ_OPERATOR: date_value})
        else:
            # Drop date query with wildcard not as suffix, e.g. 2000-1*-31
            return {}

    @staticmethod
    def _generate_queries_for_title_symbols(title_field, query_value):
        """Generate queries for any symbols in the title against the whitespace tokenized field of titles.

        Returns:
            (dict): The query or queries for the whitespace tokenized field of titles. If none such tokens exist, then
                    returns None.
        Notes:
            Splits the value stream into tokens according to whitespace.
            Heuristically identifies the ones that contain symbol-indicating-characters (examples of those tokens are
            "g-2", "SU(2)").
        """
        values_tokenized_by_whitespace = query_value.split()

        symbol_queries = []
        for value in values_tokenized_by_whitespace:
            # Heuristic: If there's a symbol-indicating-character in the value, it signifies terms that should be
            # queried against the whitespace-tokenized title.
            if any(character in value for character in ElasticSearchVisitor.TITLE_SYMBOL_INDICATING_CHARACTER):
                symbol_queries.append({
                    "match": {
                        '.'.join([title_field, FieldVariations.search]): value
                    }
                })

        if symbol_queries:
            if len(symbol_queries) == 1:
                return symbol_queries[0]
            return {'bool': {'must': symbol_queries}}

    def _generate_title_queries(self, value):
        title_field = ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['title']
        q = {
            "match": {
                title_field: {
                    "query": value,
                    "operator": "and"
                }
            }
        }

        symbol_queries = ElasticSearchVisitor._generate_queries_for_title_symbols(title_field, value)
        if symbol_queries:
            q = {
                'bool': {
                    'must': [q, symbol_queries]
                }
            }
        return q

    def _generate_type_code_query(self, value):
        """Generate type-code queries.

        Notes:
            If the value of the type-code query exists in `TYPECODE_VALUE_TO_FIELD_AND_VALUE_PAIRS_MAPPING, then we
            query the specified field, along with the given value according to the mapping.
            See: https://github.com/inspirehep/inspire-query-parser/issues/79
            Otherwise, we query both ``document_type`` and ``publication_info``.
        """
        mapping_for_value = self.TYPECODE_VALUE_TO_FIELD_AND_VALUE_PAIRS_MAPPING.get(value, None)

        if mapping_for_value:
            return self._generate_match_query(*mapping_for_value)
        else:
            return {
                'bool': {
                    'minimum_should_match': 1,
                    'should': [
                        {
                            'match': {
                                'document_type': {
                                    'query': value,
                                    'operator': 'and'
                                }
                            }
                        },
                        {
                            'match': {
                                'publication_type': {
                                    'query': value,
                                    'operator': 'and'
                                }
                            }
                        }
                    ]
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

    def _generate_match_query(self, fieldname, value):
        if isinstance(value, bool):
            return {'match': {fieldname: value}}

        return {
            'match': {
                fieldname: {
                    'query': value,
                    'operator': 'and'
                }
            }
        }

    def _generate_term_query(self, fieldname, value):
        return {
            'term': {
                fieldname: value
            }
        }

    def _generate_boolean_query(self, node):
        condition_a = node.left.accept(self)
        condition_b = node.right.accept(self)

        bool_body = [condition for condition in [condition_a, condition_b] if condition]
        if not bool_body:
            return {}
        return \
            {
                'bool': {
                    ('must' if isinstance(node, ast.AndOp) else 'should'): bool_body
                }
            }

    def _generate_range_queries(self, fieldnames, operator_value_pairs):
        """Generates ElasticSearch range queries.

        Args:
            fieldnames (list): The fieldnames on which the search is the range query is targeted on,
            operator_value_pairs (dict): Contains (range_operator, value) pairs.
                The range_operator should be one of those supported by ElasticSearch (e.g. 'gt', 'lt', 'ge', 'le').
                The value should be of type int or string.

        Notes:
            A bool should query with multiple range sub-queries is generated so that even if one of the multiple fields
            is missing from a document, ElasticSearch will be able to match some records.

            In the case of a 'date' keyword query, it updates date values after normalizing them by using
            :meth:`inspire_query_parser.utils.visitor_utils.update_date_value_in_operator_value_pairs_for_fieldname`.
            Additionally, in the aforementioned case, if a malformed date has been given, then the the method will
            return an empty dictionary.
        """
        if ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['date'] == fieldnames:
            range_queries = []
            for fieldname in fieldnames:
                updated_operator_value_pairs = \
                    update_date_value_in_operator_value_pairs_for_fieldname(fieldname, operator_value_pairs)

                if not updated_operator_value_pairs:
                    break  # Malformed date
                else:
                    range_queries.append({
                        'range': {
                            fieldname: updated_operator_value_pairs
                        }
                    })
        else:
            range_queries = [{
                    'range': {
                        fieldname: operator_value_pairs
                    }
                }
                for fieldname in fieldnames
            ]

        if len(range_queries) == 0:
            return {}
        if len(range_queries) == 1:
            return range_queries[0]

        return {'bool': {'should': range_queries}}

    @staticmethod
    def _generate_malformed_query(data):
        """Generates a query on the ``_all`` field with all the query content.

        Args:
            data (six.text_type or list): The query in the format of ``six.text_type`` (when used from parsing driver)
                or ``list`` when used from withing the ES visitor.
        """
        if isinstance(data, six.text_type):
            # Remove colon character (special character for ES)
            query_str = data.replace(':', ' ')
        else:
            query_str = ' '.join([word.strip(':') for word in data.children])

        return {
            'query_string': {
                'default_field': '_all',
                'query': query_str
            }
        }

    # ################

    def visit_empty_query(self, node):
        return {'match_all': {}}

    def visit_value_op(self, node):
        return {
            'match': {
                "_all": {
                    "query": node.op.value,
                    "operator": "and",
                }
            }
        }

    def visit_malformed_query(self, node):
        return ElasticSearchVisitor._generate_malformed_query(node)

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
            if ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['date'] == fieldnames:
                return self._generate_date_with_wildcard_query(node.value)

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
                if ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['date'] == fieldnames:
                    # Date queries with simple values are transformed into range queries, among the given and the exact
                    # next date, according to the granularity of the given date.
                    return self._generate_range_queries(force_list(fieldnames), {ES_RANGE_EQ_OPERATOR: node.value})

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

                elif ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['exact-author'] == fieldnames:
                    return self._generate_exact_author_query(node.value)

                elif ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['irn'] == fieldnames:
                    return {'term': {fieldnames: ''.join(('SPIRES-', node.value))}}

                elif ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['title'] == fieldnames:
                    return self._generate_title_queries(node.value)

                elif ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['type-code'] == fieldnames:
                    return self._generate_type_code_query(node.value)

                return {
                    'match': {
                        fieldnames: {
                            "query": node.value,
                            "operator": "and",
                        }
                    }
                }

    def visit_exact_match_value(self, node, fieldnames=None):
        """Generates a term query (exact search in ElasticSearch)."""
        if not fieldnames:
            fieldnames = ['_all']
        else:
            fieldnames = force_list(fieldnames)

        if ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['exact-author'] == fieldnames[0]:
            return self._generate_exact_author_query(node.value)

        elif ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['type-code'] == fieldnames[0]:
            return self._generate_type_code_query(node.value)

        bai_fieldnames = self._generate_fieldnames_if_bai_query(
            node.value,
            bai_field_variation=FieldVariations.raw,
            query_bai_field_if_dots_in_name=False
        )

        if ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['date'] == fieldnames:
            term_queries = [{'term': {field: _truncate_date_value_according_on_date_field(field, node.value).dumps()}}
                            for field
                            in fieldnames]
        else:
            term_queries = [{'term': {field: node.value}} for field in (bai_fieldnames or fieldnames)]

        if len(term_queries) > 1:
            return {'bool': {'should': term_queries}}
        else:
            return term_queries[0]

    def visit_partial_match_value(self, node, fieldnames=None):
        """Generates a query which looks for a substring of the node's value in the given fieldname."""
        if ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['date'] == fieldnames:
            # Date queries with partial values are transformed into range queries, among the given and the exact
            # next date, according to the granularity of the given date.
            if node.contains_wildcard:
                return self._generate_date_with_wildcard_query(node.value)

            return self._generate_range_queries(force_list(fieldnames), {ES_RANGE_EQ_OPERATOR: node.value})

        if ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['exact-author'] == fieldnames:
            return self._generate_exact_author_query(node.value)

        elif ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['type-code'] == fieldnames:
            return self._generate_type_code_query(node.value)

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
