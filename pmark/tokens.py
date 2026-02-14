from enum import IntEnum, auto
from dataclasses import dataclass


class TokenKind(IntEnum):
    """
    Token kind identifiers for the Markdown parser's token stream.
    This enum defines *every* token type the lexer can emit.
    """

    pass


@dataclass(slots=True)
class Token:
    kind: TokenKind
    """Token kind identifier."""
