from pypeg2 import Parser


class StatefulParser(Parser):
    """Defines a stateful parser for encapsulating parsing flags functionality.

    Attributes:
        parsing_parenthesized_terminal (bool):
            Signifies whether the parser is trying to identify a parenthesized terminal. Used for disabling the
            terminals parsing related check "stop on DSL keyword", for allowing to parse symbols such as "+", "-" which
            are also DSL keywords ('and' and 'not' respectively).

        parsing_parenthesized_simple_values_expression (bool):
            Signifies whether we are parsing a parenthesized simple values expression. Used for disabling the simple
            values parsing related check "stop on INSPIRE keyword", for allowing parsing more expressions and not
            restrict the input accepted by the parser.
    """

    def __init__(self):
        super(StatefulParser, self).__init__()
        self.parsing_parenthesized_terminal = False
        self.parsing_parenthesized_simple_values_expression = False


def parse(text, thing):
    """Wrapper method for creating a StatefulParser and then parsing text with thing grammar.


    Raises:
        SyntaxError: if text does not match the grammar in thing
        ValueError:  if input does not match types
        TypeError:   if output classes have wrong syntax for __init__()
        GrammarTypeError:   if grammar contains an object of unknown type
        GrammarValueError:  if grammar contains an illegal cardinality value
    """
    parser = StatefulParser()
    t, r = parser.parse(text, thing)
    if t:
        raise parser.last_error
    return r
