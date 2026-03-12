from dataclasses import dataclass, field

from pmark.line_span import LineSpan


@dataclass(slots=True)
class BlockLexerRuleContext:
    line_span: LineSpan  # (StartLine, Endline) inside rule func
    """
    The line range being processed in this rule.
    """

    speculative_mode: bool = field(default=False)
    """
    When enabled, executes rule in speculative parsing mode - only checks if the rule matches
    at the current position without generating tokens.
    """
