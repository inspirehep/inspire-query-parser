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

from __future__ import absolute_import, print_function, unicode_literals

from pytest import raises

from inspire_query_parser.utils.visitor_utils import (
    _truncate_wildcard_from_date,
    author_name_contains_fullnames,
    generate_minimal_name_variations,
)

from test_utils import parametrize


@parametrize({
    'Name with full name parts': {
        'name': 'mele salvatore', 'expected_answer': True
    },
    'Lastname only': {
        'name': 'mele', 'expected_answer': False
    },
    'Lastname, initial(Firstname)': {
        'name': 'mele s', 'expected_answer': False
    },
    'Lastname, initial(Firstname).': {
        'name': 'mele s.', 'expected_answer': False
    },
})
def test_author_name_contains_fullnames(name, expected_answer):
    assert expected_answer == author_name_contains_fullnames(name)


def test_generate_minimal_name_variations_lastname_firstname():
    name = 'Ellis, John'
    expected_variations = {
        'ellis john',
        'ellis j',
        'john ellis',
        'john e',
    }

    assert expected_variations == set(generate_minimal_name_variations(name))


def test_generate_minimal_name_variations_firstname_lastname():
    name = 'John Ellis'
    expected_variations = {
        'ellis john',
        'ellis j',
        'john ellis',
        'john e',
    }

    assert expected_variations == set(generate_minimal_name_variations(name))


def test_generate_minimal_name_variations_with_dotted_initial():
    name = 'Oz, Y.'
    expected_variations = {
        'oz y.',
        'oz y',
        'y. oz',
    }

    result = generate_minimal_name_variations(name)

    assert len(expected_variations) == len(result)

    assert expected_variations == set(generate_minimal_name_variations(name))


def test_generate_minimal_name_variations_without_dotted_initial_doesnt_generate_same_variation():
    name = 'Oz, Y'
    expected_variations = {
        'oz y',
        'y oz',
    }

    result = generate_minimal_name_variations(name)

    assert len(expected_variations) == len(result)

    assert expected_variations == set(result)


def test_generate_minimal_name_variations_with_initial_strips_multiple_consecutive_whitespace():
    name = 'oz,y'
    expected_variations = {
        'oz y',
        'y oz',
    }

    assert expected_variations == set(generate_minimal_name_variations(name))


def test_generate_minimal_name_variations_with_lastname_lowercases():
    name = 'Mele'
    expected_variations = ['mele']

    assert expected_variations == generate_minimal_name_variations(name)


def test_generate_minimal_name_variations_with_dashed_lastname():
    name = 'Caro-Estevez'
    expected_variations = ['caro estevez']

    assert expected_variations == generate_minimal_name_variations(name)


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
