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

from pytest import raises

from inspire_query_parser.utils.visitor_utils import _truncate_wildcard_from_date

from test_utils import parametrize


@parametrize({
    'Wildcard as whole day': {
        'date': '2018-01-*', 'expected_date': '2018-01'
    },
    'Wildcard as part of the day': {
        'date': '2018-01-1*', 'expected_date': '2018-01'
    },
    'Wildcard as whole day (space separated)': {
        'date': '2018 01 *', 'expected_date': '2018-01'
    },
    'Wildcard as part of the day (space separated)': {
        'date': '2018 01 1*', 'expected_date': '2018-01'
    },

    'Wildcard as whole month': {
        'date': '2018-*', 'expected_date': '2018'
    },
    'Wildcard as part of the month': {
        'date': '2018-*', 'expected_date': '2018'
    },
    'Wildcard as whole month (space separated)': {
        'date': '2018 *', 'expected_date': '2018'
    },
    'Wildcard as part of the month (space separated)': {
        'date': '2018 1*', 'expected_date': '2018'
    },
})
def test_truncate_wildcard_from_date_with_wildcard(date, expected_date):
    assert _truncate_wildcard_from_date(date) == expected_date


def test_truncate_wildcard_from_date_throws_on_wildcard_in_year():
    date = '201*'
    with raises(ValueError):
        _truncate_wildcard_from_date(date)


def test_truncate_wildcard_from_date_throws_with_unsupported_separator():
    date = '2018_1*'
    with raises(ValueError):
        _truncate_wildcard_from_date(date)
