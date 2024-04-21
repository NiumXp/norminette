import pytest

from tests.utils import dict_to_pytest_param, tokens_from_source
from norminette.tree import (
    parse,
    Name,
    NameStatement,
)
from norminette.file import File


# def test_tree():
#     result = parse(File("<input>", "a; = 2;# /*oxi*/ ola (1)"))
#     print(result)

#     assert result == 1


@pytest.mark.parametrize("source, expected", dict_to_pytest_param({
    "Just name": ["a", "Name([Token('IDENTIFIER', (1, 1), value='a')])"],
    "Name between spaces and comments": [" \t/*asd*/ \t name /*ao*/\t", "Name([Token('SPACE', (1, 1)), Token('TAB', (1, 2)), Token('MULT_COMMENT', (1, 5), value='/*asd*/'), Token('SPACE', (1, 12)), Token('TAB', (1, 13)), Token('SPACE', (1, 17)), Token('IDENTIFIER', (1, 18), value='name'), Token('SPACE', (1, 22)), Token('MULT_COMMENT', (1, 23), value='/*ao*/'), Token('TAB', (1, 29))])"],
    "Literal number": ["1", "None"],
    "Number followed by name": ["1a", "None"],
    "Space before a name": [" _ref", "Name([Token('SPACE', (1, 1)), Token('IDENTIFIER', (1, 2), value='_ref')])"],
    "Space after a name": ["_ref ", "Name([Token('IDENTIFIER', (1, 1), value='_ref'), Token('SPACE', (1, 5))])"],
    "Empty source": ['', "None"],
}))
def test_Name_parse(source: str, expected: str):
    tokens = tokens_from_source(source)
    result = Name.parse(tokens)
    assert repr(result) == expected


@pytest.mark.parametrize("source, expected", dict_to_pytest_param({
    "Empty source": ['', "None"],
    "Literal statement": ["1;", "None"],
    "Empty statement": [";", "None"],
    "Empty statements": ["  ; ; ", "None"],
    "Statement with newline": ["ref\n;", "NameStatement(name=Name([Token('IDENTIFIER', (1, 1), value='ref'), Token('NEWLINE', (1, 4))]), column=Token('SEMI_COLON', (2, 1)))"],
    "Single statement without spaces": ["niumxp;", "NameStatement(name=Name([Token('IDENTIFIER', (1, 1), value='niumxp')]), column=Token('SEMI_COLON', (1, 7)))"],
    "Single statement with identation": ["\tniumxp;", "NameStatement(name=Name([Token('TAB', (1, 1)), Token('IDENTIFIER', (1, 5), value='niumxp')]), column=Token('SEMI_COLON', (1, 11)))"],
    "Single statement with end spaces": ["a ;", "NameStatement(name=Name([Token('IDENTIFIER', (1, 1), value='a'), Token('SPACE', (1, 2))]), column=Token('SEMI_COLON', (1, 3)))"],
    "Single statement between spaces": ["   a  ;   ", "NameStatement(name=Name([Token('SPACE', (1, 1)), Token('SPACE', (1, 2)), Token('SPACE', (1, 3)), Token('IDENTIFIER', (1, 4), value='a'), Token('SPACE', (1, 5)), Token('SPACE', (1, 6))]), column=Token('SEMI_COLON', (1, 7)))"],
}))
def test_NameStatement_parse(source: str, expected: str):
    tokens = tokens_from_source(source)
    result = NameStatement.parse(tokens)
    assert repr(result) == expected


@pytest.mark.skip
def test_parse():
    tokens = tokens_from_source("a.")
    result = parse(tokens)
    print(result)
    result = parse(tokens)
    print(result)
    assert False
