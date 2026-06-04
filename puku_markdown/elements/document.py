from dataclasses import dataclass, field

from puku_markdown.elements.block.base import BlockElement


@dataclass(slots=True)
class Document:
    """
    Root container of a parsed Markdown document.
    """

    root_blocks: list[BlockElement] = field(default_factory=list)
    """Root-level blocks whose parent is this `Document`."""

    def append_root_block(self, root_block: BlockElement) -> None:
        """Append a root-level block to the document."""
        self.root_blocks.append(root_block)
