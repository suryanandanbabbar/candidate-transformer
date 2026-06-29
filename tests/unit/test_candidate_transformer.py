import io

from candidate_transformer.api import CandidateTransformer
from candidate_transformer.config.models import OutputConfig, PipelineConfig


def test_candidate_transformer_empty():
    transformer = CandidateTransformer()
    results = transformer.transform()
    assert results == []


def test_candidate_transformer_with_config():
    config = PipelineConfig(output=OutputConfig(fields=[]), source_priorities=["recruiter_csv"])
    transformer = CandidateTransformer(config)
    assert transformer.config.source_priorities == ["recruiter_csv"]


def test_candidate_transformer_load_and_transform():
    csv_data = "name,email\nAlice,alice@example.com"
    stream = io.StringIO(csv_data)

    transformer = CandidateTransformer()
    transformer.load("recruiter_csv", stream)

    candidates = transformer.transform()
    assert len(candidates) == 1
    assert candidates[0].full_name == "Alice"
    assert "alice@example.com" in candidates[0].contact.emails
