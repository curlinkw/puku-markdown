from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias, Callable

if TYPE_CHECKING:
    from puku_markdown.parser.block.state import BlockParserState
    from puku_markdown.parser.block.rule_context import BlockParserRuleContext
    from puku_markdown.parser.block.command import BlockParserCommand
    from puku_markdown.parser.block.frame_actuals import BlockParserFrameActuals


BlockParserRuleFunc: TypeAlias = Callable[
    ["BlockParserState", "BlockParserFrameActuals", "BlockParserRuleContext"],
    "BlockParserCommand",
]
