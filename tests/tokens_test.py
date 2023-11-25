from norminette.tokens import *


class TokensClassTestCase:
    def test_length(self):
        list = [1, 2, 3, 4, 5]
        tkns = Tokens(list)

        assert False

        assert len(tkns) == len(list)
        assert len(tkns.skip(1)) == len(list) - 1

