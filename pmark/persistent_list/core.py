from typing import Generic, overload, Union

from pmark.persistent_list.modification import Modification
from pmark.persistent_list.change_set import ChangeSet
from pmark.persistent_list.type_vars import ItemT


class PersistentList(Generic[ItemT]):
    def __init__(self) -> None:
        self._items: list[ItemT] = []
        self._modification_stack: list[Modification[ItemT]] = []
        self._changeset_stack: list[ChangeSet] = []
        self._has_transient: bool = False

    @overload
    def __getitem__(self, index: int) -> ItemT: ...

    @overload
    def __getitem__(self, index: slice) -> list[ItemT]: ...

    def __getitem__(self, index: Union[int, slice]) -> Union[ItemT, list[ItemT]]:
        """
        Return the item(s) at the given index or slice.

        - For an integer index, returns the single element at that position.
        - For a slice, returns a *new plain Python list* containing a shallow copy
        of the selected elements. This breaks persistence intentionally - slices
        are ephemeral and not tracked as persistent versions.

        Raises:
            IndexError: If an integer index is out of range.
        """
        return self._items[index]
