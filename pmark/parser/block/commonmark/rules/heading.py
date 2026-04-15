from pmark.parser.block.state import BlockParserState
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.command import BlockParserCommand
from pmark.constants import HASH_CHARACTER


def heading_rule(
    state: BlockParserState,
    inherited_attributes: BlockParserFrameActuals,
    context: BlockParserRuleContext,
) -> BlockParserCommand:
    """
    Heading rule.

    This rule is *terminal* - it never suspends or yields. It either succeeds
    (`COMMIT_SUCCESS`) or rejects (`COMMIT_REJECTION`) in the same
    call. It has no locals (no internal parsing state to resume) and does not
    bind `context` to any production, because no recursive descent is needed.

    Invariants:
        - No recursive calls to other rules.
        - No use of `context.locals` (no suspension points).
        - Returns only `COMMIT_SUCCESS` or `COMMIT_REJECTION` command kinds.
    """

    start_lineno = context.line_span.start_lineno
    start_line_descriptor = state.line_descriptors[start_lineno]

    if __debug__:
        if start_line_descriptor.is_lazy_continuation:
            raise RuntimeError(
                f"Internal parser error: lazy continuation line {start_lineno} "
                "was not consumed by the previous block rule."
            )

    if state.meets_indented_code_block_indent(start_lineno):
        return BlockParserCommand.with_commit_rejection_kind()
