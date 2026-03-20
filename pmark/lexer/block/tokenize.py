from pmark.line_span import LineSpan
from pmark.lexer.block.state import BlockLexerState
from pmark.lexer.block.frame import BlockLexerFrame
from pmark.lexer.block.command import (
    BlockLexerCommand,
    BlockLexerCommandKind,
    APPLICABLE_COMMAND_KINDS,
    NESTING_COMMAND_KINDS,
)
from pmark.lexer.block.rule_chains import BlockLexerRuleChain
from pmark.lexer.block.rule_context import BlockLexerRuleContext


def _process_command(
    frames: list[BlockLexerFrame],
    current_frame: BlockLexerFrame,
    command: BlockLexerCommand,
) -> None:
    """Apply a command to the frame stack and current frame."""
    match command.kind:
        case (
            BlockLexerCommandKind.COMMIT_SUCCESS
            | BlockLexerCommandKind.COMMIT_REJECTION
        ):
            current_frame.increment_ruleno()

        case (
            BlockLexerCommandKind.TOKENIZE_NESTED
            | BlockLexerCommandKind.PROBE_TERMINATION
        ):
            current_frame.capture_current_rule_context(
                rule_context=command.expect_origin_rule_context()
            )
            child_frame = current_frame.create_child_from_command(command=command)
            frames.append(child_frame)


def _process_rules_until_applicable(
    frames: list[BlockLexerFrame],
    state: BlockLexerState,
    current_frame: BlockLexerFrame,
) -> BlockLexerCommand:
    """Invoke rules of the current frame sequentially until an appplicable command appears.
    If the loop exhausts all rules without producing an appplicable command,
    an exception is raised.

    Raises:
        LookupError: If the loop completes without producing an appplicable command.
    """
    while current_frame.has_more_rules:
        command = current_frame.current_rule(
            state,
            BlockLexerRuleContext(
                line_span=LineSpan(
                    start_lineno=state.current_lineno,
                    end_lineno=current_frame.line_span.end_lineno,
                ),
                is_speculative_mode=False,
            ),
        )
        _process_command(frames=frames, current_frame=current_frame, command=command)

        if command.kind in APPLICABLE_COMMAND_KINDS:
            return command

    raise LookupError("No appplicable command produced by frame.")


def _is_in_block_scope(state: BlockLexerState, frame: BlockLexerFrame) -> bool:
    """
    Return True if the current line (from state) lies within the frame's
    line span and is not outdented (i.e., the block's indentation has not ended).
    """
    return state.current_lineno in frame.line_span and not state.is_line_outdented(
        state.current_lineno
    )


def _lex_frame_step(
    frames: list[BlockLexerFrame],
    state: BlockLexerState,
    current_frame: BlockLexerFrame,
    is_first_in_frame: bool,
) -> bool:
    if state.current_lineno not in current_frame.line_span:
        return False

    state.skip_blank_lines()

    if not _is_in_block_scope(state=state, frame=current_frame):
        return False

    if is_first_in_frame:
        current_frame.has_interblock_blank_line |= state.is_preceded_by_blank_line

    command = _process_rules_until_applicable(
        frames=frames, state=state, current_frame=current_frame
    )
    if command.kind in NESTING_COMMAND_KINDS:
        return False

    return True


def _lex_frame(
    frames: list[BlockLexerFrame],
    state: BlockLexerState,
    current_frame: BlockLexerFrame,
):
    if current_frame.is_current_rule_suspended:
        command = current_frame.current_rule(
            state, current_frame.expect_current_rule_context()
        )
        current_frame.release_current_rule_context()
        _process_command(frames=frames, current_frame=current_frame, command=command)

        if current_frame.is_current_rule_suspended:
            return
    else:
        # Invariant: If the frame is not suspended, there is no active rule
        # context, so this must be the very first time we enter the frame.

        _lex_frame_step(
            frames=frames,
            state=state,
            current_frame=current_frame,
            is_first_in_frame=True,
        )

    while _lex_frame_step(
        frames=frames, state=state, current_frame=current_frame, is_first_in_frame=False
    ):
        pass


def block_tokenize(state: BlockLexerState, initial_rule_chain: BlockLexerRuleChain):
    frames = [
        BlockLexerFrame(
            line_span=LineSpan(start_lineno=0, end_lineno=state.line_count),
            rule_chain=initial_rule_chain,
        )
    ]

    while frames:
        current_frame = frames.pop()
