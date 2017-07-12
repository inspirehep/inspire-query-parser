# coding=utf-8
from __future__ import unicode_literals, print_function

from pypeg2 import parse
from inspire_query_parser.parser import Query
from inspire_query_parser.utils.utils import emit_tree_repr

if __name__ == '__main__':
    # Find keyword combined with other production rules
    print(emit_tree_repr(parse("FIN author:'ellis'", Query)))
    print(emit_tree_repr(parse('Find author "ellis"', Query)))
    print(emit_tree_repr(parse('f author ellis', Query)))

    # Invenio like search
    print(emit_tree_repr(parse("author:ellis and title:boson", Query)))

    # Boolean operator testing
    print(emit_tree_repr(parse("author ellis and title 'boson'", Query)))
    print(emit_tree_repr(parse("a ellis AND title boson", Query)))
    print(emit_tree_repr(parse("au ellis | title 'boson'", Query)))
    print(emit_tree_repr(parse("author ellis OR title 'boson'", Query)))
    print(emit_tree_repr(parse("author ellis + title 'boson'", Query)))
    print(emit_tree_repr(parse("author ellis & title 'boson'", Query)))

    # Negation
    print(emit_tree_repr(parse("ellis and not title 'boson'", Query)))
    print(emit_tree_repr(parse("-title 'boson'", Query)))

    # Nested expressions
    print(emit_tree_repr(parse("author ellis, j. and (title boson or (author /^xi$/ and title foo))", Query)))

    # Metadata search
    print(emit_tree_repr(parse("fulltext:boson", Query)))
    print(emit_tree_repr(parse("reference:Ellis", Query)))
    print(emit_tree_repr(parse('reference "Ellis"', Query)))
    print(emit_tree_repr(parse("exactauthor:M.Vanderhaeghen.1", Query)))
    print(emit_tree_repr(parse('ac: 42', Query)))

    # Only phrases
    print(emit_tree_repr(parse('ellis', Query)))
    print(emit_tree_repr(parse("'ellis'", Query)))

    # Non trivial terminals
    print(emit_tree_repr(parse("find Higgs boson", Query)))
    print(emit_tree_repr(parse("author ellis, j.", Query)))
    print(emit_tree_repr(parse("author j., ellis", Query)))
    print(emit_tree_repr(parse("f title Super Collider Physics", Query)))
    print(emit_tree_repr(parse("find title Alternative the Phase-II upgrade of the ATLAS Inner Detector or title foo",
                               Query)))
    print(emit_tree_repr(parse("find t Closed string field theory: Quantum action", Query)))
    print(emit_tree_repr(parse("find title na61/shine", Query)))
    print(emit_tree_repr(parse("title foo and author abtrall", Query)))
    print(emit_tree_repr(parse("title e-10 and -author:ellis", Query)))
    print(emit_tree_repr(parse("title 'e-10' and -author:ellis", Query)))
    print(emit_tree_repr(parse("find a d'hoker and a gagne", Query)))
    print(emit_tree_repr(parse('a pang，yi', Query)))  # Full-width comma unicode character
    print(emit_tree_repr(parse('f a SU(2)', Query)))
    # print(emit_tree_repr(parse("773__w:C11-10-03.2 or 773__w:C11/10/03.2 and 980__a:ConferencePaper", StartRule)))

    # Recognizing same terminal token differently.
    print(emit_tree_repr(parse("a a, ellis", Query)))

    # Unicode terminals
    print(emit_tree_repr(parse('a ekström and t γ-radiation', Query)))

    # Ranges
    print(emit_tree_repr(parse("t bar->foo", Query)))
    print(emit_tree_repr(parse("ac 1->10", Query)))
