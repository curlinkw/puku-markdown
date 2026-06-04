from enum import Enum, auto
from dataclasses import dataclass

from puku_markdown._utils.scanners.link_title import LinkTitleScannerState


class _LinkReferenceDefinitionStep(Enum):
    SCAN_LABEL = auto()
    SKIP_WHITESPACES_AFTER_LABEL = auto()
    SCAN_DESTINATION = auto()
    SKIP_WHITESPACES_AFTER_DESTINATION = auto()
    SCAN_TITLE = auto()


@dataclass(slots=True)
class LinkReferenceDefinitionLocals:
    current_lineno: int
    content_buffer: str
    end_lineno: int
    current_charno: int = 1
    step: _LinkReferenceDefinitionStep = _LinkReferenceDefinitionStep.SCAN_LABEL
    is_current_line_terminator: bool | None = None
    label_end: int | None = None
    link_destination: str | None = None
    link_title_scanner_state: LinkTitleScannerState | None = None
    link_destination_end_charno: int | None = None
    link_destination_end_lineno: int | None = None
    link_title: str | None = None

    def consume_line_and_advance(self, line_content: str) -> None:
        """
        Appends a line of content to the buffer, advances the line counter,
        and resets the terminator flag for the next line.
        """
        self.content_buffer += line_content
        self.current_lineno += 1
        self.is_current_line_terminator = None

    def expect_is_current_line_terminator(self) -> bool:
        """
        Returns the cached terminator flag.

        Raises:
            ValueError: If the flag has not been set (i.e., is None).
        """
        if self.is_current_line_terminator is None:
            raise ValueError("Current line terminator flag not set")
        return self.is_current_line_terminator

    def expect_link_destination_end_charno(self) -> int:
        """
        Returns the cached end character position of the parsed destination.

        Raises:
            ValueError: If the destination end character position has not been set.
        """
        if self.link_destination_end_charno is None:
            raise ValueError("Destination end character position not set")
        return self.link_destination_end_charno

    def expect_link_destination_end_lineno(self) -> int:
        """
        Returns the cached end line number of the parsed destination.

        Raises:
            ValueError: If the destination end line number has not been set.
        """
        if self.link_destination_end_lineno is None:
            raise ValueError("Destination end line number not set")
        return self.link_destination_end_lineno

    def advance_step(self) -> None:
        """Advance to the next step in the link reference definition sequence."""
        match self.step:
            case _LinkReferenceDefinitionStep.SCAN_LABEL:
                self.step = _LinkReferenceDefinitionStep.SKIP_WHITESPACES_AFTER_LABEL
            case _LinkReferenceDefinitionStep.SKIP_WHITESPACES_AFTER_LABEL:
                self.step = _LinkReferenceDefinitionStep.SCAN_DESTINATION
            case _LinkReferenceDefinitionStep.SCAN_DESTINATION:
                self.step = (
                    _LinkReferenceDefinitionStep.SKIP_WHITESPACES_AFTER_DESTINATION
                )
            case _LinkReferenceDefinitionStep.SKIP_WHITESPACES_AFTER_DESTINATION:
                self.step = _LinkReferenceDefinitionStep.SCAN_TITLE
            case _LinkReferenceDefinitionStep.SCAN_TITLE:
                raise StopIteration("Link reference definition complete")

    @property
    def link_label(self) -> str:
        return self.content_buffer[1 : self.label_end]

    def expect_link_destination(self) -> str:
        """
        Returns the cached link destination.

        Raises:
            ValueError: If the link destination has not been set.
        """
        if self.link_destination is None:
            raise ValueError("Link destination not set")
        return self.link_destination
