from dataclasses import dataclass


@dataclass(slots=True)
class BlockElement:
    """Base class for all block-level elements in the Markdown AST.

    Convention: Do not store a parent reference to avoid dependency cycles.
    The parent relationship is maintained externally (e.g., via the parser's
    streaming context or a separate parent stack).
    """
