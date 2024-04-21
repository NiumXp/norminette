from __future__ import annotations

from typing import (
    TypeVar,
    Sequence,
    Iterable,
    Tuple,
    Union,
    Sized,
    Optional,
    overload,
    Any,
)
from typing_extensions import Self

from norminette import matchers
from norminette.matchers import Matcher
from norminette.lexer import Token

T = TypeVar('T', bound=str)


class Interval:
    __slots__ = ("_a", "_b", "_max", "_frozen", "_values")

    def __init__(self, a: int, b: int, *, max: int, frozen: bool = False) -> None:
        if a > (b := min(b, max)):
            raise ValueError("'a' can't be greater than 'b'")
        self._a = a
        self._b = b
        self._max = max
        self._frozen = frozen
        self._values = (a, b)

    @property
    def steps(self) -> int:
        return self._a - self._values[0]

    def __repr__(self) -> str:
        return f"Interval({self._a}, {self._b}, max={self._max})"

    @classmethod
    def from_sized(cls, sized: Sized, /) -> Interval:
        size = len(sized)
        return cls(0, size, max=size)

    def __len__(self) -> int:
        return self._b - self._a

    def __add__(self, value: Tuple[Optional[int], Optional[int]]) -> Interval:
        a, b = value
        interval = self.copy()
        interval.b += self._b if b is None else b
        interval.a += a or 0
        interval._frozen = self._frozen
        return interval

    def __contains__(self, item: int) -> bool:
        return self._a <= item < self._b

    @overload
    def __getitem__(self, item: int) -> int:
        """Translates the relative index `item` to absolute index using `.a`.
        """
        ...

    @overload
    def __getitem__(self, item: slice) -> Interval:
        """
        """
        ...

    def __getitem__(self, item: Union[int, slice]) -> Union[int, Interval]:
        if isinstance(item, slice):
            interval = self.copy()
            interval.b = 0  # Force interval to be closed, it means b = a
            start = item.start or 0
            stop = self._max if item.stop is None else item.stop
            return interval + (start, max(stop, start))
        if (index := self._a + item) not in self:
            raise IndexError("index out of interval")
        return index

    def copy(self) -> Interval:
        return Interval(self._a, self._b, max=self._max)

    @property
    def a(self) -> int:
        return self._a

    @a.setter
    def a(self, value: int) -> None:
        if self._frozen:
            raise AttributeError("You can't set this attribute")
        self._a = min(value, self._b)

    @property
    def b(self) -> int:
        return self._b

    @b.setter
    def b(self, value: Optional[int]) -> None:
        if self._frozen:
            raise AttributeError("You can't set this attribute")
        if value is None:
            self._b = self._max
        else:
            self._b = min(max(self._a, value), self._max)


class Tokens(Iterable[Token], Sized):
    __slots__ = (
        "_inner",
        "_interval",
        "_steps",
    )

    def __init__(self, tokens: Sequence[Token], interval: Optional[Interval] = None) -> None:
        if interval is None:
            interval = Interval.from_sized(tokens)
        self._inner = tokens
        self._interval = interval

    @property
    def steps(self) -> int:
        return self._interval.steps

    def __repr__(self) -> str:
        return '[' + ", ".join(map(repr, self)) + ']'  # type: ignore

    def __len__(self) -> int:
        return len(self._interval)

    @overload
    def __getitem__(self, item: int) -> Token: ...
    @overload
    def __getitem__(self, item: slice) -> Tokens: ...

    def __getitem__(self, item: Union[int, slice]) -> Union[Token, Tokens]:
        if isinstance(item, int):
            return self._inner[self._interval[item]]
        return Tokens(self._inner, self._interval[item])

    def __iter__(self):
        for index in self._interval:
            yield self._inner[index]

    def __enter__(self) -> Tokens:
        return self.copy()

    def __exit__(self, *_: Any) -> None:
        return

    def copy(self) -> Tokens:
        return Tokens(self._inner, self._interval.copy())

    @overload
    def pop(self, /) -> Optional[Token]: ...
    @overload
    def pop(self, match: str, /) -> Optional[Token]: ...
    @overload
    def pop(self, match: int, /) -> Optional[Tokens]: ...
    @overload
    def pop(self, match: Matcher[int], /) -> Optional[Tokens]: ...

    def pop(self, match: Optional[Union[Matcher[int], str, int]] = None, /) -> Optional[Union[Token, Tokens]]:
        if self.is_empty():
            return
        if match is None:
            match = self.current.type
        if isinstance(match, int):
            tokens = self[:match]
            self._interval.a += match
            return tokens
        if isinstance(match, str):
            if (token := self.current).type == match:
                self._interval.a += 1
                return token
            return None
        with self as tokens:
            steps = match(tokens)
        if not steps:
            return
        tokens = self[:steps]
        self._interval.a += steps
        return tokens

    def is_empty(self):
        return len(self) == 0

    @property
    def current(self) -> Token:
        return self._inner[self._interval.a]

    # def count(  # type: ignore
    #     self,
    #     match: Union[Matcher[int], str],
    #     strategy: Literal["all", "while", "until"] = "all",
    # ) -> int:
    #     if isinstance(match, str):
    #         match = matchers.IsToken(type=match)
    #     matches = 0
    #     for token in self:
    #         matched = match(token)
    #         if strategy == "all" and not matched:
    #             continue
    #         if strategy == "while" and not matched:
    #             break
    #         if strategy == "until" and matched:
    #             break
    #         matches += 1
    #     return matches

    @overload
    def skip(self, /) -> Self:
        """Skip the current token.

        Alias for `skip(1)`.
        """
        ...

    @overload
    def skip(self, match: int, /) -> Self:
        """Skip `match` tokens.

        Alias for `matcher.Echo(match)`.
        """
        ...

    @overload
    def skip(self, match: str, /) -> Self:
        """Skip the current token if `.type` is `match`.

        Alias for `matchers.IsToken(type=match)`.
        """
        ...

    @overload
    def skip(self, match: Matcher[int], /) -> Self:
        """Apply `match` to tokens to know the amount of tokens to skip.

        Note that `match` is used only once, but you can use `matchers.While(match)` or `matchers.Until(match)`.
        """
        ...

    def skip(self, match: Optional[Union[Matcher[int], str, int]] = None) -> Self:
        if match is None:
            match = matchers.Echo(1)
        elif isinstance(match, str):
            match = matchers.IsToken(type=match)
        elif isinstance(match, int):
            match = matchers.Echo(abs(match))
        with self as tokens:
            self._interval.a += match(tokens)
        return self

    def skip_whitespace(self) -> Self:
        matcher = matchers.IsWhitespace()
        matcher = matchers.While(matcher)
        return self.skip(matcher)

    # @overload
    # def startswith(self, match: str) -> bool: ...
    # @overload
    # def startswith(self, match: List[str]) -> bool: ...
    # # @overload
    # # def startswith(self, match: Matcher[Stateful]) -> bool: ...

    # def startswith(
    #     self,
    #     match: Union[str, List[str]],
    # ) -> bool:
    #     if self.is_empty():
    #         return False
    #     if not isinstance(match, list):
    #         match = [match]
    #     for value in match:
    #         matcher = matchers.IsToken(type=value)
    #         if not matcher(self):
    #             break
    #     else:
    #         return True
    #     return False
