from typing import Self, Union, cast
from enum import Enum, auto
from dataclasses import dataclass
from itertools import chain
from markdown_it.token import Token as MarkdownItPyToken

from pmark.elements import (
    BlockElement,
    AtxHeading,
    Blockquote,
    FencedCodeBlock,
    HtmlBlock,
    IndentedCodeBlock,
    List,
    ListKind,
    ThematicBreak,
    SetextHeading,
    Paragraph,
    Document,
)


class BlockTokenKind(Enum):
    PARAGRAPH = auto()
    THEMATIC_BREAK = auto()
    BLOCKQUOTE = auto()
    LINK_REFERENCE_DEFINITION = auto()
    INDENTED_CODE_BLOCK = auto()
    HTML_BLOCK = auto()
    FENCED_CODE_BLOCK = auto()
    HEADING = auto()
    ORDERED_LIST = auto()
    BULLET_LIST = auto()
    LIST_ITEM = auto()


class BlockTokenPolarity(Enum):
    OPEN = auto()
    CLOSE = auto()
    SELF_CLOSING = auto()


@dataclass(slots=True, frozen=True)
class ContentPayload:
    content: str


@dataclass(slots=True, frozen=True)
class MarkupPayload:
    markup: str


@dataclass(slots=True, frozen=True)
class FencedCodeBlockPayload:
    markup: str
    info_string: str
    content: str


@dataclass(slots=True, frozen=True)
class HeadingPayload:
    level: int
    content: str


@dataclass(slots=True, frozen=True)
class ListPayload:
    markup: str
    marker_number: int | None


