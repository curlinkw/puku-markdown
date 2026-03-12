from dataclasses import dataclass, field

from pmark.line_span import LineSpan
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

    @property
    def remaining_rules(self) -> tuple[BlockLexerRule, ...]:
        """Remaining rules to process from current position onward."""
        return RULE_CHAINS[self.rule_chain][self.current_ruleno :]
