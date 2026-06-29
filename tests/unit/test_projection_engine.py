import pytest

from candidate_transformer.config.models import FieldProjectionConfig, OutputConfig
from candidate_transformer.domain.models import Candidate, ContactInformation
from candidate_transformer.exceptions import ProjectionError
from candidate_transformer.projection.engine import ProjectionEngine


@pytest.fixture
def candidate():
    return Candidate(
        candidate_id="123",
        full_name="Alice Smith",
        contact=ContactInformation(emails=["alice@example.com"]),
    )


def test_projection_success(candidate):
    engine = ProjectionEngine()
    config = OutputConfig(
        fields=[
            FieldProjectionConfig(path="name", from_path="full_name", type="string"),
            FieldProjectionConfig(path="primary_email", from_path="contact.emails[0]", type="string"),
        ]
    )

    result = engine.project(candidate, config)
    assert result["name"] == "Alice Smith"
    assert result["primary_email"] == "alice@example.com"


def test_projection_missing_required(candidate):
    engine = ProjectionEngine()
    config = OutputConfig(
        on_missing="error",
        fields=[FieldProjectionConfig(path="missing_field", type="string", required=True)],
    )

    with pytest.raises(ProjectionError):
        engine.project(candidate, config)
