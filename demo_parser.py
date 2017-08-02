# coding=utf-8
from __future__ import unicode_literals, print_function

from inspire_query_parser.parser import Query
from inspire_query_parser.stateful_pypeg_parser import parse
from inspire_query_parser.utils.parse_tree_formatter import ParseTreeFormatter
from inspire_query_parser.utils.utils import Colors


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
    print(Colors.OKBLUE + "Parsing: [" + query_str + "]" + Colors.ENDC)
    print(Colors.OKGREEN + ParseTreeFormatter.emit_tree_format(parse(query_str, Query)) + Colors.ENDC)
    print("————————————————————————————————————————————————————————————————————————————————")


if __name__ == '__main__':
    # repl()

    # Find keyword combined with other production rules
    print_query_and_parse_tree(r"FIN author:'ellis'")
    print_query_and_parse_tree(r"find a T.A. Aibergenov and date = 1986")
    print_query_and_parse_tree(r"unknown_keyword:'bar'")
    print_query_and_parse_tree(r"dotted.keyword:'bar'")
    print_query_and_parse_tree(r'Find author "ellis"')
    print_query_and_parse_tree(r'f author ellis')

    # Invenio like search
    print_query_and_parse_tree(r"author:ellis and title:boson")

    # Boolean operator testing (And/Or)
    print_query_and_parse_tree(r"author ellis and title 'boson'")
    print_query_and_parse_tree(r"f a appelquist and date 1983")
    print_query_and_parse_tree(r"fin a henneaux and citedby a nicolai")
    print_query_and_parse_tree(r"au ellis | title 'boson'")
    print_query_and_parse_tree(r"-author ellis OR title 'boson'")
    print_query_and_parse_tree(r"author ellis + title 'boson'")
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
    print_query_and_parse_tree(r"author:ellis j title 'boson' reference:M.N.1")
    print_query_and_parse_tree(r"author ellis title 'boson' not value")

    # ##### Boolean operators at terminals level ####
    # 1. Boolean operators among simple values
    print_query_and_parse_tree(r"author ellis, j and smith")
    # 2. An and query among terminals or and "j" signifies the "journal" keyword?
    print_query_and_parse_tree(r"f author ellis, j and patrignani and j Chin.Phys.")
    # This one is ambiguous since first name "j" overlaps with journals
    print_query_and_parse_tree(r"f author ellis, j and patrignani and j ellis")
    print_query_and_parse_tree(r"f author ellis, j and patrignani and j, ellis")

    # Negation
    print_query_and_parse_tree(r"ellis and not title 'boson'")
    print_query_and_parse_tree(r"-title 'boson'")

    # Nested expressions
    print_query_and_parse_tree(r"author ellis, j. and (title boson or (author /^xi$/ and title foo))")
    print_query_and_parse_tree(r"author ellis, j. and not (title boson or not (author /^xi$/ and title foo))")

    # Metadata search
    print_query_and_parse_tree(r"fulltext:boson")
    print_query_and_parse_tree(r"reference:Ellis")
    print_query_and_parse_tree(r'reference "Ellis"')
    print_query_and_parse_tree(r"exactauthor:M.Vanderhaeghen.1")
    print_query_and_parse_tree(r'ac: 42')

    # Only phrases
    print_query_and_parse_tree(r'ellis')
    print_query_and_parse_tree(r"'ellis'")

    # Parenthesized keyword query values (working also with SPIRES operators - doesn't on legacy)
    print_query_and_parse_tree(r"author:(title ellis)")
    print_query_and_parse_tree(r"author (pardo, f AND slavich) OR (author:bernreuther and date:2017)")
    print_query_and_parse_tree(r"author:(foo or bar and not foobar)")
    print_query_and_parse_tree(r"author (pardo and slavich)")

    # Non trivial terminals
    print_query_and_parse_tree(r"find Higgs boson")
    print_query_and_parse_tree(r"author ellis, j.")
    print_query_and_parse_tree(r"author smith and j., ellis")
    print_query_and_parse_tree(r"f title Super Collider Physics")
    print_query_and_parse_tree(r"find title Alternative the Phase-II upgrade of the ATLAS Inner Detector or title foo")
    print_query_and_parse_tree(r"find title na61/shine")
    print_query_and_parse_tree(r"find j phys.rev. and vol d85")
    print_query_and_parse_tree(r"find j phys.rev.lett.,62,1825")
    print_query_and_parse_tree(r"title foo and author abtrall")
    print_query_and_parse_tree(r"title e-10 and -author d'hoker")
    print_query_and_parse_tree(r'a pang，yi')  # Full-width comma unicode character
    print_query_and_parse_tree(r'f a SU(2)')
    print_query_and_parse_tree(r't e(+)e(-)')
    print_query_and_parse_tree(r't e+e- Colliders')
    print_query_and_parse_tree(r"a a, ellis")
    print_query_and_parse_tree(r"title: Si-28(p(pol.),n(pol.))")
    print_query_and_parse_tree(r"title:  Si28(p→,p→′)Si28(6−,T=1) ")
    print_query_and_parse_tree(r"title:  C-12(vec-p,vec-n)N-12 (g.s.,1+)")

    # Regex
    print_query_and_parse_tree(r"author:/^Ellis, (J|John)$/")
    print_query_and_parse_tree(r"-year:/^[[:digit:]]{4}([\?\-]|\-[[:digit:]]{4})?$/")
    print_query_and_parse_tree(r"title:/dense ([^ $]* )?matter/")

    # Nestable keywords
    print_query_and_parse_tree(r"referstox:author:s.p.martin.1")
    print_query_and_parse_tree(r"find a parke, s j and refersto author witten")
    print_query_and_parse_tree(r"citedbyx:author:s.p.martin.1")
    print_query_and_parse_tree(r"citedby:author:s.p.martin.1")
    print_query_and_parse_tree(r"-refersto:recid:1374998 and citedby:(A.A.Aguilar.Arevalo.1)")
    print_query_and_parse_tree(r"citedby:(author A.A.Aguilar.Arevalo.1 and not a ellis)")
    print_query_and_parse_tree(r"citedby:refersto:recid:1432705")

    # Unicode terminals
    print_query_and_parse_tree(r'a ekström and t γ-radiation')

    # Ranges
    print_query_and_parse_tree(r"t bar->foo")
    print_query_and_parse_tree(r't "bar"->"foo"')
    print_query_and_parse_tree(r't bar->"foo"')
    print_query_and_parse_tree(r"ac 1->10")

    # Empty query
    print_query_and_parse_tree(r"")  # Nothing
    print_query_and_parse_tree(r"       ")  # Spaces and Tab

    # G, GE, LT, LE, E queries
    print_query_and_parse_tree(r"date > 10-2000 and title foo")
    print_query_and_parse_tree(r"date after 10/2000 - title foo")
    print_query_and_parse_tree(r"date >= nov 2000 - author ellis")
    print_query_and_parse_tree(r"date 1978+ + -ac 100+")
    print_query_and_parse_tree(r"date 2010-06+ or foo")
    print_query_and_parse_tree(r"date 2010-06   + or foo")
    print_query_and_parse_tree(r"date before 2000 and ac < 100")
    print_query_and_parse_tree(r"date before 2000 and ac 100+")
    print_query_and_parse_tree(r"ac 100- and -date <= 2000")
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
    print_query_and_parse_tree(r"find t $ \psi $ decays")

    # Unrecognized queries
    print_query_and_parse_tree(r"title and foo")
    print_query_and_parse_tree(r"title γ-radiation and and")

    # The query below doesn't work on legacy. Currently, it is recognized as a boolean query (since theory is recognized
    # as a keyword). Can be useful for testing multiple parse trees generation (one with the first parse and a second
    # with removing ":" character (could be one heuristic)).
    # print_query_and_parse_tree(r"find t Closed string field theory: Quantum action")

