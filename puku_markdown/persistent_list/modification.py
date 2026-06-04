from typing import Generic
from dataclasses import dataclass

from puku_markdown.persistent_list.type_vars import ItemT


@dataclass(slots=True, frozen=True)
class Modification(Generic[ItemT]):
    """
    A single atomic change recorded in the modification stack.
    """

    index: int
    """
    Zero-based position of the element that was changed.
    """

    prior_value: ItemT
    """
    The value that was present at `index` before the modification.
    """

    def rollback(self, target: list[ItemT]) -> None:
        """
        Revert this modification by restoring the `prior_value` at the stored index.

        This operation mutates the target list in place.

        Args:
            target: The mutable list to which this modification was applied.
                    Must have a valid index `self.index`.

        Raises:
            IndexError: If `self.index` is out of range for `target`.
        """
        target[self.index] = self.prior_value
