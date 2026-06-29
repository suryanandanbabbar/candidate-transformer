from typing import Any, Protocol, TypeVar

T_co = TypeVar("T_co", covariant=True)


class Normalizer(Protocol[T_co]):
    """
    Contract for a normalization strategy.
    Takes a raw value and attempts to normalize it to the type T.
    """

    def normalize(self, value: Any) -> T_co: ...
