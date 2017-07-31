# coding=utf-8
from ..ast import UnaryOp, Leaf, BinaryOp, ListOp

INDENTATION = 4


class ParseTreeFormatter(object):
    """Generates a tree-like representation of a parse tree."""

    @staticmethod
    def emit_tree_format(tree, verbose=False):
        """Returns a tree representation of a parse tree.

        Arguments:
            tree:           the parse tree whose tree representation is to be generated
            verbose (bool): if True prints the parse tree to be formatted

        Returns:
            str:  tree-like representation of the parse tree
        """
        if verbose:
            print("Converting: " + str(tree))
        ret_str = ParseTreeFormatter.__recursive_formatter(tree)
        return ret_str

    @staticmethod
    def __emit_symbol_at_level_str(symbol, level, is_last=False):
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

    @staticmethod
    def __recursive_formatter(node, level=-INDENTATION):
        new_level = INDENTATION + level

        if issubclass(type(node), Leaf):
            value = "" if not repr(node.value) or repr(node.value) == "None" \
                else node.__class__.__name__ + " {" + node.value.encode('utf-8') + "}"

            ret_str = ParseTreeFormatter.__emit_symbol_at_level_str(value, new_level) if value != "" else ""
        elif issubclass(type(node), unicode):
            value = "" if not repr(node) or repr(node) == "None" \
                else node.__class__.__name__ + " {" + node.encode('utf-8') + "}"

            ret_str = ParseTreeFormatter.__emit_symbol_at_level_str(value, new_level) if value != "" else ""
        else:
            ret_str = ParseTreeFormatter.__emit_symbol_at_level_str(node.__class__.__name__, new_level)
            if issubclass(type(node), UnaryOp):
                ret_str += ParseTreeFormatter.__recursive_formatter(node.op, new_level)
                if not node.op:
                    ret_str = ""

            elif issubclass(type(node), BinaryOp):
                try:
                    if node.bool_op:
                        ret_str = ParseTreeFormatter.__emit_symbol_at_level_str(
                            node.__class__.__name__ + " {" + node.bool_op + "}",
                            new_level
                        )
                except AttributeError:
                    pass
                ret_str += ParseTreeFormatter.__recursive_formatter(node.left, new_level)
                ret_str += ParseTreeFormatter.__recursive_formatter(node.right, new_level)

            elif issubclass(type(node), ListOp):
                try:
                    len(node.children)
                    for c in node.children:
                        ret_str += ParseTreeFormatter.__recursive_formatter(c, new_level)
                except TypeError:
                    ret_str += ParseTreeFormatter.__recursive_formatter(node.children, new_level)
                ret_str += ParseTreeFormatter.__emit_symbol_at_level_str("▆", new_level, True)

            elif not node:
                return ""
            else:
                raise TypeError("Unexpected base type: " + str(type(node)))

        return ret_str
