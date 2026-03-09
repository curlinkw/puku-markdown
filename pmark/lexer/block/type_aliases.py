from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias, Callable

if TYPE_CHECKING:
    from pmark.lexer.block.state import BlockLexerState
    from pmark.lexer.block.rule_context import BlockLexerRuleContext
    from pmark.lexer.block.command import BlockLexerCommand


BlockLexerRule: TypeAlias = Callable[
    [BlockLexerState, BlockLexerRuleContext], BlockLexerCommand
]
