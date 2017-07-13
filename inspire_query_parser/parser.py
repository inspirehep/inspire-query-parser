# coding=utf-8
from __future__ import unicode_literals, print_function

from pypeg2 import attr, Keyword, Literal, omit, optional, re, K, Enum, contiguous, maybe_some, some, GrammarValueError

from . import ast
from .config import INSPIRE_PARSER_KEYWORDS


# #### Parser customization ####
class CaseInsensitiveKeyword(Keyword):
    """Supports case insensitive keywords

    All subtypes must declare a grammar attribute with an Enum of accepted keywords/literals.
    """
    def __init__(self, keyword):
        """Adds lowercase keyword to the keyword table."""
        try:
            self.grammar
        except AttributeError:
            raise GrammarValueError(self.__class__.__name__ + " expects a grammar attribute (Enum).")
        keyword = keyword.lower()
        if keyword not in Keyword.table:
            Keyword.table[keyword] = self
        self.name = keyword

    @classmethod
    def parse(cls, parser, text, pos):
        m = cls.regex.match(text)
        if m:
            # Check if match is is not in the grammar of the specific keyword class.
            if m.group(0).lower() not in cls.grammar:
                result = text, SyntaxError(repr(m.group(0)) + " is not a member of " + repr(cls.grammar))
            else:
                result = text[len(m.group(0)):], cls(m.group(0))
        else:
            result = text, SyntaxError("expecting match on " + repr(cls.regex))
        return result

CIKeyword = CaseInsensitiveKeyword
# ########################


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
    """SPIRES find keyword.

    We need to have whitespace after the keyword since there's an overlap with other operators, e.g. "fulltext". If not
    this keyword will consume f from fulltext.
    """
    regex = re.compile(r"(find|fin|fi|f)\s", re.IGNORECASE)


class ExactAuthor(Keyword):
    regex = re.compile(r"exactauthor", re.IGNORECASE)


class AuthorCount(Keyword):
    regex = re.compile(r"authorcount|author-count|ac", re.IGNORECASE)


class Fulltext(Keyword):
    regex = re.compile(r"fulltext", re.IGNORECASE)


class Reference(Keyword):
    regex = re.compile(r"reference", re.IGNORECASE)


class And(CIKeyword):
    """
    The reason for defining an Enum grammar of Keywords is for populating the Keyword.table for checking whether
    terminal symbols are actually DSL keywords.
    """
    regex = re.compile(r"(and|\+|&)", re.IGNORECASE)
    grammar = Enum(K("and"), "+", "&")


class Or(CIKeyword):
    """
    The reason for defining an Enum grammar of Keywords is for populating the Keyword.table for checking whether
    terminal symbols are actually DSL keywords.
    """
    regex = re.compile(r"(or|\|)", re.IGNORECASE)
    grammar = Enum(K("or"), "|")


class Not(CIKeyword):
    """
    The reason for defining an Enum grammar of Keywords is for populating the Keyword.table for checking whether
    terminal symbols are actually DSL keywords.
    """
    regex = re.compile(r"(not|-)", re.IGNORECASE)
    grammar = Enum(K("not"), "-")


class Range(object):
    grammar = omit(Literal("->"))
# ########################


# #### Lowest level operators #####
class Qualifier(LeafRule):
    grammar = attr('value', re.compile(r"({0})\b".format("|".join(INSPIRE_PARSER_KEYWORDS))))


class Terminal(LeafRule):
    """Represents terminal symbols that are not keywords.

    Some examples include: na61/shine, e-10, SU(2).
    Terminals separation happens with these " ", ",", ".", ":", "，" characters.
    """
    regex = re.compile(r"(\w+(([-/.']\w+)|(\((\w+|\d+)\)))*)", re.UNICODE)
    extras = maybe_some([" ", ",", ".", ":", "，"])

    def __init__(self, value):
        super(Terminal, self).__init__()
        self.value = value

    @classmethod
    def parse(cls, parser, text, pos):
        m = cls.regex.match(text)
        if m:
            # Check if token is a DSL keyword
            if m.group(0).lower() in Keyword.table:
                return text, SyntaxError("found DSL keyword: " + m.group(0))

            # Extract matched keyword and clean "extras" from resulting text
            result = parser.parse(text[len(m.group(0)):], cls.extras)[0], cls(m.group(0))
        else:
            result = text, SyntaxError("expecting match on " + repr(cls.regex))
        return result


