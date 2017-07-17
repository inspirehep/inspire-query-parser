# coding=utf-8
from __future__ import unicode_literals, print_function

from pypeg2 import parse
from inspire_query_parser.parser import Query
from inspire_query_parser.utils.utils import emit_tree_repr


def print_query_and_parse_tree(query_str):
    print("Parsing: [" + query_str + "]")
    print(emit_tree_repr(parse(query_str, Query)))

if __name__ == '__main__':
    # Find keyword combined with other production rules
    print_query_and_parse_tree("FIN author:'ellis'")
    print_query_and_parse_tree('Find author "ellis"')
    print_query_and_parse_tree('f author ellis')

    # Invenio like search
    print_query_and_parse_tree("author:ellis and title:boson")

    # Boolean operator testing (And/ Or/ Implicit And)
    print_query_and_parse_tree("author ellis and title 'boson'")
    print_query_and_parse_tree("f a appelquist and date 1983")
    print_query_and_parse_tree("fin a henneaux and citedby a nicolai")
    print_query_and_parse_tree("au ellis | title 'boson'")
    print_query_and_parse_tree("-author ellis OR title 'boson'")
    print_query_and_parse_tree("author ellis + title 'boson'")
    print_query_and_parse_tree("author ellis & title 'boson'")
    print_query_and_parse_tree("author ellis title 'boson'")

    # Negation
    print_query_and_parse_tree("ellis and not title 'boson'")
    print_query_and_parse_tree("-title 'boson'")

    # Nested expressions
    print_query_and_parse_tree("author ellis, j. and (title boson or (author /^xi$/ and title foo))")
    print_query_and_parse_tree("author ellis, j. and not (title boson or not (author /^xi$/ and title foo))")

    # Metadata search
    print_query_and_parse_tree("fulltext:boson")
    print_query_and_parse_tree("reference:Ellis")
    print_query_and_parse_tree('reference "Ellis"')
    print_query_and_parse_tree("exactauthor:M.Vanderhaeghen.1")
    print_query_and_parse_tree('ac: 42')

    # Only phrases
    print_query_and_parse_tree('ellis')
    print_query_and_parse_tree("'ellis'")

    # Non trivial terminals
    print_query_and_parse_tree("find Higgs boson")
    print_query_and_parse_tree("author ellis, j.")
    print_query_and_parse_tree("author j., ellis")
    print_query_and_parse_tree("f title Super Collider Physics")
    print_query_and_parse_tree("find title Alternative the Phase-II upgrade of the ATLAS Inner Detector or title foo")
    print_query_and_parse_tree("find t Closed string field theory: Quantum action")
    print_query_and_parse_tree("find title na61/shine")
    print_query_and_parse_tree("find j phys.rev. and vol d85")
    print_query_and_parse_tree("title foo and author abtrall")
    print_query_and_parse_tree("title e-10 and -author:ellis")
    print_query_and_parse_tree("title 'e-10' and -author:ellis")
    print_query_and_parse_tree("find a d'hoker and a gagne")
    print_query_and_parse_tree('a pang，yi')  # Full-width comma unicode character
    print_query_and_parse_tree('f a SU(2)')
    print_query_and_parse_tree("a a, ellis")

    # Nestable keywords
    print_query_and_parse_tree("citedbyx:author:s.p.martin.1")
    print_query_and_parse_tree("citedby:author:s.p.martin.1")
    print_query_and_parse_tree("-refersto:recid:1374998 and citedby:(A.A.Aguilar.Arevalo.1)")
    print_query_and_parse_tree("citedby:(author A.A.Aguilar.Arevalo.1 and not a ellis)")
    print_query_and_parse_tree("citedby:refersto:recid:1432705")

    # Unicode terminals
    print_query_and_parse_tree('a ekström and t γ-radiation')

    # Ranges
    print_query_and_parse_tree("t bar->foo")
    print_query_and_parse_tree('t "bar"->"foo"')
    print_query_and_parse_tree('t bar->"foo"')
    print_query_and_parse_tree("ac 1->10")

    # Empty query
    print_query_and_parse_tree("")
    print_query_and_parse_tree("\t \n ")