@dataclass(slots=True, frozen=True)
class BlockToken:
    kind: BlockTokenKind
    polarity: BlockTokenPolarity
    payload: (
        Union[
            ContentPayload,
            FencedCodeBlockPayload,
            HeadingPayload,
            MarkupPayload,
            ListPayload,
        ]
        | None
    )

    @classmethod
    def from_markdown_it_py(cls, tokens: list[MarkdownItPyToken]) -> list[Self]:

        def _from_single_token(token: MarkdownItPyToken) -> Self:
            match token.type:
                case "blockquote_open":
                    return cls(
                        kind=BlockTokenKind.BLOCKQUOTE,
                        polarity=BlockTokenPolarity.OPEN,
                        payload=None,
                    )
                case "blockquote_close":
                    return cls(
                        kind=BlockTokenKind.BLOCKQUOTE,
                        polarity=BlockTokenPolarity.CLOSE,
                        payload=None,
                    )
                case "code_block":
                    return cls(
                        kind=BlockTokenKind.INDENTED_CODE_BLOCK,
                        polarity=BlockTokenPolarity.SELF_CLOSING,
                        payload=ContentPayload(content=token.content),
                    )
                case "fence":
                    return cls(
                        kind=BlockTokenKind.FENCED_CODE_BLOCK,
                        polarity=BlockTokenPolarity.SELF_CLOSING,
                        payload=FencedCodeBlockPayload(
                            markup=token.markup,
                            content=token.content,
                            info_string=token.info,
                        ),
                    )
                case "hr":
                    return cls(
                        kind=BlockTokenKind.THEMATIC_BREAK,
                        polarity=BlockTokenPolarity.SELF_CLOSING,
                        payload=MarkupPayload(markup=token.markup),
                    )
                case "html_block":
                    return cls(
                        kind=BlockTokenKind.HTML_BLOCK,
                        polarity=BlockTokenPolarity.SELF_CLOSING,
                        payload=ContentPayload(content=token.content),
                    )
                case "ordered_list_open":
                    return cls(
                        kind=BlockTokenKind.ORDERED_LIST,
                        polarity=BlockTokenPolarity.OPEN,
                        payload=ListPayload(
                            markup=token.markup,
                            marker_number=cast(int, token.attrs.get("start", 1)),
                        ),
                    )
                case "bullet_list_open":
                    return cls(
                        kind=BlockTokenKind.BULLET_LIST,
                        polarity=BlockTokenPolarity.OPEN,
                        payload=ListPayload(markup=token.markup, marker_number=None),
                    )
                case "ordered_list_close":
                    return cls(
                        kind=BlockTokenKind.ORDERED_LIST,
                        polarity=BlockTokenPolarity.CLOSE,
                        payload=ListPayload(markup=token.markup, marker_number=None),
                    )
                case "bullet_list_close":
                    return cls(
                        kind=BlockTokenKind.BULLET_LIST,
                        polarity=BlockTokenPolarity.CLOSE,
                        payload=ListPayload(markup=token.markup, marker_number=None),
                    )
                case "list_item_open":
                    return cls(
                        kind=BlockTokenKind.LIST_ITEM,
                        polarity=BlockTokenPolarity.OPEN,
                        payload=ListPayload(
                            markup=token.markup, marker_number=int(token.info)
                        ),
                    )
                case "list_item_close":
                    return cls(
                        kind=BlockTokenKind.LIST_ITEM,
                        polarity=BlockTokenPolarity.CLOSE,
                        payload=ListPayload(markup=token.markup, marker_number=None),
                    )

                case _:
                    raise ValueError(f"Wrong token type: {token.type}")

        converted_tokens: list[Self] = []

        for token_idx, token in enumerate(tokens):
            match token.type:
                case "inline":
                    continue
                case "heading_open":
                    if token_idx + 2 >= len(tokens):
                        raise RuntimeError(f"Not all tokens for {token}")

                    converted_tokens.append(
                        cls(
                            kind=BlockTokenKind.HEADING,
                            polarity=BlockTokenPolarity.SELF_CLOSING,
                            payload=HeadingPayload(
                                level=int(token.tag[1:]),
                                content=tokens[token_idx + 1].content,
                            ),
                        )
                    )
                case "heading_close":
                    continue

                case "paragraph_open":
                    if token_idx + 2 >= len(tokens):
                        raise RuntimeError(f"Not all tokens for {token}")

                    converted_tokens.append(
                        cls(
                            kind=BlockTokenKind.PARAGRAPH,
                            polarity=BlockTokenPolarity.SELF_CLOSING,
                            payload=ContentPayload(
                                content=tokens[token_idx + 1].content,
                            ),
                        )
                    )

                case "paragraph_close":
                    continue

                case _:
                    converted_tokens.append(_from_single_token(token))

        return converted_tokens

    @classmethod
    def from_block(cls, block: BlockElement) -> list[Self]:
        match block:
            case AtxHeading():
                return [
                    cls(
                        kind=BlockTokenKind.HEADING,
                        polarity=BlockTokenPolarity.SELF_CLOSING,
                        payload=HeadingPayload(
                            level=block.level, content=block.content
                        ),
                    )
                ]
            case Blockquote():
                return [
                    cls(
                        kind=BlockTokenKind.BLOCKQUOTE,
                        polarity=BlockTokenPolarity.OPEN,
                        payload=None,
                    ),
                    *chain(*map(cls.from_block, block.children)),
                    cls(
                        kind=BlockTokenKind.BLOCKQUOTE,
                        polarity=BlockTokenPolarity.CLOSE,
                        payload=None,
                    ),
                ]
            case FencedCodeBlock():
                return [
                    cls(
                        kind=BlockTokenKind.FENCED_CODE_BLOCK,
                        polarity=BlockTokenPolarity.SELF_CLOSING,
                        payload=FencedCodeBlockPayload(
                            markup=block.markup,
                            info_string=block.info_string,
                            content=block.content,
                        ),
                    )
                ]
            case HtmlBlock():
                return [
                    cls(
                        kind=BlockTokenKind.HTML_BLOCK,
                        polarity=BlockTokenPolarity.SELF_CLOSING,
                        payload=ContentPayload(content=block.content),
                    )
                ]
            case IndentedCodeBlock():
                return [
                    cls(
                        kind=BlockTokenKind.INDENTED_CODE_BLOCK,
                        polarity=BlockTokenPolarity.SELF_CLOSING,
                        payload=ContentPayload(content=block.content),
                    )
                ]
            case List():
                token_kind = (
                    BlockTokenKind.BULLET_LIST
                    if block.kind is ListKind.BULLET
                    else BlockTokenKind.ORDERED_LIST
                )

                item_tokens: list[Self] = []
                for item in block.items:
                    item_tokens.append(
                        cls(
                            kind=BlockTokenKind.LIST_ITEM,
                            polarity=BlockTokenPolarity.OPEN,
                            payload=ListPayload(
                                markup=block.marker_char,
                                marker_number=item.marker_number,
                            ),
                        )
                    )
                    item_tokens.extend(chain(*map(cls.from_block, item.children)))
                    item_tokens.append(
                        cls(
                            kind=BlockTokenKind.LIST_ITEM,
                            polarity=BlockTokenPolarity.CLOSE,
                            payload=ListPayload(
                                markup=block.marker_char, marker_number=None
                            ),
                        )
                    )

                return [
                    cls(
                        kind=token_kind,
                        polarity=BlockTokenPolarity.OPEN,
                        payload=ListPayload(
                            markup=block.marker_char,
                            marker_number=block.items[0].marker_number,
                        ),
                    ),
                    *item_tokens,
                    cls(
                        kind=token_kind,
                        polarity=BlockTokenPolarity.CLOSE,
                        payload=ListPayload(
                            markup=block.marker_char, marker_number=None
                        ),
                    ),
                ]

            case ThematicBreak():
                return [
                    cls(
                        kind=BlockTokenKind.THEMATIC_BREAK,
                        polarity=BlockTokenPolarity.SELF_CLOSING,
                        payload=MarkupPayload(markup=block.markup),
                    )
                ]

            case SetextHeading():
                return [
                    cls(
                        kind=BlockTokenKind.HEADING,
                        polarity=BlockTokenPolarity.SELF_CLOSING,
                        payload=HeadingPayload(
                            level=(1 if block.marker == "=" else 2),
                            content=block.content,
                        ),
                    )
                ]

            case Paragraph():
                return [
                    cls(
                        kind=BlockTokenKind.PARAGRAPH,
                        polarity=BlockTokenPolarity.SELF_CLOSING,
                        payload=ContentPayload(content=block.content),
                    )
                ]

            case _:
                raise ValueError(f"Unknown type: {type(block)}")

    @classmethod
    def from_document(cls, document: Document) -> list[Self]:
        return [*chain(*map(cls.from_block, document.root_blocks))]
