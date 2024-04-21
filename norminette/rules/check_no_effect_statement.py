from norminette import tree
from norminette.context import Context
from norminette.rules import Rule, Check
from norminette.errors import Error, Highlight


class CheckNoEffectStatement(Rule, Check):
    runs_on = "traverse",

    def run(self, context: Context) -> None:
        print("CheckNoEffectStatement")
        assert context.tree
        nodes = context.tree.copy()
        while nodes:
            node = nodes.pop()
            if isinstance(node, tree.LiteralStatement):
                error = Error("NO_EFFECT", "This statement can be removed since it has no effect")
                first = node.literal.tokens[0]
                lineno, column = first.pos
                for token in node.literal.tokens:
                    if token.pos[0] != lineno:
                        break
                    length = token.pos[1] - column + (first.length or 1)
                error.add_highlight(lineno, column, length or 1)
                context.errors.add(error)
