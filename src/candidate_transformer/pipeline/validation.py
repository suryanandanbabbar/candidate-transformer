from candidate_transformer.domain.models import Candidate
from candidate_transformer.interfaces.pipeline import PipelineStage


class ValidationStage(PipelineStage):
    """
    Validates that Canonical Candidates satisfy basic integrity checks
    before projection. Relies mainly on Pydantic's internal validation,
    but performs domain-specific sanity checks.
    """

    def execute(self, input_data: list[Candidate]) -> list[Candidate]:
        valid_candidates = []
        for candidate in input_data:
            # Ex: Reject if we don't even have a valid ID or if it's completely empty
            if not candidate.candidate_id:
                continue

            # If Pydantic model dump works without crashing, basic structure is sound
            try:
                candidate.model_dump()
                valid_candidates.append(candidate)
            except Exception:
                pass

        return valid_candidates
