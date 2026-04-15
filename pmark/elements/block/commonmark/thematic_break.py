from dataclasses import dataclass, field

from pmark.elements.block.base import BlockElement


@dataclass(slots=True)
class ThematicBreak(BlockElement):
    markup: str = field(default_factory=str)
