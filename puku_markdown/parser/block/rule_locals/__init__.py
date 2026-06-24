"""
Runtime union of all production-specific `rule-locals` and its bounded type variable.

This module defines:
- `BlockParserRuleLocals`: a union of every concrete locals dataclass.
- `BlockParserRuleLocalsT`: a type variable bound to that union.

Design decisions:
- The union is built by directly importing the concrete locals classes (no
  `TYPE_CHECKING`). Because these concrete locals are **pure data containers
  that import nothing**, this module remains a leaf in the dependency graph.
- The bounded type variable is placed in the same module as its bound.
  This keeps the coupling explicit and avoids pulling the union into a
  central `type_vars.py` where it would create unnecessary imports for
  unrelated type variables. Unbounded type variables (if any) are kept in
  a separate `type_vars.py` module.
"""

from typing import TypeVar

from puku_markdown.parser.block.rule_locals.commonmark import (
    BlockquoteLocals,
    LinkReferenceDefinitionLocals,
    ListLocals,
    ParagraphLocals,
    SetextHeadingLocals,
)

BlockParserRuleLocals = (
    ParagraphLocals
    | SetextHeadingLocals
    | BlockquoteLocals
    | LinkReferenceDefinitionLocals
    | ListLocals
)


BlockParserRuleLocalsT = TypeVar("BlockParserRuleLocalsT", bound=BlockParserRuleLocals)


__all__ = [
    "BlockParserRuleLocals",
    "BlockParserRuleLocalsT",
    "BlockquoteLocals",
    "LinkReferenceDefinitionLocals",
    "ListLocals",
    "ParagraphLocals",
    "SetextHeadingLocals",
]
