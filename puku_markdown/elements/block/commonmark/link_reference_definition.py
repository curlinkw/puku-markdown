from dataclasses import dataclass

from puku_markdown.elements.block import BlockElement


@dataclass(slots=True)
class LinkReferenceDefinition(BlockElement):
    label: str
    href: str
    title: str | None = None
