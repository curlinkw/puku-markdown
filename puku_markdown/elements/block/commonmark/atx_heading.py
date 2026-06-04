from dataclasses import dataclass

from puku_markdown.elements.block.base import BlockElement


@dataclass(slots=True)
class AtxHeading(BlockElement):
    level: int
    content: str
