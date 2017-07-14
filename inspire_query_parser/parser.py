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
            result = text, SyntaxError("expecting " + repr(cls.__name__))
        return result

CIKeyword = CaseInsensitiveKeyword
# ########################


class BooleanOperator(Enum):
    AND = 'and'
    OR = 'or'


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
class InspireKeyword(LeafRule):
    """Inspire Keyword"""
    grammar = re.compile(r"({0})\b".format("|".join(INSPIRE_PARSER_KEYWORDS.keys())))

    def __init__(self, value):
        self.value = INSPIRE_PARSER_KEYWORDS[value]


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
        """Parses terminals up to keywords defined into the Keyword.table.

        Called by PyPeg.
        """
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


class SimpleValue(ListRule):
    """Represents terminals as plaintext.

    E.g. title top cross section.
    """
    grammar = contiguous(some(Terminal))

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


class RangeOp(BinaryRule):
    """Range operator mixing any type of values.

    E.g.    muon decay year:1983->1992
            author:"Ellis, J"->"Ellis, Qqq"
            author:"Ellis, J"->Ellis, M

    The non symmetrical type of values will be handled at a later phase.
    """
    grammar = attr('left', [ComplexValue, SimpleValue]), omit(Range), attr('right', [ComplexValue, SimpleValue])


class Value(UnaryRule):
    """Generic rule for all kinds of phrases recognized.

    Serves as an encapsulation of the listed rules.
    """
    grammar = attr('op', [
        RangeOp,
        ComplexValue,
        SimpleValue,
    ])
########################


class KeywordQuery(BinaryRule):
    """Keyword queries.

    E.g. author: ellis, or title boson.
    """
    grammar = attr('left', InspireKeyword), omit(optional(':')), attr('right', Value)


class SimpleQuery(UnaryRule):
    """Query basic units.

    These are comprised of metadata queries, keywords and value queries.
    """
    grammar = attr('op', [
        KeywordQuery,
        Value,
    ])


class Statement(UnaryRule):
    """The most generic query component.

    Supports queries chaining."""
    pass


class Expression(UnaryRule):
    """A generic query expression.

    Serves as a more restrictive rule than Statement.
    This is useful for eliminating left recursion in the grammar (requirement for PEGs) when used in binary queries as
    left hand side production rule.
    """
    pass


class NotQuery(UnaryRule):
    """Negation query."""
    grammar = omit(Not), attr('op', Expression)


class ParenthesizedQuery(UnaryRule):
    """Parenthesized query for denoting precedence."""
    grammar = omit(Literal('(')), attr('op', Statement), omit(Literal(')'))


class NestedKeywordQuery(BinaryRule):
    # TODO support citedbyx
    """Nested Keyword queries.

    E.g. citedby:author:hui and cited:author:witten
    """
    pass


Expression.grammar = attr('op', [
    NotQuery,
    NestedKeywordQuery,
    ParenthesizedQuery,
    SimpleQuery,
])


NestedKeywordQuery.grammar = \
    attr('left', [re.compile('refersto', re.IGNORECASE), re.compile('citedby', re.IGNORECASE)]), \
    optional(omit(":")), \
    attr('right', Expression)


class BooleanQuery(BinaryRule):
    """Represents boolean query as a binary rule.

    Attributes:
        bool_op (str): Representation of the actual boolean operator.
    """
    bool_op = None
    grammar = Expression, [And, Or, None], Statement

    def __init__(self, args):
        self.left = args[0]

        if len(args) == 3:
            if isinstance(args[1], And):
                self.bool_op = BooleanOperator.AND
            elif isinstance(args[1], Or):
                self.bool_op = BooleanOperator.OR
            else:
                raise ValueError("Unexpected boolean operator: " + repr(args[1]))
        else:  # Implicit-And query
            self.bool_op = BooleanOperator.AND

        self.right = args[len(args) - 1]
# ########################


# #### Main productions ####
Statement.grammar = attr('op', [BooleanQuery, Expression])


class Query(UnaryRule):
    """The entry-point for the grammar.

    Find keyword is ignored as the current grammar is an augmentation of SPIRES and Google style syntaxes.
    It only serves for backward compatibility with SPIRES syntax.
    """
    grammar = [
        (omit(re.compile(r"(find|fin|fi|f)\s", re.IGNORECASE)), attr('op', Statement)),
        attr('op', Statement),
    ]
