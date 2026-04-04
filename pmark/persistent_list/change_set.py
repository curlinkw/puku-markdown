from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ChangeSet:
    index: int
