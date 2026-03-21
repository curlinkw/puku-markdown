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
from pmark.lexer.block.upcall import BlockLexerUpcall, BlockLexerUpcallKind


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
            | BlockLexerCommandKind.LOOKAHEAD_ANY_RULE_MATCHES
        ):
            current_frame.capture_current_rule_context(
                rule_context=command.expect_origin_rule_context()
            )
            child_frame = current_frame.create_child_from_command(command=command)
            frames.append(child_frame)


def _process_rules_through_next_applicable(
    frames: list[BlockLexerFrame],
    state: BlockLexerState,
    current_frame: BlockLexerFrame,
) -> BlockLexerCommand:
    """Process rules of the current frame sequentially until an applicable command appears.

    The name uses `through` to indicate inclusive processing: the rule that yields the
    applicable command is processed and its command is returned.

    If the loop exhausts all rules without producing an applicable command,
    an exception is raised.

    Raises:
        LookupError: If the loop completes without producing an applicable command.
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

    raise LookupError("No applicable command produced by frame.")


def _is_in_block_scope(state: BlockLexerState, frame: BlockLexerFrame) -> bool:
    """
    Return True if the current line (from state) lies within the frame's
    line span and is not outdented (i.e., the block's indentation has not ended).
    """
    return state.current_lineno in frame.line_span and not state.is_line_outdented(
        state.current_lineno
    )


def _lex_through_next_applicable_rule(
    frames: list[BlockLexerFrame],
    state: BlockLexerState,
    current_frame: BlockLexerFrame,
    is_first_call_in_frame: bool,
) -> BlockLexerCommand | None:
    """Lex until the next applicable rule, process it, and return its command.

    If the lexer is no longer inside the block's scope, the function returns
    `None` without producing a command.

    Args:
        frames: The current stack of lexer frames (may be mutated by nested processing).
        state: The global lexer state (line number, position, etc.).
        current_frame: The frame to operate on.
        is_first_call_in_frame: `True` if this is the first call of this function
            for `current_frame`; `False` for subsequent calls.

    Returns:
        The command produced by the applicable rule,
        or `None` if the lexer is no longer inside the block's scope
    """
    if state.current_lineno not in current_frame.line_span:
        return None

    state.skip_blank_lines()

    if not _is_in_block_scope(state=state, frame=current_frame):
        return None

    if not is_first_call_in_frame:
        current_frame.has_interblock_blank_line |= state.is_preceded_by_blank_line

    return _process_rules_through_next_applicable(
        frames=frames, state=state, current_frame=current_frame
    )


def _lex_frame(
    frames: list[BlockLexerFrame],
    state: BlockLexerState,
    current_frame: BlockLexerFrame,
) -> BlockLexerUpcall | None:
    """Process commands within a frame until a nesting command or end of frame.

    Returns:
        `None` if a nesting command was processed, otherwise a `BlockLexerUpcall`
        that signals the frame is complete.
    """

    if current_frame.is_current_rule_suspended:
        command = current_frame.current_rule(
            state, current_frame.expect_current_rule_context()
        )
        current_frame.release_current_rule_context()
        _process_command(frames=frames, current_frame=current_frame, command=command)

        if current_frame.is_current_rule_suspended:
            return None
    else:
        # Invariant: If the frame is not suspended, there is no active rule
        # context, so this must be the very first time we enter the frame.

        command = _lex_through_next_applicable_rule(
            frames=frames,
            state=state,
            current_frame=current_frame,
            is_first_call_in_frame=True,
        )
        if command is None:
            return BlockLexerUpcall(
                kind=BlockLexerUpcallKind.TOKENIZE_NESTED_RESULT,
                payload=current_frame.has_interblock_blank_line,
            )
        if command.kind in NESTING_COMMAND_KINDS:
            return None

    while (
        command := _lex_through_next_applicable_rule(
            frames=frames,
            state=state,
            current_frame=current_frame,
            is_first_call_in_frame=False,
        )
    ) is not None:
        if command.kind in NESTING_COMMAND_KINDS:
            return None

    # Invariant:
    # no nesting commands
    # -> the lexer is no longer inside the block's scope
    # -> frame complete
    return BlockLexerUpcall(
        kind=BlockLexerUpcallKind.TOKENIZE_NESTED_RESULT,
        payload=current_frame.has_interblock_blank_line,
    )


def _lookahead_any_rule_matches(
    frames: list[BlockLexerFrame],
    state: BlockLexerState,
    current_frame: BlockLexerFrame,
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
