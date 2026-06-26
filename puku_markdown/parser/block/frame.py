from dataclasses import dataclass, field
from typing import Self

from puku_markdown.line_span import LineSpan
from puku_markdown.parser.block.command import BlockParserCommand
from puku_markdown.parser.block.frame_actuals import BlockParserFrameActuals
from puku_markdown.parser.block.frame_spec import BlockParserFrameSpec
from puku_markdown.parser.block.rule_chain import BlockParserRuleChain
from puku_markdown.parser.block.rule_chain_registry import BLOCK_PARSER_RULE_CHAINS
from puku_markdown.parser.block.rule_context import BlockParserRuleContext
from puku_markdown.parser.block.type_aliases import BlockParserRuleFunc
from puku_markdown.parser.block.upcall import BlockParserUpcall


@dataclass(slots=True)
class BlockParserFrame:
    """
    Represents a stack frame in the `BlockParser` explicit stack machine.

    Each frame corresponds to a nested parsing context (e.g., a block, expression,
    or nested structure) and contains all state needed to suspend and resume
    processing. Frames are managed explicitly via a stack rather than using
    recursion, enabling deep nesting without stack overflow and providing
    fine-grained control over the parsing process.

    The frame follows the upcall pattern: when a nested frame completes,
    it writes its result directly back to the parent frame's rule context
    via the parent index stored in the child frame.
    """

    line_span: LineSpan
    """
    The line range being processed in this frame.
    """

    rule_chain: BlockParserRuleChain
    """
    Ordered sequence of parser rules to apply for this frame.
    """

    causal_command: BlockParserCommand
    """
    The command that caused this parsing frame to be created.

    This field captures the causal relationship in the explicit stack machine:
    when a parent frame processes a command that requires nested parsing,
    that command is stored in the newly created child frame as its `causal_command`.
    """

    actuals: BlockParserFrameActuals
    """
    Concrete caller-side values supplied by this frame to a block rule.

    This field holds the actual arguments that this frame (as caller)
    provides when invoking a rule. The rule receives this data as its
    inherited attributes. Storing actuals marks this frame as the caller.
    """

    current_rule_context: BlockParserRuleContext | None = field(default=None)
    """
    *Mutable* context for the currently active rule.
    """

    current_ruleno: int = field(default=0)
    """
    Index inside `rule_chain` of either the currently active rule or the next rule to process.
    """

    has_interblock_blank_line: bool = field(default=False)
    """
    Indicates whether the current frame contains at least one blank line that
    separates two distinct block-level elements.

    In the context of this parser, a *block is the output of a successfully
    invoked rule* from the frame's `rule_chain`. A rule signals successful completion
    by emitting a `COMMIT_SUCCESS` command (see `BlockParserCommandKind`). Thus, an
    inter-block blank line occurs when a blank line appears *between* two such
    `COMMIT_SUCCESS` events. Blank lines at the very start of the frame
    (before the first `COMMIT_SUCCESS`) or at the very end (after the last `COMMIT_SUCCESS`)
    are *excluded* from this flag. If needed, such leading or trailing blank lines
    can be detected explicitly by rules.
    """

    has_any_rule_succeeded: bool = field(default=False)
    """
    Cumulative flag indicating that at least one rule in this frame's `rule_chain`
    has successfully completed (i.e., emitted a `COMMIT_SUCCESS` command).

    This flag is set by the parser machinery whenever a rule invocation within this
    frame reaches a successful commit. It remains `True` for the lifetime of the frame,
    regardless of subsequent rule failures or backtracking. The primary use case is
    to distinguish *inter-block* blank lines from leading/trailing blank lines:
    a blank line that appears *after* this flag has become `True` is considered an
    inter-block blank line (see `has_interblock_blank_line`).
    """

    @classmethod
    def from_spec(
        cls: type[Self],
        spec: BlockParserFrameSpec,
        causal_command: BlockParserCommand,
        current_rule_context: BlockParserRuleContext | None = None,
        current_ruleno: int = 0,
    ) -> Self:
        """
        Create a `BlockParserFrame` from a `BlockParserFrameSpec` object.

        This factory method initialises a frame using the data provided in `spec`,
        while allowing the caller to override the initial rule index and the causal
        command. It serves as the primary way to instantiate frames when starting
        a new parsing context based on a pre-defined specification.

        Args:
            spec: The frame specification containing the line span, rule chain,
                and initial rule context (if any) for the new frame.
            current_ruleno: The starting rule index within the rule chain.
                Defaults to 0, meaning the first rule will be processed next.
            causal_command: The command (from a parent frame) that triggered
                the creation of this frame. Used to maintain a causal trace
                through the explicit stack. Defaults to `None`.

        Returns:
            A new `BlockParserFrame` instance constructed from the given spec
            and optional overrides.

        Note:
            This method does not perform validation; it assumes the spec is
            well-formed. For consistency with the dataclass design, all fields
            are assigned directly from the spec and arguments.
        """
        return cls(
            line_span=spec.line_span,
            rule_chain=spec.rule_chain,
            actuals=spec.actuals,
            current_rule_context=current_rule_context,
            current_ruleno=current_ruleno,
            causal_command=causal_command,
        )

    def create_child_from_command(self, command: BlockParserCommand) -> Self:
        """
        Create a child frame from a command that contains a frame specification.

        The command must be of a kind that includes a frame spec (e.g.,
        `PARSE_NESTED` or `LOOKAHEAD_ANY_RULE_MATCHES`). This method calls
        `command.expect_frame_spec()` to obtain the spec and uses it to build
        the new frame, also recording the command as the causal origin.

        Args:
            command: The command that triggered the creation of this child frame.

        Returns:
            A new child frame, constructed from the spec.
        """
        return type(self).from_spec(
            spec=command.expect_child_frame_spec(),
            causal_command=command,
        )

    @property
    def current_rule(self) -> BlockParserRuleFunc:
        """Return the rule at the `current_ruleno`.

        Returns:
            BlockParserRuleFunc: The rule at the current position.
        """
        return BLOCK_PARSER_RULE_CHAINS[self.rule_chain][self.current_ruleno]

    @property
    def has_more_rules(self) -> bool:
        """Check whether there are more rules to process.

        Returns:
            bool: `True` if `current_ruleno` is within the bounds of the
                rule list (i.e., there is at least one rule remaining),
                otherwise `False`.
        """
        return self.current_ruleno < len(BLOCK_PARSER_RULE_CHAINS[self.rule_chain])

    def reset_ruleno(self) -> None:
        """Reset the `current_ruleno` to the beginning."""
        self.current_ruleno = 0

    def increment_ruleno(self) -> None:
        """Advance `current_ruleno` by one."""
        self.current_ruleno += 1

    @property
    def is_current_rule_suspended(self) -> bool:
        """Indicate whether the current rule is suspended.

        The suspension state is determined solely by `current_rule_context`:
        - If `current_rule_context` is not None, the rule is suspended.
        - If `current_rule_context` is None, the rule is not suspended.

        Returns:
            bool: `True` if the current rule has a saved context (i.e., it is
            suspended and waiting to be resumed), otherwise `False`.
        """
        return self.current_rule_context is not None

    def capture_current_rule_context(
        self, rule_context: BlockParserRuleContext
    ) -> None:
        """Capture the current rule's suspension context, taking ownership.

        This method stores the provided `rule_context`, marking the current rule as
        suspended. The frame assumes ownership of the context object until it is
        released via `release_current_rule_context`. While captured, the context
        is held by the frame, and `is_current_rule_suspended` will return `True`.

        Args:
            rule_context: An opaque object representing the suspended state of
                the current rule. The caller should not modify or free it after
                passing it to this method; ownership is transferred to the frame.

        Raises:
            ValueError: If a rule context is already captured (i.e.,
                `current_rule_context` is not `None`). The caller must release
                the existing context via `release_current_rule_context()` before
                capturing a new one.
        """
        if self.current_rule_context is not None:
            raise ValueError(
                "Cannot capture new rule context because another context is already captured."
            )
        self.current_rule_context = rule_context

    def release_current_rule_context(self) -> None:
        """Release the current rule's suspension context, relinquishing ownership.

        This method clears the stored context, indicating that the current rule is
        no longer suspended. After calling this, `is_current_rule_suspended` will
        return `False`. If the context held any resources, they should be considered
        released (in C, this would typically involve freeing the context object).

        Raises:
            ValueError: If no rule context is currently captured (i.e.,
                `current_rule_context` is `None`). This prevents incorrect usage
                such as double-releasing or releasing before any capture.

        Note:
            This method does not return the context; it simply discards it. If the
            caller needs to access the context before releasing, it should do so
            via a separate getter (e.g., accessing `current_rule_context` directly)
            before calling this method.
        """
        if self.current_rule_context is None:
            raise ValueError(
                "Cannot release rule context: no context is currently captured."
            )
        self.current_rule_context = None

    def expect_current_rule_context(self) -> BlockParserRuleContext:
        """
        Return the `self.current_rule_context`, asserting that it exists.

        This method is designed to be called only after confirming that the rule is
        suspended (i.e., `is_current_rule_suspended` is `True`). It provides a
        type-safe way to obtain the `not None` context without further optional
        checks, by performing a runtime validation.

        Returns:
            BlockParserRuleContext: The saved context of the suspended rule, guaranteed to be
            `not None`.

        Raises:
            ValueError: If `self.current_rule_context is None`, meaning the rule
                is not suspended or an invariant has been violated.

        Example:
        ```python
            if frame.is_current_rule_suspended:
                ctx = frame.expect_current_rule_context()
        ```
        """
        if self.current_rule_context is None:
            raise ValueError(
                "Cannot get context: current_rule_context is None, "
                "but the rule is expected to be suspended."
            )
        return self.current_rule_context

    def expect_causal_command(self) -> BlockParserCommand:
        """
        Return the `self.causal_command`, asserting that it exists.

        This method is designed to be called only in contexts where the frame is
        known to have been created by a command (e.g., during result return or
        when accessing the caller's context). It provides a type-safe way to
        obtain the `not None` command without further optional checks, by
        performing a runtime validation.

        Returns:
            BlockParserCommand: The command that caused this frame to be created,
            guaranteed to be `not None`.

        Raises:
            ValueError: If `self.causal_command is None`, meaning the frame was
            not created by a command or an invariant has been violated.
        """
        if self.causal_command is None:
            raise ValueError(
                "Cannot get causal_command: it is None, but the frame is expected "
                "to have been created by a command."
            )
        return self.causal_command

    def return_upcall(self, upcall: BlockParserUpcall) -> None:
        """
        Complete this frame and deliver the upcall result to its creator.

        This method is called exactly once when the frame has finished processing
        and has produced an upcall object. It retrieves the causal command that
        created this frame (via `expect_causal_command()`) and delegates delivery
        of the upcall to that command's `deliver_upcall` method. After this call,
        the frame is considered finished and should be popped from the parser stack.

        Args:
            upcall: The upcall object containing the result of this frame's
                execution. Its structure is defined by `BlockParserUpcall` and
                its kind must be compatible with the command that initiated
                the frame (e.g., a `LOOKAHEAD_ANY_RULE_MATCHES` command expects a
                `LOOKAHEAD_ANY_RULE_MATCHED` upcall).

        Raises:
            RuntimeError: If the frame has no causal command (i.e., if
                `expect_causal_command()` fails). This indicates a programming
                error where a frame was created without a proper command link.
        """
        self.expect_causal_command().deliver_upcall(upcall=upcall)
