from __future__ import annotations
from dataclasses import dataclass


@dataclass(slots=True)
class BlockElement:
    """
    Base class for all block-level elements in the Markdown AST.
    """

    parent: BlockElement | None
    """
    Parent block element in the document tree. `None` for root-level blocks.
    """
