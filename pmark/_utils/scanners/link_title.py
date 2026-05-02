from enum import Enum, auto
from dataclasses import dataclass, field

from pmark._utils.constants import (
    SINGLE_QUOTE_CHARACTER,
    DOUBLE_QUOTE_CHARACTER,
    LEFT_PARENTHESIS_CHARACTER,
    RIGHT_PARENTHESIS_CHARACTER,
    BACKSLASH_CHARACTER,
)


class LinkTitleScannerStatus(Enum):
    SUCCESS = auto()
    INCOMPLETE = auto()
    REJECTION = auto()


@dataclass(slots=True)
class LinkTitleScannerState:
    status: LinkTitleScannerStatus
    next_charno: int | None = field(default=None)
    title: str | None = field(default=None)
    closing_marker: str | None = field(default=None)

    def expect_closing_marker(self) -> str:
        """
        Returns the closing marker.

        Raises:
            ValueError: If no closing marker has been set.
        """
        if not self.closing_marker:
            raise ValueError("Closing marker not set")
        return self.closing_marker


def scan_link_title(
    source: str,
    start_charno: int,
    end_charno: int,
    state: LinkTitleScannerState | None = None,
) -> LinkTitleScannerState:
    if not (start_charno < end_charno <= len(source)):
        return LinkTitleScannerState(status=LinkTitleScannerStatus.REJECTION)

    current_charno = start_charno

    if state is None:
        marker = source[current_charno]

        if marker not in (
            LEFT_PARENTHESIS_CHARACTER,
            SINGLE_QUOTE_CHARACTER,
            DOUBLE_QUOTE_CHARACTER,
        ):
            return LinkTitleScannerState(status=LinkTitleScannerStatus.REJECTION)

        start_charno += 1
        current_charno += 1

        state = LinkTitleScannerState(
            status=LinkTitleScannerStatus.REJECTION,
            closing_marker=(
                RIGHT_PARENTHESIS_CHARACTER
                if marker == LEFT_PARENTHESIS_CHARACTER
                else marker
            ),
        )

    while current_charno < end_charno:
        current_char = source[current_charno]
        marker = state.expect_closing_marker()

        if current_char == marker:
            state.next_charno = current_charno + 1

            if state.title is None:
                state.title = ""

            state.title += source[start_charno:current_charno]
            state.status = LinkTitleScannerStatus.SUCCESS
            return state

        if current_char in (LEFT_PARENTHESIS_CHARACTER, RIGHT_PARENTHESIS_CHARACTER):
            return state

        if current_char == BACKSLASH_CHARACTER and current_charno + 1 < end_charno:
            current_charno += 1

        current_charno += 1

    state.status = LinkTitleScannerStatus.INCOMPLETE

    if state.title is None:
        state.title = ""

    state.title += source[start_charno:current_charno]
    return state
