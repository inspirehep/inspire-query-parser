# coding=utf-8
from __future__ import print_function

import sys

from inspire_query_parser.utils.parse_tree_formatter import ParseTreeFormatter


class Colors(object):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


if sys.version_info[0] == 3:  # pragma: no cover (Python 2/3 specific code)
    string_types = str,
else:  # pragma: no cover (Python 2/3 specific code)
    string_types = basestring,


def print_query_and_parse_tree(query_str):
    print(Colors.OKBLUE + "Parsing: [" + query_str + "]" + Colors.ENDC)
    print(Colors.OKGREEN + ParseTreeFormatter.emit_tree_format(parse(query_str, Query)) + Colors.ENDC)
    print("————————————————————————————————————————————————————————————————————————————————")


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
