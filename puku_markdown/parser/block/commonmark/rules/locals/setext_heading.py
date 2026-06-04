from dataclasses import dataclass


@dataclass(slots=True)
class SetextHeadingLocals:
    current_lineno: int
    marker: str | None = None
    heading_level: int | None = None
    is_terminated: bool = False
