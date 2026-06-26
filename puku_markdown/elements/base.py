from dataclasses import dataclass


@dataclass(slots=True)
class Element:
    """
    Abstract root class for all Markdown AST nodes.

    This class establishes a common type hierarchy for both block-level
    (BlockElement) and inline-level (InlineElement) nodes. It is intentionally
    fieldless to serve as a pure marker interface, allowing the core traversal
    loop to accept any AST node without knowing its specific subtype.

    Convention:
        - Parent references are **not** stored on the node to avoid cyclic
          dependencies and to keep the AST lightweight and serializable.
          Parent relationships are maintained externally (e.g., via a parsing
          stack or a separate traversal context).
        - No rendering or parsing logic is attached to these classes.
          They represent pure data.
    """

    pass
