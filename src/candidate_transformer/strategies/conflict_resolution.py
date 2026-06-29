from typing import Any

from candidate_transformer.interfaces.strategy import ConflictResolutionStrategy
from candidate_transformer.strategies.registry import strategy_registry


@strategy_registry("priority_conflict_resolution")
class PriorityConflictResolutionStrategy(ConflictResolutionStrategy):
    """
    Resolves conflicts by picking the value from the highest priority source.
    Requires 'source_priorities' in the context.
    """

    def resolve(self, values: list[dict[str, Any]], context: dict[str, Any]) -> Any:
        if not values:
            return None

        priorities: list[str] = context.get("source_priorities", [])

        # values should be a list of dicts like: {"value": X, "source": "Y"}
        # Sort values based on their source index in the priorities list

        def sort_key(item: dict[str, Any]) -> int:
            source = item.get("source")
            if source in priorities:
                return priorities.index(source)
            return len(priorities)  # Lowest priority if unknown

        sorted_values = sorted(values, key=sort_key)
        return sorted_values[0]["value"]
