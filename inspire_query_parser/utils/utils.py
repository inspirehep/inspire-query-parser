# coding=utf-8
from __future__ import print_function

import sys

from ..ast import UnaryOp, Leaf, BinaryOp, ListOp

INDENTATION = 4


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


def emit_symbol_at_level_str(symbol, level, is_last=False):
    def emit_prefix():
        ret_str = ""
        prefix = ("└── " if is_last else "├── ") if level != 0 else ""
        for i in range(level-INDENTATION):
            if i % INDENTATION == 0:
                ret_str += "│"
            else:
                ret_str += " "
        return ret_str + prefix
    return emit_prefix() + str(symbol) + "\n"


def recursive_printer(node, level=-INDENTATION):
    new_level = INDENTATION + level

    if issubclass(type(node), Leaf):
        value = "" if not repr(node.value) or repr(node.value) == "None" \
            else node.__class__.__name__ + " {" + node.value.encode('utf-8') + "}"

        ret_str = emit_symbol_at_level_str(value, new_level) if value != "" else ""
    elif issubclass(type(node), unicode):
        value = "" if not repr(node) or repr(node) == "None" \
            else node.__class__.__name__ + " {" + node.encode('utf-8') + "}"

        ret_str = emit_symbol_at_level_str(value, new_level) if value != "" else ""
    else:
        ret_str = emit_symbol_at_level_str(node.__class__.__name__, new_level)
        if issubclass(type(node), UnaryOp):
            ret_str += recursive_printer(node.op, new_level)
            if not node.op:
                ret_str = ""

        elif issubclass(type(node), BinaryOp):
            try:
                if node.bool_op:
                    ret_str = emit_symbol_at_level_str(
                        node.__class__.__name__ + " {" + node.bool_op + "}",
                        new_level
                    )
            except AttributeError:
                pass
            ret_str += recursive_printer(node.left, new_level)
            ret_str += recursive_printer(node.right, new_level)

        elif issubclass(type(node), ListOp):
            try:
                len(node.children)
                for c in node.children:
                    ret_str += recursive_printer(c, new_level)
            except TypeError:
                ret_str += recursive_printer(node.children, new_level)
            ret_str += emit_symbol_at_level_str("▆", new_level, True)

        elif not node:
            return ""
        else:
            raise TypeError("Unexpected base type: " + str(type(node)))

    return ret_str


def emit_tree_repr(tree, verbose=False):
    if verbose:
        print("Converting: " + str(tree))
    ret_str = recursive_printer(tree)
    return ret_str

