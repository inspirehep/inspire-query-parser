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

from datetime import date
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import re
from unidecode import unidecode

from inspire_utils.name import ParsedName

from inspire_utils.date import PartialDate

from inspire_query_parser.ast import GenericValue
from inspire_query_parser.config import (DATE_LAST_MONTH_REGEX_PATTERN,
                                         DATE_SPECIFIERS_COLLECTION,
                                         DATE_THIS_MONTH_REGEX_PATTERN,
                                         DATE_TODAY_REGEX_PATTERN,
                                         DATE_YESTERDAY_REGEX_PATTERN)


def author_name_contains_fullnames(author_name):
    """Recognizes whether the name contains full name parts and not initials or only lastname.

    Returns:
          bool: True if name has only full name parts, e.g. 'Ellis John', False otherwise. So for example, False is
            returned for 'Ellis, J.' or 'Ellis'.
    """
    def _is_initial(name_part):
        return len(name_part) == 1 or u'.' in name_part

    parsed_name = ParsedName(author_name)

    if len(parsed_name) == 1:
        return False
    elif any([_is_initial(name_part) for name_part in parsed_name]):
        return False

    return True


def _name_variation_has_only_initials(name):
    """Detects whether the name variation consists only from initials."""
    def _is_initial(name_variation):
        return len(name_variation) == 1 or u'.' in name_variation

    parsed_name = ParsedName.loads(name)

    return all([_is_initial(name_part) for name_part in parsed_name])


def generate_minimal_name_variations(author_name):
    """Generate a small number of name variations.

    Notes:
        Unidecodes the name, so that we use its transliterated version, since this is how the field is being indexed.

        For names with more than one part, {lastname} x {non lastnames, non lastnames initial} variations.
        Additionally, it generates the swapped version of those, for supporting queries like ``Mele Salvatore`` which
        ``ParsedName`` parses as lastname: Salvatore and firstname: Mele. So in those cases, we need to generate both
        ``Mele, Salvatore`` and ``Mele, S``.

        Wherever, the '-' is replaced by ' ', it's done because it's the way the name variations are being index, thus
        we want our minimal name variations to be generated identically. This has to be done after the creation of
        ParsedName, otherwise the name is parsed differently. E.g. 'Caro-Estevez' as is, it's a lastname, if we replace
        the '-' with ' ', then it's a firstname and lastname.
    """
    parsed_name = ParsedName.loads(unidecode(author_name))

    if len(parsed_name) > 1:
        lastnames = parsed_name.last.replace('-', ' ')

        non_lastnames = ' '.join(
            parsed_name.first_list + parsed_name.middle_list + parsed_name.suffix_list
        )
        # Strip extra whitespace added if any of middle_list and suffix_list are empty.
        non_lastnames = non_lastnames.strip().replace('-', ' ')

        # Adding into a set first, so as to drop identical name variations.
        return list({
            name_variation.lower()
            for name_variation
            in [
                lastnames + ' ' + non_lastnames,
                lastnames + ' ' + non_lastnames[0],
                non_lastnames + ' ' + lastnames,
                non_lastnames + ' ' + lastnames[0],
            ]
            if not _name_variation_has_only_initials(name_variation)
        })
    else:
        return [parsed_name.dumps().replace('-', ' ').lower()]


# #### Date specifiers related utils ####
ANY_PREFIX_AND_A_NUMBER = re.compile('(.+)(\d+)')

# ES query constants that provide rounding of dates on query time, according to the date "resolution" the user gave.
# More here: https://www.elastic.co/guide/en/elasticsearch/reference/6.1/common-options.html#date-math
ES_DATE_MATH_ROUNDING_YEAR = "||/y"
ES_DATE_MATH_ROUNDING_MONTH = "||/M"
ES_DATE_MATH_ROUNDING_DAY = "||/d"


def _compile_date_regexes(date_specifier_patterns):
    date_specifier_regexes = {}
    for date_specifier in date_specifier_patterns:
        date_specifier_regexes[date_specifier] = re.compile(date_specifier, re.IGNORECASE)
    return date_specifier_regexes


DATE_SPECIFIERS_REGEXES = _compile_date_regexes(DATE_SPECIFIERS_COLLECTION)
"""Mapping from date specifier text to date specifier compiled regexes."""


def register_date_conversion_handler(date_specifier_patterns):
    """Decorator for registering handlers that convert text dates to dates.

    Args:
        date_specifier_patterns (str): the date specifier (in regex pattern format) for which the handler is registered
    """

    def _decorator(func):
        global DATE_SPECIFIERS_CONVERSION_HANDLERS
        DATE_SPECIFIERS_CONVERSION_HANDLERS[DATE_SPECIFIERS_REGEXES[date_specifier_patterns]] = func
        return func

    return _decorator


