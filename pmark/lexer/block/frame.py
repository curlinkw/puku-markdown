from typing import Self
from dataclasses import dataclass, field

from pmark.line_span import LineSpan
from pmark.lexer.block.frame_spec import BlockLexerFrameSpec
from pmark.lexer.block.rule_chains import RULE_CHAINS, BlockLexerRuleChain
from pmark.lexer.block.rule_context import BlockLexerRuleContext
from pmark.lexer.block.command import BlockLexerCommand
from pmark.lexer.block.type_aliases import BlockLexerRule


@dataclass(slots=True)
class BlockLexerFrame:
    """
    Represents a stack frame in the `BlockLexer` explicit stack machine.

    Each frame corresponds to a nested lexical context (e.g., a block, expression,
    or nested structure) and contains all state needed to suspend and resume
    processing. Frames are managed explicitly via a stack rather than using
    recursion, enabling deep nesting without stack overflow and providing
    fine-grained control over the lexing process.

    The frame follows the upcall pattern: when a nested frame completes,
    it writes its result directly back to the parent frame's rule context
    via the parent index stored in the child frame.
    """

    line_span: LineSpan
    """
    The line range being processed in this frame.
    """

    rule_chain: BlockLexerRuleChain
    """
    Ordered sequence of lexer rules to apply for this frame.
    """

    current_rule_context: BlockLexerRuleContext | None = field(default=None)
    """
    *Mutable* context for the currently active rule.
    """

    current_ruleno: int = field(default=0)
    """
    Index inside `rule_chain` of either the currently active rule or the next rule to process.
    """

    causal_command: BlockLexerCommand | None = field(default=None)
    """
    The command that caused this lexical frame to be created.

    This field captures the causal relationship in the explicit stack machine:
    when a parent frame processes a command that requires nested tokenization,
    that command is stored in the newly created child frame as its `causal_command`.
    """

    @classmethod
    def from_spec(
        cls: type[Self],
        spec: BlockLexerFrameSpec,
        current_ruleno: int = 0,
        causal_command: BlockLexerCommand | None = None,
    ) -> Self:
        """
        Create a `BlockLexerFrame` from a `BlockLexerFrameSpec` object.

        This factory method initialises a frame using the data provided in `spec`,
        while allowing the caller to override the initial rule index and the causal
        command. It serves as the primary way to instantiate frames when starting
        a new lexical context based on a pre-defined specification.

        Args:
            spec: The frame specification containing the line span, rule chain,
                and initial rule context (if any) for the new frame.
            current_ruleno: The starting rule index within the rule chain.
                Defaults to 0, meaning the first rule will be processed next.
            causal_command: The command (from a parent frame) that triggered
                the creation of this frame. Used to maintain a causal trace
                through the explicit stack. Defaults to `None`.

        Returns:
            A new `BlockLexerFrame` instance constructed from the given spec
            and optional overrides.

        Note:
            This method does not perform validation; it assumes the spec is
            well-formed. For consistency with the dataclass design, all fields
            are assigned directly from the spec and arguments.
        """
        return cls(
            line_span=spec.line_span,
            rule_chain=spec.rule_chain,
            current_rule_context=spec.current_rule_context,
            current_ruleno=current_ruleno,
            causal_command=causal_command,
        )

    def create_child_from_command(self, command: BlockLexerCommand) -> Self:
        """
        Create a child frame from a command that contains a frame specification.

        The command must be of a kind that includes a frame spec (e.g.,
        `TOKENIZE_NESTED` or `PROBE_TERMINATION`). This method calls
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
    def current_rule(self) -> BlockLexerRule:
        """Return the rule at the `current_ruleno`.

        Returns:
            BlockLexerRule: The rule at the current position.
        """
        return RULE_CHAINS[self.rule_chain][self.current_ruleno]

    @property
    def has_more_rules(self) -> bool:
        """Check whether there are more rules to process.

        Returns:
            bool: `True` if `current_ruleno` is within the bounds of the
                rule list (i.e., there is at least one rule remaining),
                otherwise `False`.
        """
        return self.current_ruleno < len(RULE_CHAINS[self.rule_chain])

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

    def capture_current_rule_context(self, rule_context: BlockLexerRuleContext) -> None:
        """Capture the current rule's suspension context, taking ownership.

        This method stores the provided `rule_context`, marking the current rule as
        suspended. The frame assumes ownership of the context object until it is
        released via `release_current_rule_context`. While captured, the context
        is held by the frame, and `is_current_rule_suspended` will return `True`.

        Args:
            rule_context: An opaque object representing the suspended state of
                the current rule. The caller should not modify or free it after
                passing it to this method; ownership is transferred to the frame.
        """
        self.current_rule_context = rule_context

    def release_current_rule_context(self) -> None:
        """Release the current rule's suspension context, relinquishing ownership.

        This method clears the stored context, indicating that the current rule is
        no longer suspended. After calling this, `is_current_rule_suspended` will
        return `False`. If the context held any resources, they should be considered
        released (in C, this would typically involve freeing the context object).

        Note:
            This method does not return the context; it simply discards it. If the
            caller needs to access the context before releasing, it should do so
            via a separate getter (e.g., accessing `current_rule_context` directly)
            before calling this method.
        """
        self.current_rule_context = None

    def expect_current_rule_context(self) -> BlockLexerRuleContext:
        """
        Return the `self.current_rule_context`, asserting that it exists.

        This method is designed to be called only after confirming that the rule is
        suspended (i.e., `is_current_rule_suspended` is `True`). It provides a
        type-safe way to obtain the `not None` context without further optional
        checks, by performing a runtime validation.

        Returns:
            BlockLexerRuleContext: The saved context of the suspended rule, guaranteed to be
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
