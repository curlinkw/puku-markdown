from pmark.line_span import LineSpan
from pmark.lexer.block.state import BlockLexerState
from pmark.lexer.block.frame import LexerFrame
from pmark.lexer.rule_chains import RULE_CHAINS, LexerRuleChain


def block_tokenize(state: BlockLexerState, initial_rule_chain: LexerRuleChain):
    frames: list[LexerFrame] = [
        LexerFrame(
            line_span=LineSpan(start_lineno=0, end_lineno=state.line_count),
            rule_chain=initial_rule_chain,
        )
    ]

    while frames:
        current_frame = frames.pop()
    
        while state.current_lineno in current_frame.line_span:
            state.skip_blank_lines()

            if state.current_lineno not in current_frame.line_span:
                break

            if state.is_line_outdented(state.current_lineno):
                break

            for rule in current_frame.remaining_rules:
                pass
