from typing import Generic, overload, Union, Self

from puku_markdown.persistent_list.core import PersistentList
from puku_markdown.persistent_list.type_vars import ItemT


class Transient(Generic[ItemT]):
    """
    Mutable, non-persistent view of a persistent list (Clojure-style transient).

    Changes made through this object affect the underlying list immediately and
    directly, but are *not recorded* on the modification stack - they are
    ephemeral and not part of the persistent version history.

    A transient *cannot be active* while a transaction exists on the same
    persistent list. Conversely, a transaction cannot be started while a transient
    is active.
    """

    __slots__ = ("_target", "_is_active")

    def __init__(self, target: PersistentList[ItemT]) -> None:
        self._target: PersistentList[ItemT] = target
        """The persistent list this `Transient` modifies"""

        self._is_active = False
        """`True` when this transient is active"""

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
        return self._target[index]

    def __enter__(self) -> Self:
        """
        Enter the transient context, activating this mutable view.

        This method is called automatically when the transient is used in a
        `with` statement. It performs the following checks:
            - No other transient is already active on the same persistent list.
            - This transient object is not already active (no nesting).

        On success, it marks the transient as active and sets the corresponding
        flag on the persistent list. The transient instance is returned, allowing
        its methods (e.g., `__setitem__`, `append`) to be used inside the block.

        Returns:
            The transient instance (`self`).

        Raises:
            RuntimeError: If another transient is already active on the persistent list,
                        or if this transient object is already active.
        """
        if self._target.has_transient:
            raise RuntimeError(
                "Cannot enter transient: another transient is already active."
            )
        if self._target.has_active_transaction:
            raise RuntimeError(
                "Cannot enter transient: a transaction is currently active on the persistent list."
            )

        self._is_active = True
        self._target._has_transient = True
        return self

    def __setitem__(self, index: int, value: ItemT) -> None:
        """
        Replace the element at the given index with `value`.

        This operation mutates the underlying persistent list directly. It is only
        allowed when the transient is active.

        Args:
            index: Zero-based position (negative indices count from the end).
            value: New element.

        Raises:
            RuntimeError: If the transient is not active.
            IndexError: If `index` is out of range (propagated from the list).
        """
        if not self._is_active:
            raise RuntimeError("Cannot write to an inactive transient.")
        self._target._items[index] = value

    def append(self, value: ItemT) -> None:
        """
        Append `value` to the end of the persistent list.

        This operation mutates the underlying persistent list directly. It is only
        allowed when the transient is active.

        Args:
            value: New element to add.

        Raises:
            RuntimeError: If the transient is not active.
        """
        if not self._is_active:
            raise RuntimeError("Cannot write to an inactive transient.")
        self._target._items.append(value)

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """
        Exit the transient context.
        """
        if not self._is_active:
            raise RuntimeError("Cannot exit an inactive transient.")

        self._is_active = False
        self._target._has_transient = False
