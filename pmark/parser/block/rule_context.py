from typing import cast
from dataclasses import dataclass, field

from pmark.line_span import LineSpan
from pmark.parser.block.rule import BlockParserRule
from pmark.parser.block.rule_locals import BlockParserRuleLocals, BlockParserRuleLocalsT


@dataclass(slots=True)
class BlockParserRuleContext:
    line_span: LineSpan
    """
    The line range being processed in this rule.
    """

    is_speculative_mode: bool = field(default=False)
    """
    When enabled, executes rule in speculative parsing mode - only checks if the rule matches
    at the current position without consuming characters.
    """

    lookahead_matched: bool | None = field(default=None)
    """
    Stores whether the most recent `LOOKAHEAD_ANY_RULE_MATCHES` command succeeded.

    When a rule issues a `LOOKAHEAD_ANY_RULE_MATCHES` command, the parser evaluates the
    specified rule chain in *speculative mode* without consuming input.
    If any rule in the chain reaches an accepting state, this field is set
    to `True`; otherwise it is set to `False`. After the rule consumes this result (e.g., by resuming
    execution), the field should be reset to `None` to avoid stale state.

    The value is delivered to the rule context via an upcall of kind
    `LOOKAHEAD_ANY_RULE_MATCHED` and stored here until the rule is ready to act on it.
    """

    has_interblock_blank_line: bool | None = field(default=None)
    """
    Indicates whether the most recently completed nested parsing produced at least one inter-block blank line.

    When a rule issues a `PARSE_NESTED` command, the parser suspends the rule and
    processes the nested region. Upon completion, the result (a boolean indicating
    whether the nested frame contains an inter-block blank line) is delivered back
    to the rule context via an upcall of kind `PARSE_NESTED_RESULT`. This field
    stores that value until the rule resumes and consumes it.

    The field is `None` when no nested result is pending or after the value has been
    consumed, the field should be reset to `None` to avoid stale state.
    """

    production: BlockParserRule | None = field(default=None)
    """
    Discriminant identifying the production (parser rule) this context belongs to.

    In attribute grammar terms, each production defines its own set of local attributes.
    This field selects which production's local attribute record is stored in `local_attributes`.

    Initially `None`; the production rule itself must set it to the appropriate rule enum value.
    """

    local_attributes: BlockParserRuleLocals | None = field(default=None)
    """
    Local attributes (temporary variables) of the production.

    These are values used only within the rule's execution - neither inherited from
    the parser nor synthesized back. The concrete type is determined by `production`.

    Initially `None`; the production rule must instantiate and assign the corresponding
    *locals* dataclass when it begins processing.
    """

    def bind_production(
        self, production: BlockParserRule, local_attributes: BlockParserRuleLocals
    ) -> None:
        """
        Bind this context to the given production and its local attributes.

        This method must be called exactly once, at the very beginning of a rule's
        execution. After this call:
          - `production` is set to the given value.
          - `local_attributes` is set to the provided instance (ownership is transferred).

        The caller is responsible for ensuring that the `local_attributes` instance
        matches the production (e.g., `ParagraphLocals` for `BlockParserRule.PARAGRAPH`).
        This method does not validate the match, but in debug builds a runtime assertion can be
        added.

        The context is considered *bound* after this call. It is intended to be
        single-use; do not call this method again on the same context.
        """
        self.production = production
        self.local_attributes = local_attributes

    @property
    def is_bound_to_production(self) -> bool:
        """
        Return `True` if this context is bound to a production.

        A context is considered bound when `bind_production()` has been called
        successfully. This predicate can be used to guard against using an uninitialized context.

        Returns:
            `True` if the context is bound to a production, `False` otherwise.
        """
        return self.production is not None

    def expect_production(self) -> BlockParserRule:
        """
        Return the production to which this context is bound.

        This method must be called only after `bind_production()` has been invoked.
        It guarantees that the context has a valid production; otherwise it raises
        an error, making it suitable for code paths that assume a fully initialized
        context.

        Returns:
            The `BlockParserRule` value previously set by `bind_production()`.

        Raises:
            RuntimeError: If `bind_production()` has not been called (i.e.,
                `production` is still `None`).
        """
        if self.production is None:
            raise RuntimeError("Context is not bound to a production")
        return self.production

    def expect_local_attributes(
        self,
        expected_production: BlockParserRule,
        expected_locals_type: type[BlockParserRuleLocalsT],
    ) -> BlockParserRuleLocalsT:
        """
        Retrieve the local attributes for the expected production.


        This method performs three runtime checks:
          1. The context must be *bound to a production*.
          2. The bound production must equal `expected_production`.
          3. The stored `local_attributes` must be an instance of
             `expected_locals_type`.

        If all checks pass, the local attributes are returned with the correct
        static type (inferred from `expected_locals_type`).

        Args:
            expected_production: The production that the context is expected
                to be bound to.
            expected_locals_type: The concrete locals class expected for that
                production.

        Returns:
            The local attributes instance, typed as the expected locals class.

        Raises:
            RuntimeError: If the context is not bound to any production.
            TypeError: If the production does not match, or if
                `local_attributes` is not an instance of `expected_locals_type`.
        """

        if not self.is_bound_to_production:
            raise RuntimeError(
                "Cannot retrieve local_attributes: context is not bound to a production"
            )

        if self.production is not expected_production:
            raise TypeError(
                f"Expected production {expected_production}, "
                f"but context is bound to {self.production}"
            )

        if not isinstance(self.local_attributes, expected_locals_type):
            raise TypeError(
                f"Expected local_attributes of type {expected_locals_type.__name__}, "
                f"got {type(self.local_attributes).__name__}"
            )

        # The cast is safe because we verified the type above.
        return cast(BlockParserRuleLocalsT, self.local_attributes)
