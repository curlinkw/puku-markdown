from dataclasses import dataclass, field

from puku_markdown.elements.block.base import BlockElement


@dataclass(slots=True)
class Blockquote(BlockElement):
    """Blockquote containing one or more block-level elements."""

    children: list[BlockElement] = field(default_factory=list)
