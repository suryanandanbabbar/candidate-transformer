from typing import Any

from candidate_transformer.interfaces.strategy import EntityResolutionStrategy
from candidate_transformer.strategies.registry import strategy_registry


@strategy_registry("deterministic_entity_resolution")
class DeterministicEntityResolutionStrategy(EntityResolutionStrategy):
    """
    Matches two intermediate candidate records deterministically based on a strict priority:
    1. Exact Phone match (if both have at least one intersecting normalized phone)
    2. Exact Email match (if both have at least one intersecting normalized email)
    3. Exact Name match (if both have the same non-empty normalized name)
    """

    def match(self, record_a: dict[str, Any], record_b: dict[str, Any]) -> bool:
        # 1. Phone Match
        phones_a = set(record_a.get("phones") or [])
        phones_b = set(record_b.get("phones") or [])
        if phones_a and phones_b and not phones_a.isdisjoint(phones_b):
            return True

        # 2. Email Match
        emails_a = set(record_a.get("emails") or [])
        emails_b = set(record_b.get("emails") or [])
        if emails_a and emails_b and not emails_a.isdisjoint(emails_b):
            return True

        # 3. Exact Name Match
        name_a = record_a.get("full_name")
        name_b = record_b.get("full_name")
        if name_a and name_b:
            # Simple normalization for comparison (lowercase, strip whitespace)
            clean_a = " ".join(str(name_a).lower().split())
            clean_b = " ".join(str(name_b).lower().split())
            if clean_a == clean_b and clean_a != "":
                return True

        return False
