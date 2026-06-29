from typing import Any

from candidate_transformer.interfaces.pipeline import PipelineStage
from candidate_transformer.strategies import strategy_registry


class EntityResolutionStage(PipelineStage):
    """
    Groups intermediate records that belong to the same candidate entity.
    Returns a List of Lists (grouped records).
    """

    def execute(self, input_data: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        if not input_data:
            return []

        strategy = strategy_registry.get("deterministic_entity_resolution")()

        groups: list[list[dict[str, Any]]] = []

        for record in input_data:
            matched = False
            for group in groups:
                # Compare against the first record in the group
                if strategy.match(record, group[0]):  # type: ignore
                    group.append(record)
                    matched = True
                    break

            if not matched:
                groups.append([record])

        return groups
