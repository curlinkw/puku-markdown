from typing import Generic, overload, Union

from pmark.persistent_list.modification import Modification
from pmark.persistent_list.change_set import ChangeSet
from pmark.persistent_list.type_vars import ItemT


class PersistentList(Generic[ItemT]):
    """
    A persistent list that supports two distinct modes of mutation:

    - *Non-persistent (transient) mutations* - via `Transient`.
       Changes are applied immediately to the current state and *not recorded*
       on the modification stack. They are ephemeral and do not become part of the
       persistent version history. Only one transient can be active at a time.

    - *Persistent (transactional) mutations* - via `TransactionalEditor`.
       Changes are recorded as `Modification` objects on a stack and grouped into
       transactions (`ChangeSet`). Each transaction is atomic and can be rolled back.

    *Mutual exclusion:* A `Transient` and a `TransactionalEditor` cannot be active
    simultaneously. If a `Transient` is active, starting a transaction is forbidden,
    and vice-versa. This ensures that transient (non-recorded) mutations never
    interfere with persistent, versioned changes.
    """

    __slots__ = ("_items", "_modification_stack", "_changeset_stack", "_has_transient")

    def __init__(self) -> None:
        """Initialise an empty persistent list with no active transient or transaction."""

        self._items: list[ItemT] = []
        """The mutable underlying list storing the current state."""

        self._modification_stack: list[Modification[ItemT]] = []
        """Stack of all recorded modifications (in order of application)."""

        self._changeset_stack: list[ChangeSet] = []
        """Stack of transaction descriptors; each is a slice of `_modification_stack`."""

        self._has_transient: bool = False
        """`True` when a `Transient` is currently active."""

    def __len__(self) -> int:
        """Return the number of items in a container."""
        return len(self._items)

    @property
    def has_transient(self) -> bool:
        """`True` if an active `Transient` currently exists for this persistent list."""
        return self.has_transient

    @property
    def has_active_transaction(self) -> bool:
        """`True` if there is at least one open transaction."""
        return bool(self._changeset_stack)

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
