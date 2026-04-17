from dataclasses import dataclass

from pmark.elements.block.base import BlockElement


@dataclass(slots=True)
class AtxHeading(BlockElement):
    level: int
    content: str
