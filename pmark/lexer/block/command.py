from typing import Final
from dataclasses import dataclass
from enum import IntEnum, auto

from pmark.lexer.block.frame_spec import BlockLexerFrameSpec
from pmark.lexer.block.rule_context import BlockLexerRuleContext
from pmark.lexer.block.upcall import BlockLexerUpcall, BlockLexerUpcallKind


class BlockLexerCommandKind(IntEnum):
    """
    Discriminant for lexer commands that control the explicit stack machine's
    flow and state transitions.
    """

    COMMIT_SUCCESS = auto()
    """
    The rule has successfully matched the input and reached a final accepting
    state.
    """

    COMMIT_REJECTION = auto()
    """
    The rule has definitively failed to match the input and reached a final
    rejecting state.
    """

    TOKENIZE_NESTED = auto()
    """
    Tokenize a nested lexical region (e.g., the content of a list item or blockquote).

    Return this command when a rule needs to recursively process a subordinate part
    of the source with its own rule chain. The lexer will suspend the current rule,
    tokenize the specified region independently, and then resume the original rule,
    making the nested result available for further processing.

    This enables clean handling of arbitrarily nested structures without explicit
    recursion in rule code. When this kind is used, the `frame_spec`
    field must contain a `BlockLexerFrameSpec` that defines the nested context.
    """

    PROBE_TERMINATION = auto()
    """
    Probe whether any termination rule matches at the current position.

    Return this command when a rule needs to check if the current lexical context
    should end. The lexer evaluates the given rule chain in *speculative mode*.
    When this kind is used, the `frame_spec` field must contain a `BlockLexerFrameSpec`
    whose `rule_chain` defines the termination rules to probe.
    """


APPLICABLE_COMMAND_KINDS: Final[frozenset[BlockLexerCommandKind]] = frozenset(
    {
        BlockLexerCommandKind.COMMIT_SUCCESS,
        BlockLexerCommandKind.PROBE_TERMINATION,
        BlockLexerCommandKind.TOKENIZE_NESTED,
    }
)
"""
Set of command kinds that terminate or suspend rule processing.
These represent successful completion or forced termination of the current rule chain.
"""

NESTING_COMMAND_KINDS: Final[frozenset[BlockLexerCommandKind]] = frozenset(
    {
        BlockLexerCommandKind.PROBE_TERMINATION,
        BlockLexerCommandKind.TOKENIZE_NESTED,
    }
)
"""
Set of command kinds that cause a new frame to be pushed onto the stack,
creating a nested parsing context.
"""


