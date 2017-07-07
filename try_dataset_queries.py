#!/usr/bin/env python
import re
import sys

from pypeg2 import parse

from inspire_query_parser.parser import Query
from inspire_query_parser.utils.utils import emit_tree_repr

unsupported = {"collection", "refersto", "citedby"}

if __name__ == '__main__':
    with open("queries.txt", "r") as input_file:
        queries_read = 0
        for line in input_file:

            try:
                t = parse(line, Query)
                # print(emit_tree_repr(t))

                queries_read += 1
            except (ValueError, SyntaxError):
                if not unsupported.intersection(set(re.split('[ :]', line))):
                    sys.stderr.write(line)
