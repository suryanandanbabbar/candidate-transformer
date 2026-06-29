import pytest

from candidate_transformer.domain.models import (
    Candidate,
    ContactInformation,
    Experience,
    Provenance,
    Skill,
)
from candidate_transformer.strategies.confidence_scoring import (
    DeterministicConfidenceScoringStrategy,
)


@pytest.fixture
def strategy():
    return DeterministicConfidenceScoringStrategy()


def test_confidence_scoring_incomplete(strategy):
    c = Candidate(
        candidate_id="1",
        full_name="Unknown",
        contact=ContactInformation(),
        provenance=[Provenance(field="id", source="unknown", method="a")],
    )
    assert strategy.score(c, {}) == 0.1


def test_confidence_scoring_complete_single_source(strategy):
    c = Candidate(
        candidate_id="1",
        full_name="Alice Smith",
        contact=ContactInformation(emails=["alice@example.com"], phones=["123"]),
        skills=[Skill(name="Python")],
        experience=[Experience(company="Google", title="SWE")],
        provenance=[Provenance(field="full_name", source="ats_json", method="b")],
    )
    assert strategy.score(c, {"ats_json": "a"}) == 0.46


def test_confidence_scoring_complete_multi_source(strategy):
    c = Candidate(
        candidate_id="1",
        full_name="Alice Smith",
        contact=ContactInformation(emails=["alice@example.com"], phones=["123"]),
        skills=[Skill(name="Python")],
        experience=[Experience(company="Google", title="SWE")],
        provenance=[
            Provenance(field="full_name", source="recruiter_csv", method="b"),
            Provenance(field="skills", source="ats_json", method="c"),
            Provenance(field="experience", source="resume_text", method="d"),
        ],
    )
    assert strategy.score(c, {"recruiter_csv": "a", "ats_json": "b", "resume_text": "c"}) == 0.86
