#!/usr/bin/env python
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

import re
import sys

from pypeg2 import parse

from inspire_query_parser.parser import Query
from inspire_query_parser.utils.utils import emit_tree_repr

unsupported = {"collection", "refersto", "citedby"}

if __name__ == '__main__':
    with open("queries.txt", "r") as input_file:
        queries_read = 0
        for line in input_file:

            try:
                t = parse(line, Query)
                # print(emit_tree_repr(t))

                queries_read += 1
            except (ValueError, SyntaxError):
                if not unsupported.intersection(set(re.split('[ :]', line))):
                    sys.stderr.write(line)
