from pmark.line_span import LineSpan
from pmark.lexer.block.state import BlockLexerState
from pmark.lexer.block.frame import BlockLexerFrame
from pmark.lexer.block.command import (
    BlockLexerCommand,
    BlockLexerCommandKind,
    APPLICABLE_COMMAND_KINDS,
    NESTING_COMMAND_KINDS,
    SPECULATIVE_SAFE_COMMAND_KINDS,
)
from pmark.lexer.block.rule_chain import BlockLexerRuleChain
from pmark.lexer.block.rule_context import BlockLexerRuleContext
from pmark.lexer.block.upcall import BlockLexerUpcall, BlockLexerUpcallKind


def _process_command(
    frames: list[BlockLexerFrame],
    current_frame: BlockLexerFrame,
    command: BlockLexerCommand,
) -> None:
    """Apply a command to the frame stack and current frame."""

    match command.kind:
        case BlockLexerCommandKind.COMMIT_SUCCESS:
            current_frame.reset_ruleno()

        case BlockLexerCommandKind.COMMIT_REJECTION:
            current_frame.increment_ruleno()

        case (
            BlockLexerCommandKind.TOKENIZE_NESTED
            | BlockLexerCommandKind.LOOKAHEAD_ANY_RULE_MATCHES
        ):
            if not current_frame.is_current_rule_suspended:
                # Invariant:
                # No suspended context
                # -> first rule invokation
                current_frame.capture_current_rule_context(
                    rule_context=command.expect_origin_rule_context()
                )
            child_frame = current_frame.create_child_from_command(command=command)
            frames.append(child_frame)


def _process_rules_through_next_applicable(
    frames: list[BlockLexerFrame],
    state: BlockLexerState,
    current_frame: BlockLexerFrame,
    is_speculative_mode: bool,
) -> BlockLexerCommand | None:
    """Process rules of the current frame sequentially until an applicable command appears.

    The name uses `through` to indicate inclusive processing: the rule that yields the
    applicable command is processed and its command is returned.

    If no rule in the current frame produces an applicable command, `None` is returned.

    Returns:
    The command produced by the first applicable rule, or `None` if no rule applies.
    """
    while current_frame.has_more_rules:
        command = current_frame.current_rule(
            state,
            BlockLexerRuleContext(
                line_span=LineSpan(
                    start_lineno=state.current_lineno,
                    end_lineno=current_frame.line_span.end_lineno,
                ),
                is_speculative_mode=is_speculative_mode,
            ),
        )
        if is_speculative_mode and (command.kind not in SPECULATIVE_SAFE_COMMAND_KINDS):
            raise RuntimeError(
                f"Speculative mode only permits safe commands: {SPECULATIVE_SAFE_COMMAND_KINDS}. Got {command.kind}."
            )

        _process_command(frames=frames, current_frame=current_frame, command=command)

        if command.kind in APPLICABLE_COMMAND_KINDS:
            return command

    return None


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

    if state.current_lineno not in current_frame.line_span:
        return None

    if state.line_descriptors[state.current_lineno].is_lazy_continuation:
        raise RuntimeError(
            f"Internal parser error: lazy continuation line {state.current_lineno} "
            "was not consumed by the previous block rule."
        )

    if state.is_line_outdented(state.current_lineno):
        return None

    if not is_first_call_in_frame:
        current_frame.has_interblock_blank_line |= state.is_preceded_by_blank_line

    command = _process_rules_through_next_applicable(
        frames=frames,
        state=state,
        current_frame=current_frame,
        is_speculative_mode=False,
    )

    if command is None:
        raise LookupError("No applicable command produced by frame.")

    return command


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
        _process_command(frames=frames, current_frame=current_frame, command=command)

        if command.kind in NESTING_COMMAND_KINDS:
            return None
        else:
            current_frame.release_current_rule_context()

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
) -> BlockLexerUpcall | None:
    """Check if any rule in the current frame's rule chain matches in speculative mode.

    Returns:
        `None` if a nesting command was processed, otherwise a `BlockLexerUpcall`
        that signals the frame is complete.
    """
    command = _process_rules_through_next_applicable(
        frames=frames,
        state=state,
        current_frame=current_frame,
        is_speculative_mode=True,
    )

    if command is None:
        return BlockLexerUpcall(
            kind=BlockLexerUpcallKind.LOOKAHEAD_ANY_RULE_MATCHED, payload=False
        )

    if command.kind is BlockLexerCommandKind.LOOKAHEAD_ANY_RULE_MATCHES:
        return None

    return BlockLexerUpcall(
        kind=BlockLexerUpcallKind.LOOKAHEAD_ANY_RULE_MATCHED, payload=True
    )


def block_tokenize(state: BlockLexerState, initial_rule_chain: BlockLexerRuleChain):
    frames = [
        BlockLexerFrame(
            line_span=LineSpan(start_lineno=0, end_lineno=state.line_count),
            rule_chain=initial_rule_chain,
            causal_command=BlockLexerCommand(
                kind=BlockLexerCommandKind.INITIALIZE_ROOT_FRAME
            ),
        )
    ]

    while frames:
        current_frame = frames[-1]

        match current_frame.causal_command.kind:
            case (
                BlockLexerCommandKind.TOKENIZE_NESTED
                | BlockLexerCommandKind.INITIALIZE_ROOT_FRAME
            ):
                upcall = _lex_frame(
                    frames=frames, state=state, current_frame=current_frame
                )
            case BlockLexerCommandKind.LOOKAHEAD_ANY_RULE_MATCHES:
                upcall = _lookahead_any_rule_matches(
                    frames=frames, state=state, current_frame=current_frame
                )
            case _:
                raise ValueError(
                    f"Invalid causal_command kind: {current_frame.causal_command.kind}."
                )

        if upcall is not None:
            current_frame.return_upcall(upcall=upcall)
            frames.pop()
