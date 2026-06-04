from dataclasses import dataclass

from pmark.elements.block.base import BlockElement


@dataclass(slots=True)
class IndentedCodeBlock(BlockElement):
    content: str
