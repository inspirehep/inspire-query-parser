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

from inspire_utils.date import PartialDate

from inspire_query_parser.config import (DATE_LAST_MONTH_REGEX_PATTERN,
                                         DATE_SPECIFIERS_COLLECTION,
                                         DATE_THIS_MONTH_REGEX_PATTERN,
                                         DATE_TODAY_REGEX_PATTERN,
                                         DATE_YESTERDAY_REGEX_PATTERN)

# #### Date specifiers related utils ####
ANY_PREFIX_AND_A_NUMBER = re.compile('(.+)(\d+)')


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
    start_date = date.today().replace(day=1)
    relative_delta = (
        relativedelta(months=_extract_number_from_text(relative_date_specifier_suffix))
        if relative_date_specifier_suffix else None
    )

    return _convert_date_to_string(start_date, relative_delta)


@register_date_conversion_handler(DATE_LAST_MONTH_REGEX_PATTERN)
def convert_last_month_date(relative_date_specifier_suffix):
    start_date = date.today().replace(day=1) - relativedelta(months=1)
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


def get_next_date_from_partial_date(partial_date):
    """Calculates the next date from the given partial date.

    Args:
        partial_date (inspire_utils.date.PartialDate): The partial date whose next date should be calculated.

    Returns:
        (str): The next date from the given partial date.
    """
    relativedelta_arg = 'years'
    if partial_date.month and not partial_date.day:
        relativedelta_arg = 'months'
    elif partial_date.month and partial_date.day:
        relativedelta_arg = 'days'

    next_date = parse(partial_date.dumps()) + relativedelta(**{relativedelta_arg: 1})
    return PartialDate.from_parts(
        next_date.year,
        next_date.month if partial_date.month else None,
        next_date.day if partial_date.day else None
    ).dumps()


def update_date_value_in_operator_value_pairs_for_fieldname(field, operator_value_pairs):
    """Updates (operator, date value) pairs by normalizing the date according to the given field.

    Args:
        field (unicode): The fieldname for which the operator-value pairs are being generated.
        operator_value_pairs (dict): ES range operator {'gt', 'gte', 'lt', 'lte'} along with a value.
            Additionally, if the operator is ``ES_RANGE_EQ_OPERATOR``, then it is indicated that the method should
            generate both a lower and an upper bound operator-value pairs, with the given date_value.

    Notes:
        On a ``ValueError`` an empty operator_value_pairs is returned.

        In case the fieldname is in `ES_MAPPING_HEP_DATE_ONLY_YEAR`, then the date is normalized and then only its year
        value is used. This is needed for ElasticSearch to be able to do comparisons on dates that have only year, which
        fails if being queried with a date with more .
    """
    updated_operator_value_pairs = {}
    for operator, value in operator_value_pairs.iteritems():
        try:
            partial_date = PartialDate.parse(value)
        except ValueError:
            return {}

        if field in ES_MAPPING_HEP_DATE_ONLY_YEAR:
            modified_date = PartialDate.from_parts(partial_date.year)
        else:
            modified_date = partial_date

        if operator == ES_RANGE_EQ_OPERATOR:
            updated_operator_value_pairs['gte'] = modified_date.dumps()
            updated_operator_value_pairs['lt'] = get_next_date_from_partial_date(modified_date)
        else:
            updated_operator_value_pairs[operator] = modified_date.dumps()

    return updated_operator_value_pairs
