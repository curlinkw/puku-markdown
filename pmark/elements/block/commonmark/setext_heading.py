from dataclasses import dataclass

from pmark.elements.block.base import BlockElement


@dataclass(slots=True)
class SetextHeading(BlockElement):
    marker: str
    content: str
