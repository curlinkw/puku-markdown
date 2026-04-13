from dataclasses import dataclass, field

from pmark.parser.block.rule import BlockParserRule
from pmark.elements.block import BlockElement


@dataclass(slots=True, frozen=True)
class BlockParserFrameActuals:
    """
    Caller-side concrete values supplied by this frame to a `block rule`.

    Terminology (actuals / formals) originates from ALGOL 58 calling conventions:
    - *Actuals*: concrete arguments provided by the caller.
    - *Formals*: parameter placeholders in the callee.

    This class defines the formal schema: the field names and their types
    are the formals that a rule expects. Each instance stores the actual
    values for a specific frame when it calls a rule.

    Naming discipline:
    - Caller (frame) side: uses "actuals" (this class). *Storing actuals
      unambiguously marks the holder as the caller*.
    - Callee (rule) side: uses attribute grammar terminology:
      - *Inherited attributes*: values received from the parent (frame).
      - *Synthesized attributes*: values computed by the rule and returned
        to the parent (frame).
      - *Locals*: temporary values internal to the rule, not passed up or down.

      The rule never sees "actuals". It receives the content of this class
      as its *inherited attributes*.

    Thus this class belongs exclusively to the caller (frame). The rule
    interprets its content as *inherited attributes*.
    """

    parent_production: BlockParserRule | None = field(default=None)  # parentType
    """
    The production that directly encloses this rule in the parsing hierarchy.

    `None` when this rule is invoked from the root frame (no enclosing rule).
    For nested rules, this field identifies the innermost production that
    initiated the current frame.
    """

    parent_block: BlockElement | None = field(default=None)  # block_element.parent
    """
    The block element that encloses the block currently being parsed.

    `None` when parsing at the document root (no parent block).
    This field represents the parent in the output AST, distinct from
    `parent_production` which tracks the parser rule hierarchy.
    """

    paragraph_line_limit: int | None = field(default=None)
    """
    Exclusive line index that limits paragraph continuation.

    If `None`, defaults to `state.line_count`. Id est, parser must parse until end of block.
    """

    def try_attach_parent(self, block: BlockElement) -> bool:
        """Attach the frame's parent block to the given block, if present.

        If `self.parent_block` is `None`, does nothing and returns `False`.
        Otherwise, sets `block.parent = self.parent_block` and returns `True`.

        Args:
            block: The block element to become a child of the parent block.
        """
        if self.parent_block is None:
            return False
        block.parent = self.parent_block
        return True
