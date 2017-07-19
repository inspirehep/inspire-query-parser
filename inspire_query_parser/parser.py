# coding=utf-8
from __future__ import unicode_literals, print_function

from pypeg2 import attr, Keyword, Literal, omit, optional, re, K, Enum, contiguous, maybe_some, some, GrammarValueError, \
    whitespace

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
        """Checks if terminal token is a keyword after lower-casing it."""
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
    """Serves as the possible case for a boolean operator."""
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
# ########################


# #### Lowest level operators #####
class InspireKeyword(LeafRule):
    grammar = re.compile(r"({0})\b".format("|".join(INSPIRE_PARSER_KEYWORDS.keys())))

    def __init__(self, value):
        self.value = INSPIRE_PARSER_KEYWORDS[value]


class Terminal(LeafRule):
    """Represents terminal symbols that are not keywords.

    Some examples include: na61/shine, e-10, SU(2).
    Terminals separation happens with these " ", ",", ".", ":", "，" characters.
    """
    regex = re.compile(r"[*]?(\w+(([-/.'*]\w+)|(\((\w+|\d+)\)))*)[*]?", re.UNICODE)

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

            result = text[len(m.group(0)):], cls(m.group(0))
        else:
            result = text, SyntaxError("expecting match on " + repr(cls.regex))
        return result


class SimpleValue(ListRule):
    """Represents terminals as plaintext.

    E.g. title top cross section.
    """
    grammar = attr('children', contiguous(some(Terminal, maybe_some([" ", ",", ".", ":", "，"]))))


class ComplexValue(LeafRule):
    """Accepting value with either single/double quotes or a regex value (/^.../$).

    These values have special and different meaning for the later phases of parsing:
      * Single quotes: partial text matching (text is analyzed before searched)
      * Double quotes: exact text matching
      * Regex: regex searches

    E.g. t 'Millisecond pulsar velocities'.

    This makes no difference for the parser and will be handled at a later parsing phase.
    """
    grammar = attr('value', re.compile(r"((/(\^)?.+(\$)?/)|('[^']*')|(\"[^\"]*\"))")),


class GreaterThanOp(UnaryRule):
    """Greater than operator.

    Supports queries like author-count > 2000 or date after 10-2000.
    """
    grammar = omit(re.compile(r"after|>", re.IGNORECASE)), attr('op', SimpleValue)


class GreaterEqualOp(UnaryRule):
    """Greater than or Equal to operator.

    Supports queries like date >= 10-2000 or topcite 200+.
    """
    grammar = [
        (omit(Literal(">=")), attr('op', SimpleValue)),
        (attr('op', Terminal), omit(Literal("+"))),
    ]


class LessThanOp(UnaryRule):
    """Less than operator.

    Supports queries like author-count < 100 or date before 1984.
    """
    grammar = omit(re.compile(r"before|<", re.IGNORECASE)), attr('op', SimpleValue)


class LessEqualOp(UnaryRule):
    """Less than or Equal to operator.

    Supports queries like date <= 10-2000 or author-count 100-.
    """
    grammar = [
        (omit(Literal("<=")), attr('op', SimpleValue)),
        (attr('op', Terminal), omit(Literal("-")))
    ]


class RangeOp(BinaryRule):
    """Range operator mixing any type of values.

    E.g.    muon decay year:1983->1992
            author:"Ellis, J"->"Ellis, Qqq"
            author:"Ellis, J"->Ellis, M

    The non symmetrical type of values will be handled at a later phase.
    """
    grammar = attr('left', [ComplexValue, SimpleValue]), omit(Literal("->")), attr('right', [ComplexValue, SimpleValue])


class Value(UnaryRule):
    """Generic rule for all kinds of phrases recognized.

    Serves as an encapsulation of the listed rules.
    """
    grammar = attr('op', [
        (omit(Literal("=")), SimpleValue),
        RangeOp,
        GreaterEqualOp,
        LessEqualOp,
        GreaterThanOp,
        LessThanOp,
        ComplexValue,
        SimpleValue,
    ])
########################


class InvenioKeywordQuery(BinaryRule):
    """Keyword queries with colon separator (i.e. Invenio style).

    There needs to be a distinction between Invenio and SPIRES keyword queries, so as the parser is able to recognize
    any terminal as keyword for the former ones.
    E.g. author: ellis, title: boson, or unknown_keyword: foo.
    """
    grammar = attr('left', [InspireKeyword, Terminal]), omit(':'), attr('right', Value)


class SpiresKeywordQuery(BinaryRule):
    """Keyword queries with space separator (i.e. Spires style)."""
    grammar = attr('left', InspireKeyword), attr('right', Value)


class SimpleQuery(UnaryRule):
    """Query basic units.

    These are comprised of metadata queries, keywords and value queries.
    """
    grammar = attr('op', [
        InvenioKeywordQuery,
        SpiresKeywordQuery,
        Value,
    ])


class Statement(UnaryRule):
    """The most generic query component.

    Supports queries chaining, see its grammar for more information.
    """
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
    """Nested Keyword queries.

    E.g. citedby:author:hui and refersto:author:witten
    """
    pass


Expression.grammar = attr('op', [
    NotQuery,
    NestedKeywordQuery,
    ParenthesizedQuery,
    SimpleQuery,
])


NestedKeywordQuery.grammar = \
    attr('left', [
        re.compile('refersto', re.IGNORECASE),
        re.compile('citedbyx', re.IGNORECASE),
        re.compile('citedby', re.IGNORECASE),
    ]), \
    optional(omit(":")), \
    attr('right', Expression)


# FIXME Implicit And should happen only between KeywordColonQueries!
class BooleanQuery(BinaryRule):
    """Represents boolean query as a binary rule.

    Attributes:
        bool_op (str): Representation of the actual boolean operator.
            If its value is None at creation time, this signifies an Implicit And. From that point on, this attribute
            will contain the value from :attr:`BooleanOperator.AND` field.
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


class EmptyQuery(LeafRule):
    grammar = omit(optional(whitespace)), attr('value', None)


class Query(UnaryRule):
    """The entry-point for the grammar.

    Find keyword is ignored as the current grammar is an augmentation of SPIRES and Google style syntaxes.
    It only serves for backward compatibility with SPIRES syntax.
    """
    grammar = [
        (omit(re.compile(r"(find|fin|fi|f)\s", re.IGNORECASE)), attr('op', Statement)),
        attr('op', Statement),
        attr('op', EmptyQuery),
    ]
