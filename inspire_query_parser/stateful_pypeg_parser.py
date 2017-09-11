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
import six

from pypeg2 import Parser


class StatefulParser(Parser):
    """Defines a stateful parser for encapsulating parsing flags functionality.

    Attributes:
        _parsing_parenthesized_terminal (bool):
            Signifies whether the parser is trying to identify a parenthesized terminal. Used for disabling the
            terminals parsing related check "stop on DSL keyword", for allowing to parse symbols such as "+", "-" which
            are also DSL keywords ('and' and 'not' respectively).

        _parsing_parenthesized_simple_values_expression (bool):
            Signifies whether we are parsing a parenthesized simple values expression. Used for disabling the simple
            values parsing related check "stop on INSPIRE keyword", for allowing parsing more expressions and not
            restrict the input accepted by the parser.
    """

    def __init__(self):
        super(StatefulParser, self).__init__()
        self._parsing_parenthesized_terminal = False
        self._parsing_parenthesized_simple_values_expression = False


def parse(text, thing):
    """Wrapper method for creating a StatefulParser and then parsing text with thing grammar.


    Raises:
        SyntaxError: if text does not match the grammar in thing
        ValueError:  if input does not match types
        TypeError:   if output classes have wrong syntax for __init__()
        GrammarTypeError:   if grammar contains an object of unknown type
        GrammarValueError:  if grammar contains an illegal cardinality value
    """
    if not isinstance(text, six.text_type):
        text = six.text_type(text.decode('utf-8'))

    parser = StatefulParser()
    t, r = parser.parse(text, thing)
    if t:
        raise parser.last_error
    return r
