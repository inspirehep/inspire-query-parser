# coding=utf-8
from __future__ import unicode_literals, print_function

from pypeg2 import parse
from inspire_query_parser.parser import StartRule
from inspire_query_parser.utils.utils import emit_tree_repr

if __name__ == '__main__':
    # Find keyword combined with other production rules
    print(emit_tree_repr(parse("FIN author:'ellis'", StartRule)))
    print(emit_tree_repr(parse('find author "ellis"', StartRule)))
    print(emit_tree_repr(parse('f author ellis', StartRule)))

    # Invenio like search
    print(emit_tree_repr(parse("author:ellis and title:boson", StartRule)))

    # Boolean operator testing
    print(emit_tree_repr(parse("author ellis and title 'boson'", StartRule)))
    print(emit_tree_repr(parse("author ellis AND title boson", StartRule)))
    print(emit_tree_repr(parse("author ellis | title 'boson'", StartRule)))
    print(emit_tree_repr(parse("author ellis OR title 'boson'", StartRule)))
    print(emit_tree_repr(parse("author ellis + title 'boson'", StartRule)))
    print(emit_tree_repr(parse("author ellis & title 'boson'", StartRule)))

    # Negation
    print(emit_tree_repr(parse("author ellis and not title 'boson'", StartRule)))
    print(emit_tree_repr(parse("-title 'boson'", StartRule)))

    # Nested expressions
    print(emit_tree_repr(parse("author ellis, j. and (title boson or (author /^xi$/ and title foo))", StartRule)))

    # Metadata search
    print(emit_tree_repr(parse("fulltext:boson", StartRule)))
    print(emit_tree_repr(parse("reference:Ellis", StartRule)))
    print(emit_tree_repr(parse('reference "Ellis"', StartRule)))
    print(emit_tree_repr(parse("exactauthor:M.Vanderhaeghen.1", StartRule)))
    print(emit_tree_repr(parse('authorcount:42', StartRule)))

    # Only phrases
    print(emit_tree_repr(parse('ellis', StartRule)))
    print(emit_tree_repr(parse("'ellis'", StartRule)))

    # Non trivial terminals
    print(emit_tree_repr(parse("find Higgs boson", StartRule)))
    print(emit_tree_repr(parse("author ellis, j.", StartRule)))
    print(emit_tree_repr(parse("author j., ellis", StartRule)))
    print(emit_tree_repr(parse("f title Super Collider Physics", StartRule)))
    print(emit_tree_repr(parse("find title Alternative the Phase-II upgrade of the ATLAS Inner Detector or title foo",
                               StartRule)))
    print(emit_tree_repr(parse("find t Closed string field theory: Quantum action", StartRule)))
    print(emit_tree_repr(parse("find title na61/shine", StartRule)))
    print(emit_tree_repr(parse("title foo and author abtrall", StartRule)))
    print(emit_tree_repr(parse("title e-10 and -author:ellis", StartRule)))
    print(emit_tree_repr(parse("find a d'hoker and a gagne", StartRule)))
    print(emit_tree_repr(parse('a pang，yi', StartRule)))  # Full-width comma unicode character
    print(emit_tree_repr(parse('f a SU(2)', StartRule)))
    # print(emit_tree_repr(parse("773__w:C11-10-03.2 or 773__w:C11/10/03.2 and 980__a:ConferencePaper", StartRule)))

    # Recognizing same terminal token differently.
    print(emit_tree_repr(parse("a a, ellis", StartRule)))

    # Unicode terminals
    print(emit_tree_repr(parse('a ekström and t γ-radiation', StartRule)))

    # Ranges
    print(emit_tree_repr(parse("t bar->foo", StartRule)))
    print(emit_tree_repr(parse("ac 1->10", StartRule)))
