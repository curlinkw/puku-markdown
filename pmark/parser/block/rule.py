from enum import Enum, auto


class BlockParserRule(Enum):
    """Discriminant identifying each concrete block parser rule type."""

    PARAGRAPH_RULE = auto()
