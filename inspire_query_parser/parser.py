# coding=utf-8
from __future__ import unicode_literals, print_function

from pypeg2 import attr, Keyword, Literal, parse, omit, optional, re, Symbol, word, K, Enum, contiguous, maybe_some

from . import ast
from .config import INSPIRE_PARSER_KEYWORDS


class LeafRule(ast.Leaf):
    def __init__(self):
        pass


class UnaryRule(ast.UnaryOp):
    def __init__(self):
        pass


class BinaryRule(ast.BinaryOp):
    def __init__(self):
        pass


class ListRule(ast.ListOp):
    def __init__(self):
        pass
# ########################


# #### Keywords ####
class Find(Keyword):
    keyword = "find"
    regex = re.compile(
        r"({0})\s".format("|".join([keyword[:i] for i in range(len(keyword) + 1, 0, -1)])),
        re.IGNORECASE)
    grammar = Enum(
        K("find"), K("FIND"),
        *[k for i in range(1, len(keyword) + 1) for k in (K(keyword[:i] + " "), K(keyword[:i].upper() + " "))])


class ExactAuthor(Keyword):
    regex = re.compile(r"exactauthor", re.IGNORECASE)
    grammar = Enum(K("exactauthor"), K("EXACTAURTHOR"))


class AuthorCount(Keyword):
    regex = re.compile(r"authorcount|author-count|ac", re.IGNORECASE)
    grammar = Enum(K("authorcount"), K("author-count"), K("ac"), K("AC"), K("AUTHORCOUNT"))


class Fulltext(Keyword):
    regex = re.compile(r"fulltext", re.IGNORECASE)
    grammar = Enum(K("fulltext"), K("FULLTEXT"))


class Reference(Keyword):
    regex = re.compile(r"reference", re.IGNORECASE)
    grammar = Enum(K("reference"))


class And(Keyword):
    regex = re.compile(r"(and|\+|&)", re.IGNORECASE)
    grammar = Enum(K("and"), K("AND"), "+", "&")


class Or(Keyword):
    regex = re.compile(r"(or|\|)", re.IGNORECASE)
    grammar = Enum(K("or"), K("OR"), "|")


class Not(Keyword):
    regex = re.compile(r"(not|-)", re.IGNORECASE)
    grammar = Enum(K("not"), K("NOT"), "-")


class Range(object):
    grammar = omit(Literal("->"))
# ########################


# #### Leafs #####
class Qualifier(LeafRule):
    grammar = attr('value', re.compile(r"({0})\b".format("|".join(INSPIRE_PARSER_KEYWORDS))))


class Terminal(LeafRule):
    Symbol.check_keywords = True
    Symbol.regex = re.compile(r"(\w+(([-/.']\w+)|(\((\w+|\d+)\)))*)", re.UNICODE)
    grammar = attr('value', Symbol), maybe_some([" ", ",", ".", ":", "，"])


class TerminalTail(UnaryRule):
    pass


class Terminals(ListRule):
    grammar = contiguous(attr('children', (Terminal, TerminalTail)))


TerminalTail.grammar = attr('op', [Terminals, None])


class NormalPhrase(UnaryRule):
    grammar = attr('op', Terminals)


class ExactPhraseRange(BinaryRule):
    grammar = omit(Literal('"')), attr('left', Terminals), omit(Literal('"')), \
              omit(Range), \
              omit(Literal('"')), attr('right', Terminals), omit(Literal('"'))


class NormalPhraseRange(BinaryRule):
    grammar = attr('left', Terminals), omit(Range), attr('right', Terminals)


class SpecialPhrase(LeafRule):
    """Accepting value with either double/single quotes or a regex value (/^.../$)."""
    grammar = attr('value', re.compile(r"((/\^[^$]*\$/)|('[^']*')|(\"[^\"]*\"))")),


class Phrase(UnaryRule):
    grammar = attr('op', [
        ExactPhraseRange,
        NormalPhraseRange,
        SpecialPhrase,
        NormalPhrase,
    ])


class ExactAuthorOp(UnaryRule):
    grammar = omit(ExactAuthor), omit(optional(':')), attr('op', NormalPhrase)  # TODO check normal phrase is needed


class AuthorCountOp(UnaryRule):
    grammar = omit(AuthorCount), omit(optional(':')), attr('op', re.compile("\d+"))


class AuthorCountRangeOp(BinaryRule):
    grammar = omit(AuthorCount), omit(optional(':')), \
              attr('left', re.compile("\d+")), omit(Range), attr('right', re.compile("\d+"))


class FulltextOp(UnaryRule):
    grammar = omit(Fulltext), omit(optional(':')), attr('op', NormalPhrase)  # TODO add Partial and Exact phrases


class ReferenceOp(UnaryRule):
    grammar = omit(Reference), omit(optional(':')), attr('op', [re.compile(r"\"[^\"]*\""), NormalPhrase])
########################


class QualifierExpression(BinaryRule):
    grammar = attr('left', Qualifier), omit(optional(':')), \
              attr('right', Phrase)


class TermExpression(UnaryRule):
    grammar = attr('op', [
        AuthorCountRangeOp,
        AuthorCountOp,
        ExactAuthorOp,
        FulltextOp,
        ReferenceOp,
        QualifierExpression,
        Phrase,
    ])


class Statement(UnaryRule):
    pass


class NotQuery(UnaryRule):
    grammar = omit(Not), attr('op', Statement)


class ParenthesizedQuery(UnaryRule):
    grammar = omit(Literal('(')), attr('op', Statement), omit(Literal(')'))


class Expression(UnaryRule):
    grammar = attr('op', [
        NotQuery,
        ParenthesizedQuery,
        TermExpression,
    ])


class AndQuery(BinaryRule):
    pass


class OrQuery(BinaryRule):
    pass


AndQuery.grammar = attr('left', Expression), omit(And), attr('right', Statement)

OrQuery.grammar = attr('left', Expression), omit(Or), attr('right', Statement)
# ########################


# #### Main productions ####
Statement.grammar = attr('op', [AndQuery, OrQuery, Expression])


class Query(UnaryRule):
    grammar = [
        (omit(Find), attr('op', Statement)),
        attr('op', Statement),
    ]
