from lexer.block.state import BlockLexerState


def block_tokenize(state: BlockLexerState):
    while state.has_more_lines:
        if not state.skip_blank_lines():
            break

        if state.is_line_outdented(state.current_lineno):
            break

        # rules iterating
        # TODO
