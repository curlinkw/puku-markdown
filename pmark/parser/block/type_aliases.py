from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias, Callable

if TYPE_CHECKING:
    from pmark.parser.block.state import BlockParserState
    from pmark.parser.block.rule_context import BlockParserRuleContext
    from pmark.parser.block.command import BlockParserCommand


BlockParserRuleFunc: TypeAlias = Callable[
    [BlockParserState, BlockParserRuleContext], BlockParserCommand
]
