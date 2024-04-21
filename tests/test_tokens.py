import textwrap

import pytest

from norminette.file import File
from norminette.lexer import Lexer
from norminette.tokens import Tokens, Token as T, Interval
from norminette import matchers
from tests.utils import dict_to_pytest_param


@pytest.fixture()
def tokens():
    source = """
    int\tmain(void)
    {
        return 1;
    }
    """
    source = textwrap.dedent(source)
    source = source.strip('\n')
    source += '\n'

    file = File("<file.c>", source)
    lexer = Lexer(file)
    tokens = tuple(lexer)

    yield Tokens(tokens)


def test_interval_constructor():
    with pytest.raises(ValueError):
        Interval(3, 2, max=10)
    with pytest.raises(ValueError):
        Interval(2, 2, max=0)
    assert repr(Interval(1, 2, max=3)) == "Interval(1, 2, max=3)"
    assert repr(Interval(1, 2, max=1)) == "Interval(1, 1, max=1)"


def test_interval_getitem_using_int():
    interval = Interval(6, 15, max=20)

    assert interval[0] == 6
    assert interval[1] == 7
    assert interval[8] == 14
    with pytest.raises(IndexError):
        interval[17]
    with pytest.raises(IndexError):
        interval[len(interval)]


def test_interval_getitem_using_slice():
    interval = Interval(6, 15, max=20)

    assert repr(interval[0:1]) == f"Interval(6, {6 + 1}, max=20)"
    assert repr(interval[2:3]) == f"Interval({6 + 2}, {6 + 3}, max=20)"
    assert repr(interval[5:]) == f"Interval({6 + 5}, 20, max=20)"
    assert repr(interval[5:2]) == f"Interval({6 + 5}, {6 + 5}, max=20)"
    assert repr(interval[5:0]) == f"Interval({6 + 5}, {6 + 5}, max=20)"
    assert repr(interval[:5]) == f"Interval(6, {6 + 5}, max=20)"
    assert repr(interval[:]) == "Interval(6, 20, max=20)"
    assert repr(interval[:100]) == "Interval(6, 20, max=20)"
    assert repr(interval[100:]) == "Interval(20, 20, max=20)"


def test_interval_add():
    assert repr(Interval(1, 10, max=10) + (0, 0)) == "Interval(1, 10, max=10)"
    assert repr(Interval(1, 10, max=10) + (0, 5)) == "Interval(1, 10, max=10)"
    assert repr(Interval(1, 10, max=15) + (0, 5)) == "Interval(1, 15, max=15)"
    assert repr(Interval(1, 10, max=15) + (3, 0)) == "Interval(4, 10, max=15)"
    assert repr(Interval(1, 10, max=15) + (20, 0)) == "Interval(10, 10, max=15)"
    assert repr(Interval(1, 10, max=15) + (0, 20)) == "Interval(1, 15, max=15)"
    assert repr(Interval(1, 10, max=15) + (2, 2)) == "Interval(3, 12, max=15)"
    assert repr(Interval(1, 10, max=15) + (None, 1)) == "Interval(1, 11, max=15)"
    assert repr(Interval(1, 10, max=15) + (1, None)) == "Interval(2, 15, max=15)"
    assert repr(Interval(1, 10, max=15) + (None, None)) == "Interval(1, 15, max=15)"


@pytest.mark.parametrize("interval, expected", [
    [Interval(1, 1, max=1), "Interval(1, 1, max=1)"],
    [Interval(1, 2, max=1), "Interval(1, 1, max=1)"],
    [Interval(10, 22, max=30), "Interval(10, 22, max=30)"],
    [Interval(4, 15, max=15), "Interval(4, 15, max=15)"],
])
def test_interval_repr(interval: Interval, expected: str):
    assert repr(interval) == expected


@pytest.mark.parametrize("expected, interval", dict_to_pytest_param({
    "Large interval": [10, Interval(0, 10, max=10)],
    "Closed interval": [0, Interval(2, 2, max=10)],
    "One number interval": [1, Interval(1, 2, max=2)],
}))
def test_interval_len(expected: int, interval: Interval):
    assert len(interval) == expected


@pytest.mark.parametrize("interval, element, expected", dict_to_pytest_param({
    "Element in first position": [Interval(5, 10, max=10), 5, True],
    "Element in last position": [Interval(1, 4, max=10), 3, True],
    "Element in last position (over interval)": [Interval(1, 4, max=10), 4, False],
    "Element in any position": [Interval(7, 15, max=20), 9, True],
    "Element before first position": [Interval(2, 5, max=5), 1, False],
    "Element after last position": [Interval(6, 9, max=12), 10, False],
    "No element in closed interval": [Interval(2, 2, max=5), 2, False],
}))
def test_interval_in(interval: Interval, element: int, expected: bool):
    assert (element in interval) is expected


def test_interval_steps():
    interval = Interval(1, 10, max=20)

    assert interval.steps == 0
    interval.a += 1
    assert interval.steps == 1
    interval.a += 4
    assert interval.steps == 5
    interval.a -= 5
    assert interval.steps == 0


def test_tokens_len():
    tokens = [
        T("COMMA", (1, 1)),
        T("AND", (1, 1)),
        T("COLON", (1, 1)),
        T("DOT", (1, 1)),
        T("EQUALS", (1, 1)),
        T("MORE_THAN", (1, 1)),
    ]
    size = len(tokens)

    assert len(Tokens(tokens)) == size
    assert len(Tokens(tokens, Interval(1, 3, max=size))) == len(tokens[1:3])
    assert len(Tokens(tokens, Interval(1, 10, max=size))) == len(tokens[1:10])


# @pytest.mark.parametrize("matcher, expected", [
#     ["SPACE", 5],
#     ["INT", 1],
#     ["NOTHING", 0],
#     ["VOID", 1],
# ])
# def test_count_all_strategy(matcher: str, expected: int, tokens: Tokens):
#     result = tokens.count(matcher)

#     assert result == expected


# @pytest.mark.parametrize("skip, matcher, expected", [
#     [9, "SPACE", 4],
#     [0, "TAB", 0],
# ])
# def test_count_while_strategy(skip: int, matcher: str, expected: int, tokens: Tokens):
#     tokens = tokens.skip(skip)
#     result = tokens.count(matcher, strategy="while")

#     assert result == expected


# @pytest.mark.parametrize("matcher, expected", [
#     ["SPACE", 9],
#     ["INT", 0],
#     ["42", 20],
# ])
# def test_count_until_strategy(matcher: str, expected: int, tokens: Tokens):
#     result = tokens.count(matcher, strategy="until")

#     assert result == expected


def test_skip_match_as_int():
    tokens = Tokens([T("SPACE", (1, 1)), T("TAB", (1, 1))])

    tokens.skip(1)

    assert len(tokens) == 1
    assert tokens[0].type == "TAB"
    with pytest.raises(IndexError):
        tokens[1]


def test_skip_match_as_str():
    tokens = Tokens([T("SPACE", (1, 1)), T("TAB", (1, 2))])

    tokens.skip("SPACE")

    assert len(tokens) == 1
    assert tokens[0].type == "TAB"
    with pytest.raises(IndexError):
        tokens[1]


@pytest.mark.parametrize("match", dict_to_pytest_param({
    "Test matcher with return 0": [matchers.Echo(0)],
}))
def test_skip_match_as_matcher(match: matchers.Matcher[int]):
    pass
