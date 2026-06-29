from collections.abc import Callable
from typing import Generic, TypeVar

from candidate_transformer.exceptions import ConfigurationError

T = TypeVar("T")


class Registry(Generic[T]):
    """
    A lightweight, generic registry for tracking framework extensions
    such as connectors, normalizers, and strategies.
    """

    def __init__(self, name: str):
        self.name = name
        self._items: dict[str, type[T]] = {}

    def register(self, key: str, item: type[T]) -> None:
        """Register a class with a specific key."""
        if key in self._items:
            raise ConfigurationError(f"Key '{key}' is already registered in registry '{self.name}'.")
        self._items[key] = item

    def __call__(self, key: str) -> Callable[[type[T]], type[T]]:
        """Decorator for automatic registration."""

        def decorator(cls: type[T]) -> type[T]:
            self.register(key, cls)
            return cls

        return decorator

    def get(self, key: str) -> type[T]:
        """Retrieve a class by key."""
        if key not in self._items:
            raise ConfigurationError(f"Key '{key}' not found in registry '{self.name}'.")
        return self._items[key]

    def all(self) -> dict[str, type[T]]:
        """Return all registered items."""
        return self._items.copy()
