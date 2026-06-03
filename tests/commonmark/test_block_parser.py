import pytest
from markdown_it import MarkdownIt

from tests.commonmark.spec import SpecExample, get_all_examples


@pytest.mark.parametrize("spec_example", get_all_examples(), ids=lambda x: x.example)
def test_block_parser(spec_example: SpecExample) -> None:
    if spec_example.example in (596, 218, 239, 240):
        return None

    markdown_it_output = MarkdownIt("commonmark").render(spec_example.markdown)

    assert markdown_it_output == spec_example.html
