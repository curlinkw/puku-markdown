from pmark.line_span import LineSpan
from pmark.parser.block.state import BlockParserState
from pmark.parser.block.frame import BlockParserFrame
from pmark.parser.block.command import (
    BlockParserCommand,
    BlockParserCommandKind,
    APPLICABLE_COMMAND_KINDS,
    NESTING_COMMAND_KINDS,
    SPECULATIVE_SAFE_COMMAND_KINDS,
)
from pmark.parser.block.rule_chain import BlockParserRuleChain
from pmark.parser.block.rule_context import BlockParserRuleContext
from pmark.parser.block.upcall import BlockParserUpcall, BlockParserUpcallKind
from pmark.parser.block.frame_actuals import BlockParserFrameActuals
from pmark.parser.block.block_stream import BlockParserBlockStream
from pmark.parser.block.logger import logger


def _process_command(
    frames: list[BlockParserFrame],
    current_frame: BlockParserFrame,
    command: BlockParserCommand,
) -> None:
    """Apply a command to the frame stack and current frame."""

    match command.kind:
        case BlockParserCommandKind.COMMIT_SUCCESS:
            current_frame.reset_ruleno()

        case BlockParserCommandKind.COMMIT_REJECTION:
            current_frame.increment_ruleno()

        case (
            BlockParserCommandKind.PARSE_NESTED
            | BlockParserCommandKind.LOOKAHEAD_ANY_RULE_MATCHES
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
    frames: list[BlockParserFrame],
    state: BlockParserState,
    current_frame: BlockParserFrame,
    is_speculative_mode: bool,
) -> BlockParserCommand | None:
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
            current_frame.actuals,
            BlockParserRuleContext(
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


def _parse_through_next_applicable_rule(
    frames: list[BlockParserFrame],
    state: BlockParserState,
    current_frame: BlockParserFrame,
    is_first_call_in_frame: bool,
) -> BlockParserCommand | None:
    """Parse until the next applicable rule, process it, and return its command.

    If the parser is no longer inside the block's scope, the function returns
    `None` without producing a command.

    Args:
        frames: The current stack of parser frames (may be mutated by nested processing).
        state: The global parser state (line number, position, etc.).
        current_frame: The frame to operate on.
        is_first_call_in_frame: `True` if this is the first call of this function
            for `current_frame`; `False` for subsequent calls.

    Returns:
        The command produced by the applicable rule,
        or `None` if the parser is no longer inside the block's scope
    """
    if state.current_lineno not in current_frame.line_span:
        return None

    state.skip_blank_lines()

    if state.current_lineno not in current_frame.line_span:
        return None

    if __debug__:
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


def _parse_frame(
    frames: list[BlockParserFrame],
    state: BlockParserState,
    current_frame: BlockParserFrame,
) -> BlockParserUpcall | None:
    """Process commands within a frame until a nesting command or end of frame.

    Returns:
        `None` if a nesting command was processed, otherwise a `BlockParserUpcall`
        that signals the frame is complete.
    """

    if current_frame.is_current_rule_suspended:
        command = current_frame.current_rule(
            state, current_frame.actuals, current_frame.expect_current_rule_context()
        )
        _process_command(frames=frames, current_frame=current_frame, command=command)

        if command.kind in NESTING_COMMAND_KINDS:
            return None
        else:
            current_frame.release_current_rule_context()

    else:
        # Invariant: If the frame is not suspended, there is no active rule
        # context, so this must be the very first time we enter the frame.

        command = _parse_through_next_applicable_rule(
            frames=frames,
            state=state,
            current_frame=current_frame,
            is_first_call_in_frame=True,
        )
        if command is None:
            return BlockParserUpcall(
                kind=BlockParserUpcallKind.PARSE_NESTED_RESULT,
                payload=current_frame.has_interblock_blank_line,
            )
        if command.kind in NESTING_COMMAND_KINDS:
            return None

    while (
        command := _parse_through_next_applicable_rule(
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
    # -> the parser is no longer inside the block's scope
    # -> frame complete
    return BlockParserUpcall(
        kind=BlockParserUpcallKind.PARSE_NESTED_RESULT,
        payload=current_frame.has_interblock_blank_line,
    )


def _lookahead_any_rule_matches(
    frames: list[BlockParserFrame],
    state: BlockParserState,
    current_frame: BlockParserFrame,
) -> BlockParserUpcall | None:
    """Check if any rule in the current frame's rule chain matches in speculative mode.

    Returns:
        `None` if a nesting command was processed, otherwise a `BlockParserUpcall`
        that signals the frame is complete.
    """
    command = _process_rules_through_next_applicable(
        frames=frames,
        state=state,
        current_frame=current_frame,
        is_speculative_mode=True,
    )

    if command is None:
        return BlockParserUpcall(
            kind=BlockParserUpcallKind.LOOKAHEAD_ANY_RULE_MATCHED, payload=False
        )

    if command.kind is BlockParserCommandKind.LOOKAHEAD_ANY_RULE_MATCHES:
        return None

    return BlockParserUpcall(
        kind=BlockParserUpcallKind.LOOKAHEAD_ANY_RULE_MATCHED, payload=True
    )


def block_parse(state: BlockParserState, initial_rule_chain: BlockParserRuleChain):
    frames = [
        BlockParserFrame(
            line_span=LineSpan(start_lineno=0, end_lineno=state.line_count),
            rule_chain=initial_rule_chain,
            causal_command=BlockParserCommand(
                kind=BlockParserCommandKind.INITIALIZE_ROOT_FRAME,
                child_frame_spec=None,
                origin_rule_context=None,
            ),
            actuals=BlockParserFrameActuals(
                parent_production=None,
                block_stream=BlockParserBlockStream(
                    emit=state.target_document.append_root_block
                ),
                continuation_line_limit=None,
            ),
        )
    ]

    while frames:
        current_frame = frames[-1]

        logger.debug("Entering frame: %r", current_frame)

        match current_frame.causal_command.kind:
            case (
                BlockParserCommandKind.PARSE_NESTED
                | BlockParserCommandKind.INITIALIZE_ROOT_FRAME
            ):
                upcall = _parse_frame(
                    frames=frames, state=state, current_frame=current_frame
                )
            case BlockParserCommandKind.LOOKAHEAD_ANY_RULE_MATCHES:
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
