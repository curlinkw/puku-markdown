"""
Module providing a runtime type-safe cast function.

This module defines `safe_cast`, which behaves like `typing.cast` but performs
an actual runtime type check using `isinstance`. It is intended for situations
where you want to assert that a value is of a specific type and get an immediate
error if it is not, rather than relying solely on static type checkers.

The implementation is kept simple and fast by delegating the type check directly
to the built-in `isinstance` function. Therefore, the `typ` argument must be
something that `isinstance` accepts.
"""

from typing import TypeVar, Type, Any

__all__ = ["safe_cast"]

T = TypeVar("T")


def safe_cast(typ: Type[T], val: Any) -> T:
    """
    Cast a value to a type, raising TypeError if the runtime type does not match.

    This function performs a runtime check using `isinstance(val, typ)`. If the
    check passes, the value is returned unchanged; otherwise, a `TypeError` is
    raised. The function signature mirrors `typing.cast` for easy substitution,
    and the type hints indicate that the return value is of the type specified
    by `typ`.

    Args:
        typ: The expected type.
        val: The value to check.

    Returns:
        The value unchanged, if it is an instance of `typ`.

    Raises:
        TypeError: If `val` is not an instance of `typ`, or if `typ` is not
            a valid type for `isinstance` (e.g., a non-class, a `Union` from
            `typing`, etc.). The error message includes the expected type and
            the actual type of the value.
    """
    if not isinstance(val, typ):
        raise TypeError(f"Expected type {typ}, got {type(val)}")
    return val
