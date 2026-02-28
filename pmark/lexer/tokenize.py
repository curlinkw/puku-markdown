from pmark.tokens import Token
from pmark.re_patterns import LINE_ENDINGS_RE
from pmark.constants import NULL_CHARACTER, UNICODE_REPLACEMENT_CHARACTER
from pmark.lexer.block_state import BlockLexerState


def tokenize(
    source: str,
) -> list[Token]:
    """
    # TODO
    """

    # Replace NULL characters with Unicode replacement character
    # Note: This is not required by CommonMark spec, but is a common safety practice
    # to prevent issues with underlying string handling in C extensions or when
    # interacting with systems that treat NULL as string terminator
    source = source.replace(NULL_CHARACTER, UNICODE_REPLACEMENT_CHARACTER)

    # Normalize all line endings (\r\n, \r, \n) to \n for parsing simplicity
    # CommonMark treats all line ending styles as equivalent, so this transformation
    # is spec-compliant and simplifies the parser by only needing to handle \n.
    source = LINE_ENDINGS_RE.sub("\n", source)

    block_state = BlockLexerState(source=source)

    while block_state.has_more_lines:
        if not block_state.skip_blank_lines():
            break

        if block_state.is_line_outdented(block_state.current_lineno):
            break

    return []
