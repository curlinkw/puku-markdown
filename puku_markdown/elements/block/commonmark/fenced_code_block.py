from dataclasses import dataclass

from puku_markdown.elements.block.base import BlockElement


@dataclass(slots=True)
class FencedCodeBlock(BlockElement):
    markup: str
    info_string: str
    content: str
