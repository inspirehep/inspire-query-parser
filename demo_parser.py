# coding=utf-8
from __future__ import unicode_literals, print_function

import sys
from pypeg2 import parse
from inspire_query_parser.parser import Query
from inspire_query_parser.utils.utils import emit_tree_repr, Colors


def print_query_and_parse_tree(query_str):
    print(Colors.OKBLUE + "Parsing: [" + query_str + "]" + Colors.ENDC)
    print(Colors.OKGREEN + emit_tree_repr(parse(query_str, Query)) + Colors.ENDC)
    print("————————————————————————————————————————————————————————————————————————————————")


def repl():
    """Read-Eval-Print-Loop for reading the query, printing it and its parse tree.

    Exit the loop either with an interrupt or quit.
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

if __name__ == '__main__':
    # repl()

    # print_query_and_parse_tree("date today - 2")

    # Find keyword combined with other production rules
    print_query_and_parse_tree("FIN author:'ellis'")
    print_query_and_parse_tree("find a T.A. Aibergenov and date = 1986")
    print_query_and_parse_tree("unknown_keyword:'bar'")
    print_query_and_parse_tree("dotted.keyword:'bar'")
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
    # FIXME Implicit and
    # print_query_and_parse_tree("author ellis title 'boson'")

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
    # The query below doesn't work on legacy. If we add a catch all option at the Statement rule
    # then we can accept it as something unrecognized.
    # print_query_and_parse_tree("find t Closed string field theory: Quantum action")
    print_query_and_parse_tree("find title na61/shine")
    print_query_and_parse_tree("find j phys.rev. and vol d85")
    print_query_and_parse_tree("find j phys.rev.lett.,62,1825")
    print_query_and_parse_tree("title foo and author abtrall")
    print_query_and_parse_tree("title e-10 and -author:ellis")
    print_query_and_parse_tree("title 'e-10' and -author:ellis")
    print_query_and_parse_tree("find a d'hoker and a gagne")
    print_query_and_parse_tree('a pang，yi')  # Full-width comma unicode character
    print_query_and_parse_tree('f a SU(2)')
    print_query_and_parse_tree('t e(+)e(-)')
    print_query_and_parse_tree('t e+e- Colliders')
    print_query_and_parse_tree("a a, ellis")
    print_query_and_parse_tree("title: Si-28(p(pol.),n(pol.))")
    print_query_and_parse_tree("title:  Si28(p→,p→′)Si28(6−,T=1) ")
    print_query_and_parse_tree("title:  C-12(vec-p,vec-n)N-12 (g.s.,1+)")

    # Regex
    print_query_and_parse_tree("author:/^Ellis, (J|John)$/")
    print_query_and_parse_tree("-year:/^[[:digit:]]{4}([\?\-]|\-[[:digit:]]{4})?$/")
    print_query_and_parse_tree("title:/dense ([^ l]* )?matter/")
    print_query_and_parse_tree("title:/dense ([^ $]* )?matter/")

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

    # G, GE, LT, LE, E queries
    print_query_and_parse_tree("date > 10-2000 and title foo")
    print_query_and_parse_tree("date after 10/2000 - title foo")
    print_query_and_parse_tree("date >= 2000 - author ellis")
    print_query_and_parse_tree("date 1978+ + -ac 100+")
    print_query_and_parse_tree("date 2010-06+ or foo")
    print_query_and_parse_tree("date 2010-06   + or foo")
    print_query_and_parse_tree("date before 2000 and ac < 100")
    print_query_and_parse_tree("date before 2000 and ac 100+")
    print_query_and_parse_tree("ac 100- and -date <= 2000")
    print_query_and_parse_tree("f a wimpenny and date = 1987")

    # Star queries
    print_query_and_parse_tree("find a 'o*aigh' and t \"alge*\" and date >2013")
    print_query_and_parse_tree("a *alge | a alge* | a o*aigh")
    print_query_and_parse_tree("find t $\psi$")
    print_query_and_parse_tree("find t $\psi$")
