from dataclasses import dataclass

from pmark.elements.block.base import BlockElement


@dataclass(slots=True)
class FencedCodeBlock(BlockElement):
    markup: str
    info_string: str
    content: str
