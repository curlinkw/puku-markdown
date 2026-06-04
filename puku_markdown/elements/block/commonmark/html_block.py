from enum import Enum, auto
from dataclasses import dataclass

from puku_markdown.elements.block.base import BlockElement


class HtmlBlockKind(Enum):
    RAW_TEXT_TAG = auto()
    COMMENT = auto()
    PROCESSING_INSTRUCTION = auto()
    MARKUP_DECLARATION = auto()
    CDATA = auto()
    BLOCK_LEVEL_TAG = auto()
    TAG = auto()


@dataclass(slots=True)
class HtmlBlock(BlockElement):
    kind: HtmlBlockKind
    content: str
