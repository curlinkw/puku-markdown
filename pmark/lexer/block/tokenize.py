from pmark.line_span import LineSpan
from pmark.lexer.block.state import BlockLexerState
from pmark.lexer.block.frame import BlockLexerFrame
from pmark.lexer.block.command import BlockLexerCommand, BlockLexerCommandKind
from pmark.lexer.block.frame_spec import BlockLexerFrameSpec
from pmark.lexer.block.rule_chains import BlockLexerRuleChain


def _process_command(
    frames: list[BlockLexerFrame],
    current_frame: BlockLexerFrame,
    command: BlockLexerCommand,
) -> None:
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


def _lex_exhaustively(
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

    while state.current_lineno in current_frame.line_span:
        state.skip_blank_lines()

        if state.current_lineno not in current_frame.line_span:
            break

        if state.is_line_outdented(state.current_lineno):
            break


def block_tokenize(state: BlockLexerState, initial_rule_chain: BlockLexerRuleChain):
    frames = [
        BlockLexerFrame(
            line_span=LineSpan(start_lineno=0, end_lineno=state.line_count),
            rule_chain=initial_rule_chain,
        )
    ]

    while frames:
        current_frame = frames.pop()
