from __future__ import annotations

from typing import Optional

from norminette.tokens import Tokens
from norminette.matchers import (
    Until,
    IsBracesNest,
    IsLiteral,
)


class Node:
    @classmethod
    def parse(cls, tokens: Tokens) -> Optional[Node]:
        ...


class Literal(Node):
    @classmethod
    def parse(cls, tokens: Tokens) -> Optional[Literal]:
        if result := tokens.pop(IsLiteral()):
            return cls(result)
        return None


class Expression(Node):
    @classmethod
    def parse(cls, tokens: Tokens) -> Optional[Expression]:
        ...


class If(Node):
    @classmethod
    def parse(cls, tokens: Tokens) -> Optional[If]:
        if not (result := tokens.pop("IF")):
            return None
        if not (condition := Expression.parse(tokens)):
            return None
        if not (block := Block.parse(tokens)):
            return None
        return cls(condition, block)


class Block(Node):
    @classmethod
    def parse(cls, tokens: Tokens) -> Optional[Block]:
        if result := tokens.pop(IsBracesNest()):
            return cls(result)
        return None