class Terminals(ListRule):
    """Encapsulation rule for terminals.

    From this level downwards, automatic whitespace removal is disabled for PyPeg using contiguous setting.
    """
    grammar = contiguous(attr('children', (some(Terminal))))


class SimpleValue(ListRule):
    """Represents terminals as plaintext.

    E.g. title top cross section.
    """
    grammar = some(Terminals)

    def __init__(self, args):
        self.children = args


class ComplexValue(LeafRule):
    """Accepting value with either single/double quotes or a regex value (/^.../$).

    These values have special and different meaning for the later phases of parsing:
      * Single quotes: partial text matching (text is analyzed before searched)
      * Double quotes: exact text matching
      * Regex: regex searches
    E.g. t 'Millisecond pulsar velocities'.

    This makes no difference for the parser and will be handled at a later parsing phase.
    """
    grammar = attr('value', re.compile(r"((/\^[^$]*\$/)|('[^']*')|(\"[^\"]*\"))")),


class ExactValueRange(BinaryRule):
    """Range for exact values.

    E.g. author:"Ellis, J"->"Ellis, Qqq"
    """
    # TODO change Terminals to exact value regex.
    grammar = omit(Literal('"')), attr('left', Terminals), omit(Literal('"')), \
              omit(Range), \
              omit(Literal('"')), attr('right', Terminals), omit(Literal('"'))


class SimpleValueRange(BinaryRule):
    """Range for simple values, i.e. words or numbers.

    E.g. muon decay year:1983->1992
    """
    # TODO Change Terminals to word/number regex.
    grammar = attr('left', Terminals), omit(Range), attr('right', Terminals)


class Value(UnaryRule):
    """Generic rule for all kinds of phrases recognized.

    Serves as an encapsulation of the listed rules.
    """
    grammar = attr('op', [
        ExactValueRange,
        SimpleValueRange,
        ComplexValue,
        SimpleValue,
    ])


class ExactAuthorOp(UnaryRule):
    """Support for ExactAuthor queries.

    E.g. find ea: andre lukas"""
    # TODO Add as an option an exact value.
    grammar = omit(ExactAuthor), omit(optional(':')), attr('op', SimpleValue)


# TODO Authorcount: Support greater/less that/to operators and merge range.
class AuthorCountOp(UnaryRule):
    grammar = omit(AuthorCount), omit(optional(':')), attr('op', re.compile("\d+"))


class AuthorCountRangeOp(BinaryRule):
    grammar = omit(AuthorCount), omit(optional(':')), \
              attr('left', re.compile("\d+")), omit(Range), attr('right', re.compile("\d+"))


class FulltextOp(UnaryRule):
    grammar = omit(Fulltext), omit(optional(':')), attr('op', SimpleValue)  # TODO add Partial and Exact phrases


class ReferenceOp(UnaryRule):
    grammar = omit(Reference), omit(optional(':')), attr('op', [re.compile(r"\"[^\"]*\""), SimpleValue])
########################


class QualifierExpression(BinaryRule):
    """Qualified keyword queries.

    E.g. author: ellis, or title boson.
    """
    grammar = attr('left', Qualifier), omit(optional(':')), attr('right', Value)


class SimpleQuery(UnaryRule):
    """Query basic units.

    These are comprised of metadata queries, qualified keywords and plaintext phrases (values).
    """
    grammar = attr('op', [
        AuthorCountRangeOp,
        AuthorCountOp,
        ExactAuthorOp,
        FulltextOp,
        ReferenceOp,
        QualifierExpression,
        Value,
    ])


class Statement(UnaryRule):
    """The most generic query component.

    Supports queries chaining."""
    pass


class NotQuery(UnaryRule):
    """Negation query."""
    grammar = omit(Not), attr('op', Statement)


class ParenthesizedQuery(UnaryRule):
    """Parenthesized query for denoting precedence."""
    grammar = omit(Literal('(')), attr('op', Statement), omit(Literal(')'))


class Expression(UnaryRule):
    """A generic query expression.

    Serves as a more restrictive rule than Statement.
    This is useful for eliminating left recursion in the grammar (requirement for PEGs) when used in binary queries as
    left hand side production rule.
    """
    grammar = attr('op', [
        NotQuery,
        ParenthesizedQuery,
        SimpleQuery,
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
    """The entry-point for the grammar.

    Find keyword is ignored as the current grammar is an augmentation of SPIRES and Google style syntaxes.
    It only serves for backward compatibility with SPIRES syntax.
    """
    grammar = [
        (omit(Find), attr('op', Statement)),
        attr('op', Statement),
    ]
