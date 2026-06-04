from puku_markdown.parser.block.rule_chain import BlockParserRuleChain
from puku_markdown.parser.block.state import BlockParserState
from puku_markdown.parser.block.parse import block_parse
from puku_markdown.elements.document import Document
from puku_markdown._utils.re_patterns import LINE_ENDINGS_RE
from puku_markdown._utils.constants import (
    NULL_CHARACTER,
    UNICODE_REPLACEMENT_CHARACTER,
    LINE_FEED_CHARACTER,
)


def parse(source: str) -> Document:
    """
    Parse a CommonMark Markdown string into a document AST.

    The parser handles CommonMark block elements using an explicit stack
    (no recursion). Inline elements are not yet supported.

    Preprocessing steps (applied to the entire input, including code blocks):
        1. NULL characters (``\\x00``) are replaced by the Unicode replacement
           character (``�``) to avoid issues with C extensions or systems that
           treat NULL as a string terminator.
        2. All line endings (``\\r\\n``, ``\\r``, ``\\n``) are normalized to
           ``\\n``. This simplifies parsing and is safe for HTML output,
           but note that original line endings inside code blocks are **not**
           preserved.

    Args:
        source: A UTF-8 encoded Markdown string.

    Returns:
        A `Document` object representing the root of the parsed block AST.
        The document can be traversed or serialized to HTML.

    Example:
        >>> from puku_markdown import parse
        >>> doc = parse("# Hello\\n\\n- List item")
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

    block_state = BlockParserState(source=source, target_document=Document())
    block_parse(
        state=block_state,
        initial_rule_chain=BlockParserRuleChain.FULL_COMMONMARK_RULE_CHAIN,
    )

    return block_state.target_document
