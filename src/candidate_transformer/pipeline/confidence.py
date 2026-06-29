from candidate_transformer.domain.models import Candidate
from candidate_transformer.interfaces.pipeline import PipelineStage
from candidate_transformer.strategies import strategy_registry


class ConfidenceScoringStage(PipelineStage):
    """
    Calculates and assigns confidence scores to candidates.
    """

    def execute(self, input_data: list[Candidate]) -> list[Candidate]:
        if not input_data:
            return []

        strategy = strategy_registry.get("deterministic_confidence_scoring")()

        for candidate in input_data:
            score = strategy.score(candidate, {})  # type: ignore
            candidate.overall_confidence = score

        return input_data
