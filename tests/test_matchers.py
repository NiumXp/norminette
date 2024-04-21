from typing import List, Dict, Any

import pytest

from norminette import matchers
from norminette.lexer import Token as T
from norminette.tokens import Tokens
from tests.utils import dict_to_pytest_param


@pytest.mark.parametrize("raw_tokens, params, expected", dict_to_pytest_param({
    "Two spaces with default iterations (1)": [[T("SPACE", (1, 1)), T("SPACE", (1, 1))], {"type": "SPACE"}, 1],
    "Two spaces with iterations 0 (inf)": [[
        T("SPACE", (1, 1)),
        T("SPACE", (1, 2)),
    ], {"type": "SPACE", "iterations": 0}, 2],
    "Empty tokens": [[], {"type": "NULL"}, 0],
    "Multiple types with one iteration": [[
        T("SPACE", (1, 1)),
        T("TAB", (1, 2)),
        T("SPACE", (1, 3)),
    ], {"type": ["SPACE", "TAB"]}, 1],
    "Multiple types with specific iteration": [[
        T("SPACE", (1, 1)),
        T("TAB", (1, 2)),
        T("SPACE", (1, 3)),
        T("AND", (1, 4)),
    ], {"type": ["SPACE", "TAB"], "iterations": 3}, 3],
}))
def test_IsToken(raw_tokens: List[T], params: Dict[str, Any], expected: int):
    tokens = Tokens(raw_tokens)
    matcher = matchers.IsToken(**params)
    matched = matcher(tokens)
    assert matched == expected


@pytest.mark.parametrize("value", [
    False,
    True,
    1,
    "just to check string address",
    object(),
])
def test_Echo(value: Any):
    tokens = Tokens([T("PLUS", (1, 1))])
    matcher = matchers.Echo(value)
    matched = matcher(tokens)
    assert matched is value
