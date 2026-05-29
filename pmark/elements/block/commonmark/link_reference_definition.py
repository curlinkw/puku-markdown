from dataclasses import dataclass

from pmark.elements.block import BlockElement


@dataclass(slots=True)
class LinkReferenceDefinition(BlockElement):
    label: str
    href: str
    title: str
