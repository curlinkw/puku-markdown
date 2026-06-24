from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from puku_markdown.parser.block.command import BlockParserCommand
    from puku_markdown.parser.block.frame_actuals import BlockParserFrameActuals
    from puku_markdown.parser.block.rule_context import BlockParserRuleContext
    from puku_markdown.parser.block.state import BlockParserState


type BlockParserRuleFunc = Callable[
    ["BlockParserState", "BlockParserFrameActuals", "BlockParserRuleContext"],
    "BlockParserCommand",
]
