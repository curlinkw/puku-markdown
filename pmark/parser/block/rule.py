from enum import Enum, auto


class BlockParserRule(Enum):
    """Discriminant identifying each concrete block parser rule type."""

    PARAGRAPH_RULE = auto()
    THEMATIC_BREAK_RULE = auto()
