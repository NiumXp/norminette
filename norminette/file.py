from os.path import splitext, basename
from typing import Optional
from functools import cached_property

from norminette.lexer import Lexer


class File:
    def __init__(self, filepath: str, source: Optional[str] = None) -> None:
        self.path = filepath
        self.name, self.type = splitext(basename(filepath))
        self.source = source

    def __repr__(self) -> str:
        return f"<File {self.path!r} {len(self.source or '')} chars>"

    @cached_property
    def tokens(self):
        lexer = Lexer(self.source)
        tokens = lexer.get_tokens()
        return tuple(tokens)
