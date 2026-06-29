from typing import Any

from candidate_transformer.domain.models import Candidate
from candidate_transformer.interfaces.strategy import ConfidenceScoringStrategy
from candidate_transformer.strategies.registry import strategy_registry


@strategy_registry("deterministic_confidence_scoring")
class DeterministicConfidenceScoringStrategy(ConfidenceScoringStrategy):
    """
    Deterministic confidence scoring based on completeness and provenance agreement.
    """

    def score(self, candidate: Any, context: dict[str, Any]) -> float:
        """
        Calculates a deterministic confidence score (0.0 to 1.0) based on multiple dimensions.
        Formula:
        1. Profile Completeness:
           Count of populated major fields (full_name, emails, phones, location, skills, experience, education)
           divided by the total expected (7). Max 0.5 points.
        2. Source Corroboration:
           (Number of distinct sources - 1) * 0.15. Max 0.3 points.
        3. Conflict Penalty:
           Deduct 0.05 for each field resolved via 'priority_fallback' (indicates a strict conflict).
        4. Resolution Bonus:
           Add 0.1 if the candidate was formed by merging multiple original records (len(candidate.provenance sources) > 1).
        """
        if not isinstance(candidate, Candidate):
            return 0.0

        # 1. Profile Completeness (0.0 to 0.5)
        fields_to_check = [
            candidate.full_name and candidate.full_name != "Unknown",
            bool(candidate.contact.emails),
            bool(candidate.contact.phones),
            bool(candidate.contact.location),
            bool(candidate.skills),
            bool(candidate.experience),
            bool(candidate.education)
        ]
        completeness_ratio = sum(1 for f in fields_to_check if f) / len(fields_to_check)
        completeness_score = completeness_ratio * 0.5

        # 2. Source Corroboration (0.0 to 0.3)
        unique_sources = {prov.source for prov in candidate.provenance if prov.source != "unknown"}
        corroboration_score = min(0.3, max(0.0, (len(unique_sources) - 1) * 0.15))

        # 3. Conflict Penalty (Negative)
        conflicts = sum(1 for prov in candidate.provenance if prov.method == "priority_fallback")
        conflict_penalty = conflicts * 0.05

        # 4. Resolution Bonus (0.0 or 0.1)
        resolution_bonus = 0.1 if len(unique_sources) > 1 else 0.0

        # Base score gives them something to start with if they have basic info
        base = 0.1 

        final_score = base + completeness_score + corroboration_score + resolution_bonus - conflict_penalty
        return round(min(max(final_score, 0.0), 1.0), 2)
