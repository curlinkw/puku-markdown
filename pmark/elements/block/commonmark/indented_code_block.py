from dataclasses import dataclass, field

from pmark.elements.block.base import BlockElement


@dataclass(slots=True)
class IdentedCodeBlock(BlockElement):
    content: str = field(default_factory=str)
