from dataclasses import dataclass

from puku_markdown.elements import Element


@dataclass(slots=True)
class RendererState:
    """
    Base protocol for mutable rendering states.

    Provides a common type hierarchy for the core iterative traversal loop.
    The actual state is renderer-specific; each concrete output format
    (HTML, Text, LaTeX, etc.) defines its own fields and accumulation logic
    in a dedicated subclass.
    """

    previous_sibling_type: type[Element] | None
    """
    The class of the immediately preceding sibling block, or `None` if none exists.

    Used to determine whether a separator (e.g., a blank line) is needed before
    the next block.
    """
