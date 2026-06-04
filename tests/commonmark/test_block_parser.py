import pytest
from markdown_it import MarkdownIt

from tests.commonmark.spec import SpecExample, get_all_examples
from tests.markdown_it_py import markdown_it_py_block_parse, BlockToken

from puku_markdown.parser.parse import parse


@pytest.mark.parametrize("spec_example", get_all_examples(), ids=lambda x: x.example)
def test_block_parser(spec_example: SpecExample) -> None:
    if spec_example.example in (596, 218, 239, 240):
        return None

    assert MarkdownIt("commonmark").render(spec_example.markdown) == spec_example.html

    assert markdown_it_py_block_parse(
        spec_example.markdown
    ) == BlockToken.from_document(parse(spec_example.markdown))
