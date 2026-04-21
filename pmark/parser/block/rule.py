from enum import Enum, auto


class BlockParserRule(Enum):
    """Discriminant identifying each concrete block parser rule type."""

    PARAGRAPH = auto()
    THEMATIC_BREAK = auto()
    SETEXT_HEADING = auto()
