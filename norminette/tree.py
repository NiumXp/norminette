from __future__ import annotations

from typing import Optional, Union, Sequence, Callable
from dataclasses import dataclass

from norminette.file import File
from norminette.utils import max_loop_iterations
from norminette.exceptions import MaybeInfiniteLoop
from norminette.lexer import Lexer
from norminette.tokens import Tokens, Token
from norminette import matchers


class Node:
    pass


@dataclass
class Name(Node):
    tokens: Tokens

    def __repr__(self) -> str:
        return f"Name({self.tokens!r})"

    @classmethod
    def parse(cls, tokens: Tokens) -> Optional[Name]:
        matcher = matchers.IsToken(type="IDENTIFIER")
        matcher = matchers.Strip(matcher)
        if result := tokens.pop(matcher):
            return cls(result)
        return None


@dataclass
class NameStatement(Node):
    name: Name
    column: Token

    @classmethod
    def parse(cls, t: Tokens) -> Optional[NameStatement]:
        with t as tokens:
            if name := Name.parse(tokens):
                if column := tokens.pop("SEMI_COLON"):
                    return cls(name, column)
        return None


@dataclass
class Literal(Node):
    tokens: Tokens

    @classmethod
    def parse(cls, tokens: Tokens) -> Optional[Literal]:
        matcher = matchers.IsToken(type={"CONSTANT", "CHAR_CONSTANT", "STRING"})
        matcher = matchers.Strip(matcher)
        if result := tokens.pop(matcher):
            return cls(result)
        return None


@dataclass
class LiteralStatement(Node):
    literal: Literal
    column: Token

    @classmethod
    def parse(cls, t: Tokens) -> Optional[LiteralStatement]:
        with t as tokens:
            if literal := Literal.parse(tokens):
                if column := tokens.pop("SEMI_COLON"):
                    t.skip(tokens.steps)
                    return cls(literal, column)
        return None


@dataclass
class EmptyStatement(Node):
    tokens: Tokens

    @classmethod
    def parse(cls, tokens: Tokens) -> Optional[EmptyStatement]:
        matcher = matchers.IsToken(type="SEMI_COLON")
        matcher = matchers.Strip(matcher, only="left")
        if result := tokens.pop(matcher):
            return cls(result)
        return None


@dataclass
class FunctionCall(Node):
    def __init__(self, left: Name, nest: Tokens) -> None:
        self.left = left
        self.nest = nest

    def __repr__(self):
        return f"FunctionCall({self.left!r}, {self.nest!r})"

    @classmethod
    def parse(cls, t: Tokens) -> Optional[FunctionCall]:
        with t as tokens:
            matcher = matchers.IsToken(type={"SEMI_COLON", "NEWLINE"})
            matcher = matchers.Until(matcher, greedy=True)
            tokens = tokens.pop(matcher)
            if not tokens:
                return
            match = matchers.IsNest('(', ')')
            match = matchers.Strip(match)
            if nest := tokens.pop(match):
                t.skip(tokens.steps)
                return cls(name, nest)
        return None


class Assignation(Node):
    def __init__(self, left: Tokens, assign: Token, value: Tokens) -> None:
        self.left = left
        self.assign = assign
        self.value = value

    def __repr__(self) -> str:
        return f"Assignation({self.left!r}, {self.assign!r}, {self.value!r})"

    @classmethod
    def parse(cls, t: Tokens) -> Optional[Assignation]:
        with t as tokens:
            matcher = matchers.IsAssign()
            matcher = matchers.Until(matcher)
            left = tokens.pop(matcher)
            if not left:
                return
            assign = tokens.pop()
            t.skip(tokens.steps)
            return cls(left, assign, [])
        return


class PreProcessor(Node):
    def __init__(
        self,
        hash: Tokens,
        name: Optional[Name] = None,
        parameters: Optional[Tokens] = None,
        value: Optional[Tokens] = None,
    ) -> None:
        self.hash = hash
        self.name = name
        self.parameters = parameters
        self.value = value

    def __repr__(self) -> str:
        return f"PreProcessor({self.name!r}, {self.value!r})"

    def is_null(self) -> bool:
        return not self.name

    def is_multline(self) -> bool:
        # TODO
        ...

    @classmethod
    def parse(cls, t: Tokens) -> Optional[PreProcessor]:
        with t as tokens:
            matcher = matchers.IsToken(type="HASH")
            matcher = matchers.Strip(matcher)
            hash = tokens.pop(matcher)
            if not hash:
                return
            name = Name.parse(tokens)
            match = matchers.Until("NEWLINE", greedy=True)
            right = tokens.pop(match)
            return cls(hash, name, parameters=None, value=right)
        return None


class FunctionCallStatement(FunctionCall):
    pass


class Unrecognizable(Node):
    def __init__(self, tokens: Tokens) -> None:
        self.tokens = tokens

    def __repr__(self) -> str:
        return f"Unrecognizable({self.tokens!r})"


parse_functions = (
    NameStatement.parse,
    LiteralStatement.parse,
    Literal.parse,
    PreProcessor.parse,
    FunctionCall.parse,
    Assignation.parse,
    Name.parse,
)


def parse(
    it: Tokens,
    /,
    functions: Sequence[Callable[[Tokens], Optional[Node]]] = parse_functions,
) -> Optional[Node]:
    if isinstance(it, File):
        tokens = tuple(Lexer(it))
        tokens = Tokens(tokens)
    else:
        tokens = it
    with tokens as copy:
        poped = None
        for _ in range(max_loop_iterations):
            if copy.is_empty():
                break
            for parse_node in functions:
                if node := parse_node(copy):
                    if poped:
                        break
                    tokens.skip(copy.steps)
                    return node
            poped = copy.pop()
        else:
            raise MaybeInfiniteLoop()
    if tokens := tokens.pop(copy.steps):
        return Unrecognizable(tokens)
    return None
