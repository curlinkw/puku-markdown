from dataclasses import dataclass, field

from pmark.line_span import LineSpan


@dataclass(slots=True)
class BlockLexerRuleContext:
    line_span: LineSpan  # (StartLine, Endline) inside rule func
    """
    The line range being processed in this rule.
    """

    is_speculative_mode: bool = field(default=False)
    """
    When enabled, executes rule in speculative parsing mode - only checks if the rule matches
    at the current position without generating tokens.
    """

    has_termination_match: bool | None = field(default=None)
    """
    Indicates whether a `BlockLexerCommand.PROBE_TERMINATION` call found a matching termination rule.

    This field holds the result of the most recent termination probe performed by
    the rule. It is set to `True` if at least one termination rule successfully
    matched, `False` if none matched, and remains `None` until a probe has been
    initiated and completed. After the rule consumes this result (e.g., by resuming
    execution), the field should be reset to `None` to avoid stale state.

    The value is delivered to the rule context via an upcall of kind
    `PROBE_TERMINATION_RESULT` and stored here until the rule is ready to act on it.
    """

    has_interblock_blank_line: bool | None = field(default=None)
    """
    Indicates whether the most recently completed nested tokenization produced at least one inter-block blank line.

    When a rule issues a `TOKENIZE_NESTED` command, the lexer suspends the rule and
    processes the nested region. Upon completion, the result (a boolean indicating
    whether the nested frame contains an inter-block blank line) is delivered back
    to the rule context via an upcall of kind `TOKENIZE_NESTED_RESULT`. This field
    stores that value until the rule resumes and consumes it.

    The field is `None` when no nested result is pending or after the value has been
    consumed, the field should be reset to `None` to avoid stale state.
    """
