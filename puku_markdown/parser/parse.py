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


def parse(
    source: str,
) -> Document:
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

    block_state = BlockParserState(source=source, target_document=Document())
    block_parse(
        state=block_state,
        initial_rule_chain=BlockParserRuleChain.FULL_COMMONMARK_RULE_CHAIN,
    )

    return block_state.target_document
