from __future__ import annotations

from typing import TYPE_CHECKING, List, Any, Union, Optional, Tuple

if TYPE_CHECKING:
    from norminette.rules import Rule


class History:
    def __init__(self, value: Optional[List[Rule]] = None, /) -> None:
        if value is None:
            value = []
        self._inner = value

    def append(self, value: Rule) -> None:
        self._inner.append(value)

    def __len__(self) -> int:
        return len(self._inner)

    def __getitem__(self, item: Any) -> Union[History, Rule]:
        if isinstance(item, int):
            return self._inner[item]
        if isinstance(item, slice):
            return History(self._inner[item])
        raise TypeError(...)

    def find(self, matcher: str, /) -> Optional[Tuple[int, Rule]]:
        for index, rule in enumerate(self._inner):
            if rule == matcher:
                return index, rule
        return None
