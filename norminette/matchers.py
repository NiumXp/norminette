from __future__ import annotations

import itertools
from typing import (
    TYPE_CHECKING,
    Callable,
    Container,
    Iterable,
    Optional,
    Literal,
    Union,
    TypeVar,
    Generic,
    overload,
)
from typing_extensions import TypeAlias

from norminette.exceptions import MaybeInfiniteLoop
from norminette.lexer.dictionary import brackets
from norminette.utils import max_loop_iterations

if TYPE_CHECKING:
    from norminette.tokens import Tokens

T = TypeVar('T')
G = TypeVar('G', bool, int)

Matcher: TypeAlias = Callable[["Tokens"], T]


class IsToken:
    types: Container[str]

    @overload
    def __init__(self, *, type: str, iterations: int = 1) -> None:
        """
        """
        ...

    @overload
    def __init__(self, *, type: Container[str], iterations: int = 1) -> None:
        """
        """
        ...

    def __init__(self, *, type: Container[str], iterations: int = 1) -> None:
        if isinstance(type, str):
            type = type,
        if isinstance(type, Iterable):
            type = frozenset(type)
        self.types = type
        self.iterations = abs(iterations)

    def __repr__(self) -> str:
        return f"IsToken(type={self.types!r})"

    def __call__(self, tokens: Tokens) -> int:
        if self.iterations == 0:
            slice = tokens
        else:
            slice = itertools.islice(tokens, self.iterations)
            slice = tuple(slice)
        if slice and all(token.type in self.types for token in slice):
            return self.iterations or len(tokens)
        return 0


class IsNest:
    opening: Matcher[int]
    closing: Matcher[int]

    def __init__(
        self,
        opening: Union[Matcher[int], str],
        closing: Union[Matcher[int], str],
    ) -> None:
        if isinstance(opening, str):
            opening = brackets.get(opening, opening)
            opening = IsToken(type=opening)
        if isinstance(closing, str):
            closing = brackets.get(closing, closing)
            closing = IsToken(type=closing)
        self.opening = opening
        self.closing = closing

    def __call__(self, tokens: Tokens) -> int:
        if steps := self.opening(tokens):
            tokens.skip(steps)
            tokens.skip(Until(self.closing, exclusive=False))
            return tokens.steps
        return 0


class IsWhitespace(IsToken):
    types = {"SPACE", "TAB", "MULT_COMMENT", "NEWLINE"}

    def __init__(self, iterations: int = 1):
        self.iterations = iterations


class IsAssign(IsToken):
    types = {
        "RIGHT_ASSIGN",
        "LEFT_ASSIGN",
        "ADD_ASSIGN",
        "SUB_ASSIGN",
        "MUL_ASSIGN",
        "DIV_ASSIGN",
        "MOD_ASSIGN",
        "AND_ASSIGN",
        "XOR_ASSIGN",
        "OR_ASSIGN",
        "LESS_OR_EQUAL",
        "GREATER_OR_EQUAL",
        "EQUALS",
        "NOT_EQUAL",
        "ASSIGN",
    }

    def __init__(self, iterations: int = 1):
        self.iterations = iterations


class Echo(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value

    def __call__(self, tokens: Tokens) -> T:
        return self.value


class While:
    def __init__(self, matcher: Union[Matcher[int], str], /) -> None:
        if isinstance(matcher, str):
            matcher = IsToken(type=matcher)
        self.matcher = matcher

    def __call__(self, tokens: Tokens) -> int:
        for _ in range(max_loop_iterations):
            result = self.matcher(tokens)
            if not result:
                return tokens.steps
            tokens.skip(result)
        raise MaybeInfiniteLoop()


class Until:
    def __init__(
        self,
        matcher: Union[Matcher[int], str],
        /,
        exclusive: bool = True,
        greedy: bool = False,
    ) -> None:
        r"""
        If `exclusive` is `False`, the `matcher` will be skiped too. The
        `Until("NEWLINE", exclusive=False)` with `"   \n!"` as tokens will
        match all spaces and the newline, resulting only the `!` as tokens.

        If `greedy` is `True` and `matcher` does not match, it returns all
        tokens. The `Until("NEWLINE", greedy=True)` will be like "everthing
        before a newline or EOF".
        """
        if isinstance(matcher, str):
            matcher = IsToken(type=matcher)
        self.matcher = matcher
        self.exclusive = exclusive
        self.greedy = greedy

    def __call__(self, tokens: Tokens) -> int:
        for _ in range(max_loop_iterations):
            if result := self.matcher(tokens):
                break
            if tokens.skip(1).is_empty():
                if not self.greedy:
                    return 0
                break
        else:
            raise MaybeInfiniteLoop()
        if not self.exclusive:
            tokens.skip(result)
        return tokens.steps


class Strip:
    def __init__(
        self,
        matcher: Matcher[int],
        striper: Matcher[int] = IsWhitespace(),
        only: Optional[Literal["left", "right"]] = None,
    ) -> None:
        if not isinstance(While, Until):
            striper = While(striper)
        self.matcher = matcher
        self.striper = striper
        self.only = only

    def __call__(self, tokens: Tokens) -> int:
        if self.only != "right":
            tokens.skip(self.striper)
        if not tokens.pop(self.matcher):
            return 0
        if self.only != "left":
            tokens.skip(self.striper)
        return tokens.steps
