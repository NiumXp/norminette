from typing import Dict, Any, List

import pytest
from _pytest.mark.structures import ParameterSet

from norminette.file import File
from norminette.lexer import Lexer
from norminette.tokens import Tokens


def lexer_from_source(source: str, /) -> Lexer:
    file = File("<file>", source)
    return Lexer(file)


def tokens_from_source(source: str, /) -> Tokens:
    lexer = lexer_from_source(source)
    tokens = tuple(lexer)
    tokens = Tokens(tokens)
    return tokens


def dict_to_pytest_param(data: Dict[str, List[Any]]) -> List[ParameterSet]:
    params: List[ParameterSet] = []
    for id, values in data.items():
        param = pytest.param(*values, id=id)
        params.append(param)
    return params
