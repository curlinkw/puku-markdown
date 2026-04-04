from enum import Enum, auto


class BlockLexerRule(Enum):
    """Discriminant identifying each concrete block lexer rule type."""

    PARAGRAPH_RULE = auto()
