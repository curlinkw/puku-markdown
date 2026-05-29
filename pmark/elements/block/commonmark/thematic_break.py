from dataclasses import dataclass

from pmark.elements.block.base import BlockElement


@dataclass(slots=True)
class ThematicBreak(BlockElement):
    markup: str
