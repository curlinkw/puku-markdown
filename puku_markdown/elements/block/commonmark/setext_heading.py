from dataclasses import dataclass

from puku_markdown.elements.block.base import BlockElement


@dataclass(slots=True)
class SetextHeading(BlockElement):
    marker: str
    content: str