DATE_SPECIFIERS_CONVERSION_HANDLERS = {}
"""Mapping that depending on the date-specifier (key), returns the handler that converts the textual date to date."""


def _extract_number_from_text(text):
    number = 0  # fallback in case extracting the number fails
    number_match = ANY_PREFIX_AND_A_NUMBER.match(text)
    if number_match:
        try:
            number = int(number_match.group(2))
        except ValueError:
            pass
    return number


def _convert_date_to_string(start_date, relative_delta=None):
    return str(start_date - relative_delta) if relative_delta is not None else str(start_date)


@register_date_conversion_handler(DATE_TODAY_REGEX_PATTERN)
def convert_today_date_specifier(relative_date_specifier_suffix):
    start_date = date.today()
    relative_delta = (
        relativedelta(days=_extract_number_from_text(relative_date_specifier_suffix))
        if relative_date_specifier_suffix else None
    )

    return _convert_date_to_string(start_date, relative_delta)


@register_date_conversion_handler(DATE_YESTERDAY_REGEX_PATTERN)
def convert_yesterday_date_specifier(relative_date_specifier_suffix):
    start_date = date.today() - relativedelta(days=1)
    relative_delta = (
        relativedelta(days=_extract_number_from_text(relative_date_specifier_suffix))
        if relative_date_specifier_suffix else None
    )

    return _convert_date_to_string(start_date, relative_delta)


@register_date_conversion_handler(DATE_THIS_MONTH_REGEX_PATTERN)
def convert_this_month_date(relative_date_specifier_suffix):
    start_date = date.today()
    relative_delta = (
        relativedelta(months=_extract_number_from_text(relative_date_specifier_suffix))
        if relative_date_specifier_suffix else None
    )

    return _convert_date_to_string(start_date, relative_delta)


@register_date_conversion_handler(DATE_LAST_MONTH_REGEX_PATTERN)
def convert_last_month_date(relative_date_specifier_suffix):
    start_date = date.today() - relativedelta(months=1)
    relative_delta = (
        relativedelta(months=_extract_number_from_text(relative_date_specifier_suffix))
        if relative_date_specifier_suffix else None
    )

    return _convert_date_to_string(start_date, relative_delta)


ES_MAPPING_HEP_DATE_ONLY_YEAR = {
    'publication_info.year',
}
"""Contains all the dates that contain always only a year date."""

ES_RANGE_EQ_OPERATOR = 'eq'
"""Additional (internal to the parser) range operator, for handling date equality queries as ranges."""


def _truncate_wildcard_from_date(date_value):
    """Truncate wildcard from date parts.

    Returns:
        (str) The truncated date.

    Raises:
        ValueError, on either unsupported date separator (currently only ' ' and '-' are supported), or if there's a
        wildcard in the year.

    Notes:
        Either whole date part is wildcard, in which we ignore it and do a range query on the
        remaining parts, or some numbers are wildcards, where again, we ignore this part.
    """
    if ' ' in date_value:
        date_parts = date_value.split(' ')
    elif '-' in date_value:
        date_parts = date_value.split('-')
    else:
        # Either unsupported separators or wildcard in year, e.g. '201*'.
        raise ValueError("Erroneous date value: %s.", date_value)

    if GenericValue.WILDCARD_TOKEN in date_parts[-1]:
        del date_parts[-1]

    return '-'.join(date_parts)


def _truncate_date_value_according_on_date_field(field, date_value):
    """Truncates date value (to year only) according to the given date field.

    Args:
        field (unicode): The field for which the date value will be used to query on.
        date_value (str): The date value that is going to be truncated to its year.

    Returns:
        PartialDate: The possibly truncated date, on success. None, otherwise.

    Notes:
        In case the fieldname is in `ES_MAPPING_HEP_DATE_ONLY_YEAR`, then the date is normalized and then only its year
        value is used. This is needed for ElasticSearch to be able to do comparisons on dates that have only year, which
        fails if being queried with a date with more .
    """
    try:
        partial_date = PartialDate.parse(date_value)
    except ValueError:
        return None

    if field in ES_MAPPING_HEP_DATE_ONLY_YEAR:
        truncated_date = PartialDate.from_parts(partial_date.year)
    else:
        truncated_date = partial_date

    return truncated_date


def _get_next_date_from_partial_date(partial_date):
    """Calculates the next date from the given partial date.

    Args:
        partial_date (inspire_utils.date.PartialDate): The partial date whose next date should be calculated.

    Returns:
        PartialDate: The next date from the given partial date.
    """
    relativedelta_arg = 'years'

    if partial_date.month:
        relativedelta_arg = 'months'
    if partial_date.day:
        relativedelta_arg = 'days'

    next_date = parse(partial_date.dumps()) + relativedelta(**{relativedelta_arg: 1})
    return PartialDate.from_parts(
        next_date.year,
        next_date.month if partial_date.month else None,
        next_date.day if partial_date.day else None
    )


