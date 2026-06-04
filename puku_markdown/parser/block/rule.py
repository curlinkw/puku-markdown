from enum import Enum, auto


class BlockParserRule(Enum):
    """Discriminant identifying each concrete block parser rule type."""

    PARAGRAPH = auto()
    THEMATIC_BREAK = auto()
    SETEXT_HEADING = auto()
    BLOCKQUOTE = auto()
    LINK_REFERENCE_DEFINITION = auto()
    INDENTED_CODE_BLOCK = auto()
    HTML_RAW_TEXT_TAG = auto()
    HTML_COMMENT = auto()
    HTML_PROCESSING_INSTRUCTION = auto()
    HTML_MARKUP_DECLARATION = auto()
    HTML_CDATA = auto()
    HTML_BLOCK_LEVEL_TAG = auto()
    HTML_TAG = auto()
    FENCED_CODE_BLOCK = auto()
    ATX_HEADING = auto()
    LIST = auto()
