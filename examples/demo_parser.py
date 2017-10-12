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

from __future__ import print_function, unicode_literals

import sys

from inspire_query_parser.parser import Query
from inspire_query_parser.stateful_pypeg_parser import StatefulParser
from inspire_query_parser.utils.format_parse_tree import emit_tree_format
from inspire_query_parser.visitors.restructuring_visitor import RestructuringVisitor


def repl():
    """Read-Eval-Print-Loop for reading the query, printing it and its parse tree.

    Exit the loop either with an interrupt or "quit".
    """
    while True:
        try:
            sys.stdout.write("Type in next query: \n> ")
            import locale
            query_str = raw_input().decode(sys.stdin.encoding or locale.getpreferredencoding(True))
        except KeyboardInterrupt:
            break

        if u'quit' in query_str:
            break

        print_query_and_parse_tree(query_str)


def print_query_and_parse_tree(query_str):
    parser = StatefulParser()
    print('\033[94m' + "Parsing " + '\033[1m' + query_str + "" + '\033[0m')
    _, parse_tree = parser.parse(query_str, Query)
    print('\033[92m' + emit_tree_format(parse_tree.accept(RestructuringVisitor())) + '\033[0m')
    print("————————————————————————————————————————————————————————————————————————————————")


if __name__ == '__main__':
    # repl()

    # Find keyword combined with other production rules
    print_query_and_parse_tree(r"FIN author:'ellis'")
    print_query_and_parse_tree(r"find a T.A. Aibergenov and date = 1986")
    print_query_and_parse_tree(r'Find author "ellis"')
    print_query_and_parse_tree(r'f author ellis')

    # Invenio like search
    print_query_and_parse_tree(r"author:ellis and title:boson")
    print_query_and_parse_tree(r"unknown_keyword:'bar'")
    print_query_and_parse_tree(r"dotted.keyword:'bar'")

    # Boolean operator testing (And/Or)
    print_query_and_parse_tree(r"author ellis and title 'boson'")
    print_query_and_parse_tree(r"f a appelquist and date 1983")
    print_query_and_parse_tree(r"fin a henneaux and citedby a nicolai")
    print_query_and_parse_tree(r"au ellis | title 'boson'")
    print_query_and_parse_tree(r"-author ellis OR title 'boson'")
    print_query_and_parse_tree(r"author ellis & title 'boson'")

    # Implicit And
    # Works in the case of "A B":
    # 1) B KeywordQuery is of format "keyword:value"
    # 2) B is a NotQuery, e.g. "title foo not title bar"
    # 3) A or B KeywordQueries have a ComplexValue as value, e.g. author 'ellis' title boson
    # 4) B KeywordQuery has a keyword that is a non-shortened version of INSPIRE_KEYWORDS.
    print_query_and_parse_tree(r"author ellis elastic.keyword:'boson'")
    print_query_and_parse_tree(r"find cn atlas not tc c")
    print_query_and_parse_tree(r"author:ellis j title:'boson' reference:M.N.1")
    print_query_and_parse_tree(r"author ellis title 'boson' not title higgs")
    print_query_and_parse_tree(r"author ellis - title 'boson'")

    # ##### Boolean operators at terminals level ####
    # 1. Boolean operators among simple values
    print_query_and_parse_tree(r"author ellis, j and smith")
    # 2. An and query among terminals or and "j" signifies the "journal" keyword?
    print_query_and_parse_tree(r"f author ellis, j and patrignani and j Chin.Phys.")
    # This one is ambiguous since first name "j" overlaps with journals
    print_query_and_parse_tree(r"f author ellis, j and patrignani and j ellis")
    # While this is clearer
    print_query_and_parse_tree(r"f author ellis, j and patrignani and j, ellis")

    # Negation
    print_query_and_parse_tree(r"ellis and not title 'boson'")
    print_query_and_parse_tree(r"-title 'boson'")

    # Nested expressions
    print_query_and_parse_tree(r"author ellis, j. and (title boson or (author /^xi$/ and title foo))")
    print_query_and_parse_tree(r"author ellis, j. and not (title boson or not (author /^xi$/ and title foo))")

    # Metadata search
    print_query_and_parse_tree(r'fulltext:boson and (reference:Ellis or reference "Ellis")')
    print_query_and_parse_tree(r"exactauthor:M.Vanderhaeghen.1 and ac: 42")

    # Simple phrases
    print_query_and_parse_tree(r'ellis')
    print_query_and_parse_tree(r"'ellis'")

    # Parenthesized keyword query values (working also with SPIRES operators - doesn't on legacy)
    print_query_and_parse_tree(r"author:(title ellis)")
    print_query_and_parse_tree(r"author (pardo, f AND slavich) OR (author:bernreuther and not date:2017)")

    # Non trivial terminals
    print_query_and_parse_tree(r"author smith and j., ellis")
    print_query_and_parse_tree(r"find title Alternative the Phase-II upgrade of the ATLAS Inner Detector or na61/shine")
    print_query_and_parse_tree(r"find (j phys.rev. and vol d85) or (j phys.rev.lett.,62,1825)")
    print_query_and_parse_tree(r"title e-10 and -author d'hoker")
    print_query_and_parse_tree(r'a pang，yi and ekström and t SU(2)')  # Full-width comma unicode character
    print_query_and_parse_tree(r't e(+)e(-) or e+e- Colliders')
    print_query_and_parse_tree(r"title: Si-28(p(pol.),n(pol.))")
    print_query_and_parse_tree(r"t Si28(p→,p→′)Si28(6−,T=1) ")
    print_query_and_parse_tree(r"ti C-12(vec-p,vec-n)N-12 (g.s.,1+)")

    # Regex
    print_query_and_parse_tree(r"author:/^Ellis, (J|John)$/")
    print_query_and_parse_tree(r"title:/dense ([^ $]* )?matter/")

    # Nestable keywords
    print_query_and_parse_tree(r"referstox:author:s.p.martin.1")
    print_query_and_parse_tree(r"find a parke, s j and refersto author witten")
    print_query_and_parse_tree(r"citedbyx:author:s.p.martin.1")
    print_query_and_parse_tree(r"citedby:author:s.p.martin.1")
    print_query_and_parse_tree(r"-refersto:recid:1374998 and citedby:(A.A.Aguilar.Arevalo.1)")
    print_query_and_parse_tree(r"citedby:(author A.A.Aguilar.Arevalo.1 and not a ellis)")
    print_query_and_parse_tree(r"citedby:refersto:recid:1432705")

    # Ranges
    print_query_and_parse_tree(r"d 2015->2017 and cited:1->9")

    # Empty query
    print_query_and_parse_tree(r"")  # Nothing
    print_query_and_parse_tree(r"       ")  # Spaces and Tab

    # G, GE, LT, LE, E queries
    print_query_and_parse_tree(r"date > 2000-10 and < 2000-12")
    print_query_and_parse_tree(r"date after 10/2000 and before 2000-12")
    print_query_and_parse_tree(r"date >= nov 2000 and d<=2005")
    print_query_and_parse_tree(r"date 1978+ + -ac 100+")
    print_query_and_parse_tree(r"f a wimpenny and date = 1987")

    # Date specifiers
    print_query_and_parse_tree(r"date today - 2 and title foo")
    print_query_and_parse_tree(r"date this month author ellis")
    print_query_and_parse_tree(r"date yesterday - 2 - ac 100")
    print_query_and_parse_tree(r"date last month - 2 + ac < 50")
    print_query_and_parse_tree(r"date this month - 2")
    print_query_and_parse_tree(r"du > yesterday - 2")

    # Star queries
    print_query_and_parse_tree(r"find a 'o*aigh' and t \"alge*\" and date >2013")
    print_query_and_parse_tree(r"a *alge | a alge* | a o*aigh")

    # Unrecognized queries
    print_query_and_parse_tree(r"title and foo")
    print_query_and_parse_tree(r"title γ-radiation and and")

    # The query below doesn't work on legacy. Currently, it is recognized as a boolean query (since theory is recognized
    # as a keyword). Can be useful for testing multiple parse trees generation (one with the first parse and a second
    # with removing ":" character (could be one heuristic)).
    # print_query_and_parse_tree(r"find t Closed string field theory: Quantum action")
