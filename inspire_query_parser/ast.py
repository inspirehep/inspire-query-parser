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

# Abstract Syntax Tree classes
# I.e. generic syntax tree classes that simply define categories
# for each of the actual AST nodes.


class Leaf(object):

    def __init__(self, value):
        self.value = value

    def accept(self, visitor):
        return visitor.visit(self)

    def __eq__(self, other):
        return type(self) == type(other) and self.value == other.value

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, repr(self.value))


class UnaryOp(object):
    def __init__(self, op):
        self.op = op

    def accept(self, visitor):
        return visitor.visit(self, self.op.accept(visitor))

    def __eq__(self, other):
        return type(self) == type(other) and self.op == other.op

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self.op))


class BinaryOp(object):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def accept(self, visitor):
        return visitor.visit(self,
                             self.left.accept(visitor),
                             self.right.accept(visitor))

    def __eq__(self, other):
        return (
            type(self) == type(other)
        ) and (
            self.left == other.left
        ) and (
            self.right == other.right
        )

    def __repr__(self):
        return "%s(%s, %s)" % (self.__class__.__name__,
                               repr(self.left), repr(self.right))


class ListOp(object):

    def __init__(self, children):
        try:
            iter(children)
        except TypeError:
            self.children = [children]
        else:
            self.children = children

    def accept(self, visitor):
        return visitor.visit(self, [c.accept(visitor) for c in self.children])

    def __eq__(self, other):
        return type(self) == type(other) and self.op == other.op

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self.children))
# Concrete Syntax Tree classes
# I.e. classes that provide the supertypes for the parser nodes.


class Keyword(Leaf):
    pass


class Value(Leaf):
    pass
