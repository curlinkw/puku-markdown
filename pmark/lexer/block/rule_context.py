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

    lookahead_matched: bool | None = field(default=None)
    """
    Stores whether the most recent `LOOKAHEAD_ANY_RULE_MATCHES` command succeeded.

    When a rule issues a `LOOKAHEAD_ANY_RULE_MATCHES` command, the lexer evaluates the
    specified rule chain in *speculative mode* without consuming input or emitting
    tokens. If any rule in the chain reaches an accepting state, this field is set
    to `True`; otherwise it is set to `False`. After the rule consumes this result (e.g., by resuming
    execution), the field should be reset to `None` to avoid stale state.

    The value is delivered to the rule context via an upcall of kind
    `LOOKAHEAD_ANY_RULE_MATCHED` and stored here until the rule is ready to act on it.
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