@dataclass(slots=True, frozen=True)
class BlockLexerCommand:
    """
    Instruction returned by a lexer rule to control the lexer's next action.

    A `BlockLexerCommand` encapsulates a directive that tells the block lexer
    how to proceed after a rule has finished its work. It is the primary
    communication channel from lexer rules to the lexer engine.

    Commands play a central role in the *upcall pattern*: when a rule creates
    a child frame (e.g., via `TOKENIZE_NESTED`), the command stores the rule's
    context in `origin_rule_context`. When the child frame completes, it calls
    `return_results()`, which in turn invokes `deliver_results()` on this command.
    The command then forwards the result back to the originating rule's context,
    allowing the rule to resume with the child's output.

    Design Note:
        The architecture anticipates the possibility of evolving into a
        *discriminated union* (sum type) if future command variants require
        significantly different payloads. The current structure keeps the design
        simple until the need for more varied payloads arises.
    """

    kind: BlockLexerCommandKind
    """
    The specific action the lexer should perform. See `BlockLexerCommandKind` for details.
    """

    child_frame_spec: BlockLexerFrameSpec | None = None
    """
    Specification for creating a child frame, used by command kinds that initiate
    nested lexical contexts (`TOKENIZE_NESTED` and `PROBE_TERMINATION`).
    For command kinds that do not create a child frame, this field must be `None`.
    """

    origin_rule_context: BlockLexerRuleContext | None = None
    """
    The context of the rule that produced this command.

    When a rule returns a command to the lexer engine, its current execution
    context must be captured and stored here. This allows the engine to later
    resume the rule (e.g., after a nested frame completes) or use the context
    when processing the command. For commands that do not originate from a rule
    with a context (e.g., synthetic commands injected by the lexer itself),
    this field must be `None`.
    """

    def expect_child_frame_spec(self) -> BlockLexerFrameSpec:
        """
        Return the child frame specification, asserting that it exists for this command kind.

        This method is intended to be called only after confirming that the command
        kind requires a child frame spec (i.e., `self.kind` is `TOKENIZE_NESTED` or
        `PROBE_TERMINATION`). It provides a type-safe way to obtain the `not None`
        `child_frame_spec` without further optional checks, performing a runtime
        validation to uphold the invariant. If `child_frame_spec` is unexpectedly
        `None` - indicating an internal logic error or inconsistent state - a
        `ValueError` is raised.

        Returns:
            BlockLexerFrameSpec: The child frame specification associated with the command,
            guaranteed to be `not None`.

        Raises:
            ValueError: If `self.child_frame_spec` is `None`, meaning the command kind does
                not require a child frame spec or the dataclass invariant has been violated.
        Example:
        ```python
            if cmd.kind in (BlockLexerCommandKind.TOKENIZE_NESTED,
                            BlockLexerCommandKind.PROBE_TERMINATION):
                spec = cmd.expect_child_frame_spec()
        ```
        """

        if self.child_frame_spec is None:
            raise ValueError(
                f"Cannot get child frame spec: child_frame_spec is None for command kind {self.kind}, "
                "but a child frame specification is expected for this kind."
            )
        return self.child_frame_spec

    def expect_origin_rule_context(self) -> BlockLexerRuleContext:
        """
        Return the origin rule context, asserting that it exists for this command.

        This method is intended to be called only after confirming that the command
        originated from a rule that had a captured context (i.e., `origin_rule_context`
        is not `None`). It provides a type-safe way to obtain the `not None` origin
        context without further optional checks, performing a runtime validation to
        uphold the invariant. If `origin_rule_context` is unexpectedly `None` -
        indicating an internal logic error or inconsistent state - a `ValueError` is raised.

        Returns:
            BlockLexerRuleContext: The context of the rule that produced this command,
            guaranteed to be `not None`.

        Raises:
            ValueError: If `self.origin_rule_context` is `None`, meaning the command
                does not carry an origin rule context or the invariant has been violated.

        Example:
        ```python
            if cmd.origin_rule_context is not None:
                ctx = cmd.expect_origin_rule_context()
                parent_frame.capture_current_rule_context(ctx)
        ```
        """
        if self.origin_rule_context is None:
            raise ValueError(
                f"Cannot get origin rule context: origin_rule_context is None for command kind {self.kind}, "
                "but an origin rule context is expected for this command."
            )
        return self.origin_rule_context

    def deliver_upcall(self, upcall: BlockLexerUpcall) -> None:
        """
        Deliver an upcall result to the context that originated this command.

        In the upcall pattern, this method is invoked (typically by a completing
        child frame) to pass the result of a nested operation back to the waiting
        context (e.g., a suspended rule).

        Args:
            upcall: The upcall object representing the result of the nested
                operation. Its structure is defined by `BlockLexerUpcall`.
        """

        match upcall.kind:
            case BlockLexerUpcallKind.PROBE_TERMINATION_RESULT:
                if self.kind is not BlockLexerCommandKind.PROBE_TERMINATION:
                    raise ValueError(
                        f"Cannot deliver PROBE_TERMINATION_RESULT to command of kind {self.kind}. "
                        f"Expected PROBE_TERMINATION command."
                    )
                self.expect_origin_rule_context().has_termination_match = upcall.payload

            case BlockLexerUpcallKind.TOKENIZE_NESTED_RESULT:
                if self.kind is not BlockLexerCommandKind.TOKENIZE_NESTED:
                    raise ValueError(
                        f"Cannot deliver TOKENIZE_NESTED_RESULT to command of kind {self.kind}. "
                        f"Expected TOKENIZE_NESTED command."
                    )
                self.expect_origin_rule_context().has_interblock_blank_line = (
                    upcall.payload
                )
