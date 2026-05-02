from pmark._utils.re_patterns import LINE_ENDINGS_RE
from pmark._utils.constants import NULL_CHARACTER, UNICODE_REPLACEMENT_CHARACTER
from pmark.parser.block.state import BlockParserState
from pmark._utils.constants import LINE_FEED_CHARACTER


def parse(
    source: str,
) -> None:
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
    source = LINE_ENDINGS_RE.sub(LINE_FEED_CHARACTER, source)

    return None
