"""Pure ordering helper shared by Column and Card services."""

from collections.abc import Iterable
from typing import Protocol


class Orderable(Protocol):
    order_index: int


def reindex(items: Iterable[Orderable]) -> None:
    """Assign contiguous order_index 0..n-1 following the current sequence order.

    Only mutates the given objects (so a SQLAlchemy session tracks the change).
    Never commits; the calling service owns the transaction.
    """
    for index, item in enumerate(items):
        if item.order_index != index:
            item.order_index = index
