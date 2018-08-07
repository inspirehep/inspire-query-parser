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

from inspire_schemas.utils import convert_old_publication_info_to_new
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
    generate_match_query,
    generate_minimal_name_variations,
    generate_nested_query,
    update_date_value_in_operator_value_pairs_for_fieldname,
    wrap_queries_in_bool_clauses_if_more_than_one,
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
    # ## Journal queries ##
    JOURNAL_FIELDS_PREFIX = 'publication_info'
    JOURNAL_TITLE = 'journal_title'
    JOURNAL_VOLUME = 'journal_volume'
    JOURNAL_PAGE_START = 'page_start'
    JOURNAL_ART_ID = 'artid'
    JOURNAL_FIELDS_MAPPING = {
        JOURNAL_TITLE: '.'.join((JOURNAL_FIELDS_PREFIX, JOURNAL_TITLE)),
        JOURNAL_VOLUME: '.'.join((JOURNAL_FIELDS_PREFIX, JOURNAL_VOLUME)),
        JOURNAL_PAGE_START: '.'.join((JOURNAL_FIELDS_PREFIX, JOURNAL_PAGE_START)),
        JOURNAL_ART_ID: '.'.join((JOURNAL_FIELDS_PREFIX, JOURNAL_ART_ID)),
    }
    # ########################################

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
        'exact-author': 'authors.full_name_unicode_normalized',
        'irn': 'external_system_identifiers.value.raw',
        'journal': [
            JOURNAL_FIELDS_MAPPING.values()
        ],
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
    AUTHORS_NESTED_QUERY_PATH = 'authors'
    DATE_NESTED_FIELDS = [
        'publication_info.year',
    ]
    DATE_NESTED_QUERY_PATH = 'publication_info'
    JOURNAL_NESTED_QUERY_PATH = 'publication_info'
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
                            generate_match_query(
                                ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['author'],
                                names_variation[1],
                                with_operator_and=True
                            )
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

        query = {
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

        return generate_nested_query(ElasticSearchVisitor.AUTHORS_NESTED_QUERY_PATH, query)

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
            query = self._generate_term_query(
                '.'.join((ElasticSearchVisitor.AUTHORS_BAI_FIELD, FieldVariations.raw)),
                author_name_or_bai
            )
        else:
            author_name = normalize('NFKC', normalize_name(author_name_or_bai)).lower()
            query = self._generate_term_query(
                ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['exact-author'],
                author_name
            )

        return generate_nested_query(ElasticSearchVisitor.AUTHORS_NESTED_QUERY_PATH, query)

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
                    returns an empty dict.
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
                symbol_queries.append(
                    generate_match_query(
                        '.'.join([title_field, FieldVariations.search]),
                        value,
                        with_operator_and=False
                    )
                )

        return wrap_queries_in_bool_clauses_if_more_than_one(symbol_queries, use_must_clause=True)

    def _generate_title_queries(self, value):
        title_field = ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['title']
        q = generate_match_query(title_field, value, with_operator_and=True)

        symbol_queries = ElasticSearchVisitor._generate_queries_for_title_symbols(title_field, value)
        return wrap_queries_in_bool_clauses_if_more_than_one(
            [element for element in (q, symbol_queries) if element],
            use_must_clause=True
        )

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
            return generate_match_query(*mapping_for_value, with_operator_and=True)
        else:
            return {
                'bool': {
                    'minimum_should_match': 1,
                    'should': [
                        generate_match_query('document_type', value, with_operator_and=True),
                        generate_match_query('publication_type', value, with_operator_and=True),
                    ]
                }
            }

    # TODO Move it to visitor utils
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

    # TODO Move it to visitor utils and write tests for it.
    def _generate_term_query(self, fieldname, value, boost=None):
        if not boost:
            return {
                'term': {
                    fieldname: value
                }
            }

        return {
            'term': {
                fieldname: {
                    'value': value,
                    'boost': boost
                }
            }
        }

    def _generate_boolean_query(self, node):
        condition_a = node.left.accept(self)
        condition_b = node.right.accept(self)

        bool_body = [condition for condition in [condition_a, condition_b] if condition]
        return wrap_queries_in_bool_clauses_if_more_than_one(
            bool_body,
            use_must_clause=isinstance(node, ast.AndOp),
            preserve_bool_semantics_if_one_clause=True
        )

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
                    range_query = {
                        'range': {
                            fieldname: updated_operator_value_pairs
                        }
                    }

                    range_queries.append(
                        generate_nested_query(ElasticSearchVisitor.DATE_NESTED_QUERY_PATH, range_query)
                        if fieldname in ElasticSearchVisitor.DATE_NESTED_FIELDS
                        else range_query
                    )
        else:
            range_queries = [{
                    'range': {
                        fieldname: operator_value_pairs
                    }
                }
                for fieldname in fieldnames
            ]

        return wrap_queries_in_bool_clauses_if_more_than_one(range_queries, use_must_clause=False)

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

    @staticmethod
    def _preprocess_journal_query_value(third_journal_field, old_publication_info_values):
        """Transforms the given journal query value (old publication info) to the new one.

        Args:
            third_journal_field (six.text_type): The final field to be used for populating the old publication info.
            old_publication_info_values (six.text_type): The old publication info. It must be one of {only title, title
                & volume, title & volume & artid/page_start}.

        Returns:
            (dict) The new publication info.
        """
        # Prepare old publication info for :meth:`inspire_schemas.utils.convert_old_publication_info_to_new`.
        publication_info_keys = [
            ElasticSearchVisitor.JOURNAL_TITLE,
            ElasticSearchVisitor.JOURNAL_VOLUME,
            third_journal_field,
        ]
        values_list = [
            value.strip()
            for value
            in old_publication_info_values.split(',')
            if value
        ]

        old_publication_info = [
            {
                key: value
                for key, value
                in zip(publication_info_keys, values_list)
                if value
            }
        ]

        # We are always assuming that the returned list will not be empty. In the situation of a journal query with no
        # value, a malformed query will be generated instead.
        new_publication_info = convert_old_publication_info_to_new(old_publication_info)[0]

        return new_publication_info

    def _generate_journal_nested_queries(self, value):
        """Generates ElasticSearch nested query(s).

        Args:
            value (string): Contains the journal_title, journal_volume and artid or start_page separated by a comma.
                            This value should be of type string.

        Notes:
            The value contains at least one of the 3 mentioned items, in this order and at most 3.
            The 3rd is either the artid or the page_start and it will query the corresponding ES field for this item.
            The values are then split on comma and stripped of spaces before being saved in a values list in order to
            be assigned to corresponding fields.
        """
        # Abstract away which is the third field, we care only for its existence.
        third_journal_field = ElasticSearchVisitor.JOURNAL_PAGE_START

        new_publication_info = ElasticSearchVisitor._preprocess_journal_query_value(third_journal_field, value)

        # We always expect a journal title, otherwise query would be considered malformed, and thus this method would
        # not have been called.
        queries_for_each_field = [
            generate_match_query(ElasticSearchVisitor.JOURNAL_FIELDS_MAPPING[ElasticSearchVisitor.JOURNAL_TITLE],
                                 new_publication_info[ElasticSearchVisitor.JOURNAL_TITLE],
                                 with_operator_and=False)
        ]

        if ElasticSearchVisitor.JOURNAL_VOLUME in new_publication_info:
            queries_for_each_field.append(
                generate_match_query(
                    ElasticSearchVisitor.JOURNAL_FIELDS_MAPPING[ElasticSearchVisitor.JOURNAL_VOLUME],
                    new_publication_info[ElasticSearchVisitor.JOURNAL_VOLUME],
                    with_operator_and=False
                )
            )

        if third_journal_field in new_publication_info:
            artid_or_page_start = new_publication_info[third_journal_field]
            match_queries = [
                generate_match_query(
                    ElasticSearchVisitor.JOURNAL_FIELDS_MAPPING[third_field],
                    artid_or_page_start,
                    with_operator_and=False
                )
                for third_field
                in (ElasticSearchVisitor.JOURNAL_PAGE_START, ElasticSearchVisitor.JOURNAL_ART_ID)
            ]

            queries_for_each_field.append(
                wrap_queries_in_bool_clauses_if_more_than_one(match_queries, use_must_clause=False)
            )

        return generate_nested_query(
            ElasticSearchVisitor.JOURNAL_FIELDS_PREFIX,
            wrap_queries_in_bool_clauses_if_more_than_one(queries_for_each_field, use_must_clause=True)
        )
    # ################

    def visit_empty_query(self, node):
        return {'match_all': {}}

    def visit_value_op(self, node):
        return generate_match_query('_all', node.op.value, with_operator_and=True)

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

            query = self._generate_query_string_query(
                node.value,
                fieldnames=bai_fieldnames or fieldnames,
                analyze_wildcard=True
            )

            if ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['author'] == fieldnames:
                return generate_nested_query(ElasticSearchVisitor.AUTHORS_NESTED_QUERY_PATH, query)
            return query
        else:
            if isinstance(fieldnames, list):
                if ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['date'] == fieldnames:
                    # Date queries with simple values are transformed into range queries, among the given and the exact
                    # next date, according to the granularity of the given date.
                    return self._generate_range_queries(force_list(fieldnames), {ES_RANGE_EQ_OPERATOR: node.value})

                if ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['journal'] == fieldnames:
                    return self._generate_journal_nested_queries(node.value)

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
                            query = {"match": {bai_fieldnames[0]: node.value}}
                            return generate_nested_query(ElasticSearchVisitor.AUTHORS_NESTED_QUERY_PATH, query)
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

                elif fieldnames not in ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME.values():
                    colon_value = ':'.join([fieldnames, node.value])
                    given_field_query = generate_match_query(fieldnames, node.value, with_operator_and=True)
                    texkey_query = self._generate_term_query('texkeys.raw', colon_value, boost=2.0)
                    _all_field_query = generate_match_query('_all', colon_value, with_operator_and=True)
                    return wrap_queries_in_bool_clauses_if_more_than_one([given_field_query, texkey_query, _all_field_query],
                                                                         use_must_clause=False)

                return generate_match_query(fieldnames, node.value, with_operator_and=True)

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

        elif ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['journal'] == fieldnames:
            return self._generate_journal_nested_queries(node.value)

        bai_fieldnames = self._generate_fieldnames_if_bai_query(
            node.value,
            bai_field_variation=FieldVariations.raw,
            query_bai_field_if_dots_in_name=False
        )

        if ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['date'] == fieldnames:
            term_queries = []
            for field in fieldnames:
                term_query =  \
                    {'term': {field: _truncate_date_value_according_on_date_field(field, node.value).dumps()}}

                term_queries.append(
                    generate_nested_query(ElasticSearchVisitor.DATE_NESTED_QUERY_PATH, term_query)
                    if field in ElasticSearchVisitor.DATE_NESTED_FIELDS
                    else term_query
                )
        elif ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['author'] in fieldnames:
            term_queries = [
                generate_nested_query(ElasticSearchVisitor.AUTHORS_NESTED_QUERY_PATH, {'term': {field: node.value}})
                for field in (bai_fieldnames or fieldnames)
            ]
        else:
            term_queries = [{'term': {field: node.value}} for field in (bai_fieldnames or fieldnames)]

        return wrap_queries_in_bool_clauses_if_more_than_one(term_queries, use_must_clause=False)

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

        elif ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['journal'] == fieldnames:
            return self._generate_journal_nested_queries(node.value)

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

        query = self._generate_query_string_query(value,
                                                  fieldnames=bai_fieldnames or fieldnames,
                                                  analyze_wildcard=True)
        if (bai_fieldnames and ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['author'] in bai_fieldnames) \
                or (fieldnames and ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['author'] in fieldnames):
            return generate_nested_query(ElasticSearchVisitor.AUTHORS_NESTED_QUERY_PATH, query)

        return query

    def visit_regex_value(self, node, fieldname):
        query = {
            'regexp': {
                fieldname: node.value
            }
        }

        if ElasticSearchVisitor.KEYWORD_TO_ES_FIELDNAME['author'] == fieldname:
            return generate_nested_query(ElasticSearchVisitor.AUTHORS_NESTED_QUERY_PATH, query)

        return query
