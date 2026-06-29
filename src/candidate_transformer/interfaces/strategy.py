import abc
from typing import Any


class Strategy(abc.ABC):
    """
    Base interface for all configurable algorithms (strategies).
    """

    pass


class ConflictResolutionStrategy(Strategy):
    @abc.abstractmethod
    def resolve(self, values: list[Any], context: dict[str, Any]) -> Any: ...


class EntityResolutionStrategy(Strategy):
    @abc.abstractmethod
    def match(self, record_a: dict[str, Any], record_b: dict[str, Any]) -> bool: ...


class ConfidenceScoringStrategy(Strategy):
    @abc.abstractmethod
    def score(self, candidate: Any, context: dict[str, Any]) -> float: ...
