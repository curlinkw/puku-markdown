from dataclasses import dataclass


@dataclass(slots=True)
class RendererState:
    """
    Base protocol for mutable rendering states.

    Provides a common type hierarchy for the core iterative traversal loop.
    The actual state is renderer-specific; each concrete output format
    (HTML, Text, LaTeX, etc.) defines its own fields and accumulation logic
    in a dedicated subclass.
    """

    pass
