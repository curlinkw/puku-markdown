from dataclasses import dataclass, field

from pmark.line_span import LineSpan
from pmark.lexer.rule_chains import RULE_CHAINS, LexerRuleChain
from pmark.lexer.block.rule_context import BlockLexerRuleContext


@dataclass(slots=True, frozen=True)
class LexerFrame:
    line_span: LineSpan  # (StartLine, Endline) inside tokenize func
    """
    The line range being processed in this frame.
    """

    rule_chain: LexerRuleChain
    """
    Sequence of lexer rules to apply for this frame.
    """

    rule_context: BlockLexerRuleContext | None = field(default=None)

    ruleno: int = field(default=0)

    @property
    def remaining_rules(self) -> tuple:
        """Remaining rules to process from current position onward."""
        return RULE_CHAINS[self.rule_chain][self.ruleno :]