def _get_proper_elastic_search_date_rounding_format(partial_date):
    """Returns the proper ES date math unit according to the "resolution" of the partial_date.

    Args:
        partial_date (PartialDate): The partial date for which the date math unit is.

    Returns:
        (str): The ES date math unit format.

    Notes:
        This is needed for supporting range queries on dates, i.e. rounding them up or down according to
        the ES range operator.
        For example, without this, a query like 'date > 2010-11', would return documents with date '2010-11-15', due to
        the date value of the query being interpreted by ES as '2010-11-01 01:00:00'. By using the suffixes for rounding
        up or down, the date value of the query is interpreted as '2010-11-30T23:59:59.999', thus not returning the
        document with date '2010-11-15', as the user would expect. See:
        https://www.elastic.co/guide/en/elasticsearch/reference/6.1/query-dsl-range-query.html#_date_math_and_rounding
    """
    es_date_math_unit = ES_DATE_MATH_ROUNDING_YEAR

    if partial_date.month:
        es_date_math_unit = ES_DATE_MATH_ROUNDING_MONTH
    if partial_date.day:
        es_date_math_unit = ES_DATE_MATH_ROUNDING_DAY

    return es_date_math_unit


def update_date_value_in_operator_value_pairs_for_fieldname(field, operator_value_pairs):
    """Updates (operator, date value) pairs by normalizing the date value according to the given field.

    Args:
        field (unicode): The fieldname for which the operator-value pairs are being generated.
        operator_value_pairs (dict): ES range operator {'gt', 'gte', 'lt', 'lte'} along with a value.
            Additionally, if the operator is ``ES_RANGE_EQ_OPERATOR``, then it is indicated that the method should
            generate both a lower and an upper bound operator-value pairs, with the given date_value.

    Notes:
        On a ``ValueError`` an empty operator_value_pairs is returned.
    """
    updated_operator_value_pairs = {}
    for operator, value in operator_value_pairs.items():
        modified_date = _truncate_date_value_according_on_date_field(field, value)
        if not modified_date:
            return {}

        if operator == ES_RANGE_EQ_OPERATOR:
            updated_operator_value_pairs['gte'] = \
                modified_date.dumps() + _get_proper_elastic_search_date_rounding_format(modified_date)

            next_date = _get_next_date_from_partial_date(modified_date)
            updated_operator_value_pairs['lt'] = \
                next_date.dumps() + _get_proper_elastic_search_date_rounding_format(next_date)
        else:
            updated_operator_value_pairs[operator] = \
                modified_date.dumps() + _get_proper_elastic_search_date_rounding_format(modified_date)

    return updated_operator_value_pairs


# #### Generic ElasticSearch DSL generation helpers ####
def generate_match_query(field, value, with_operator_and):
    """Helper for generating a match query.

    Args:
        field (six.text_type): The ES field to be queried.
        value (six.text_type/bool): The value of the query (bool for the case of type-code query ["core: true"]).
        with_operator_and (bool): Flag that signifies whether to generate the explicit notation of the query, along
            with '"operator": "and"', so that all tokens of the query value are required to match.

    Notes:
        If value is of instance bool, then the shortened version of the match query is generated, at all times.
    """
    if isinstance(value, bool):
        return {'match': {field: value}}

    if with_operator_and:
        return {
            'match': {
                field: {
                    'query': value,
                    'operator': 'and'
                }
            }
        }

    return {'match': {field: value}}


def generate_nested_query(path, queries):
    """Generates nested query.

    Returns:
        (dict): The nested query if queries is not falsy, otherwise an empty dict.
    """
    if not queries:
        return {}

    return {
        'nested': {
            'path': path,
            'query': queries
        }
    }


def wrap_queries_in_bool_clauses_if_more_than_one(queries,
                                                  use_must_clause,
                                                  preserve_bool_semantics_if_one_clause=False):
    """Helper for wrapping a list of queries into a bool.{must, should} clause.

    Args:
        queries (list): List of queries to be wrapped in a bool.{must, should} clause.
        use_must_clause (bool): Flag that signifies whether to use 'must' or 'should' clause.
        preserve_bool_semantics_if_one_clause (bool): Flag that signifies whether to generate a bool query even if
            there's only one clause. This happens to generate boolean query semantics. Usually not the case, but
            useful for boolean queries support.

    Returns:
        (dict): If len(queries) > 1, the bool clause, otherwise if len(queries) == 1, will return the query itself,
                while finally, if len(queries) == 0, then an empty dictionary is returned.
    """
    if not queries:
        return {}

    if len(queries) == 1 and not preserve_bool_semantics_if_one_clause:
        return queries[0]

    return {
        'bool': {
            ('must' if use_must_clause else 'should'): queries
        }
    }
