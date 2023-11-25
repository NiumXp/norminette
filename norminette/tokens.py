from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence, Optional, Any, Union

from norminette.lexer.tokens import Token


class Matcher(ABC):
    @staticmethod
    def _parse(val):
        if isinstance(val, Matcher):
            return val
        if isinstance(val, str):
            return Exact(val)
        if isinstance(val, (set, tuple, list)):
            return In(val)
        raise TypeError("not able to parse", type(val))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({', '.join(map(repr, self.__dict__.values()))})"

    @abstractmethod
    def perform(self, tokens: Tokens) -> Optional[Tokens]:
        ...


class Exact(Matcher):
    def __init__(self, type: str, value: Optional[Any] = None) -> None:
        self.type = type
        self.value = value

    def perform(self, tokens: Tokens) -> Optional[Tokens]:
        if self.type == tokens._current.type:
            return tokens.copy().shrink(length=1)
        return None


class In(Matcher):
    def __init__(self, items: Sequence[str]) -> None:
        self.items = items

    def perform(self, tokens: Tokens) -> bool:
        if tokens._current.type in self.items:
            return tokens.copy().shrink(length=1)
        return None


class Or(Matcher):
    def __init__(self, *matchers: Matcher) -> None:
        self.matchers = matchers

    def perform(self, tokens: Tokens) -> Optional[Tokens]:
        for match in self.matchers:
            if result := match.perform(tokens):
                return result
        return None


class And(Matcher):
    def __init__(self, *matchers: Matcher) -> None:
        self.matchers = matchers

    def perform(self, tokens: Tokens) -> Optional[Tokens]:
        length = 0
        for matcher in self.matchers:
            if result := matcher.perform(tokens):
                length = len(result)
            else:
                return None
        return tokens.copy().shrink(length=length)


class Tokens:
    def __init__(
        self,
        items: Sequence[Token] = (),
        *,
        start: Optional[int] = None,
        end: Optional[int] = None,
    ) -> None:
        self._items = items
        self._start = start or 0
        self._end = end if end is not None else len(items)

    def copy(self, **kwargs):
        instance = Tokens()
        for name, value in self.__dict__.items():
            setattr(instance, name, kwargs.pop(name, value))
        return instance

    def is_empty(self) -> bool:
        return len(self) == 0

    @property
    def _range(self) -> range:
        return range(self._start, self._end)

    @property
    def _current(self) -> Token:
        return self._items[self._start]

    def __repr__(self) -> str:
        return '[' + ", ".join(map(repr, self)) + ']'

    def __len__(self) -> int:
        return min(self._end - self._start, len(self._items))

    def __iter__(self):
        for index in self._range:
            yield self._items[index]

    def __getitem__(self, item: Any):
        if isinstance(item, int):
            if item not in self._range:
                raise IndexError("index out of range")
            assert item > 0, "not implemented negative indexes"
            return self._items[item]
        raise Exception("not implemented")

    def shrink(self, length: Optional[int] = None):
        if length is not None:
            self._end = min(self._start + length, len(self))
        return self

    def skip(self, val: Union[int, Matcher, Sequence[str]], /):
        if isinstance(val, Matcher):
            val = len(val.perform(self) or '')
        if isinstance(val, int):
            self._start += min(val, self._end)
            return self
        # if isinstance(val, str):
        #     val = val,
        # for index in self._range:
        #     if self[index].type not in val:
        #         break
        # self._start += index - self._start
        # return self

    def back(self, val: Union[int, Sequence[str]], /):
        if isinstance(val, int):
            self._start = max(self._start - val, 0)
            return self
        # if isinstance(val, str):
        #     val = val,
        # for index in self._range:
        #     if self[index].type not in val:
        #         break
        # self._start -= index - self._start
        # return self

    def check(self, val, /) -> bool:
        matcher = Matcher._parse(val)
        return matcher.perform(self)

    def skip_while(self, val):
        while self._start < self._end and self.check(val):
            self._start += 1
        return self

    def skip_ws(self, *, newline: bool = False):
        return self.skip_while(("SPACE", "TAB"))
    skip_whitespace = skip_ws


l = [
    Token("TAB", (1, 4)),
    Token("SPACE", (1, 1)),
    Token("SPACE", (1, 2)),
    Token("IDENTIFIER", (1, 3), "void"),
    Token("TAB", (1, 4)),
    Token("TAB", (1, 5)),
    Token("SPACE", (1, 6)),
    Token("IDENTIFIER", (1, 7), "main"),
]
t = Tokens(l)
print(t)
t.skip(Or(Exact("SPACE"), Exact("TAB")))
print(t)
# t.skip_ws()
# t.skip(1)
# t.skip_ws()
# t.back(100000)
# print(t)
