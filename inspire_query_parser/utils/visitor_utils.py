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
import re

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
