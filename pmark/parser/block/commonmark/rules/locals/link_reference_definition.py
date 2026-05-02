from enum import Enum, auto
from dataclasses import dataclass


class _LinkReferenceDefinitionStep(Enum):
    SCAN_LABEL = auto()


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
