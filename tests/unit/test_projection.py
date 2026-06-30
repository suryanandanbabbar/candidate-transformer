import pytest
from candidate_transformer.config.models import OutputConfig, FieldProjectionConfig
from candidate_transformer.domain.models import Candidate, ContactInformation, Experience, Education
from candidate_transformer.projection.engine import ProjectionEngine
from candidate_transformer.exceptions import ProjectionError

@pytest.fixture
def sample_candidate():
    return Candidate(
        candidate_id="uuid-1234",
        full_name="Jane Doe",
        contact=ContactInformation(
            emails=["JANE@EXAMPLE.COM"],
            phones=["(415) 555-1234"]
        ),
        experience=[
            Experience(company="Acme Corp", title="Senior Engineer", start="2020-01-01")
        ],
        education=[],
        skills=[]
    )

def test_field_remapping_and_nested_extraction(sample_candidate):
    config = OutputConfig(
        fields=[
            FieldProjectionConfig(path="name", from_path="full_name", type="string"),
            FieldProjectionConfig(path="primary_email", from_path="contact.emails[0]", type="string"),
            FieldProjectionConfig(path="recent_employer", from_path="experience[0].company", type="string")
        ],
        on_missing="null"
    )
    
    engine = ProjectionEngine()
    result = engine.project(sample_candidate, config)
    
    assert result["name"] == "Jane Doe"
    assert result["primary_email"] == "JANE@EXAMPLE.COM"
    assert result["recent_employer"] == "Acme Corp"

def test_runtime_normalization(sample_candidate):
    config = OutputConfig(
        fields=[
            FieldProjectionConfig(path="email", from_path="contact.emails[0]", type="string", normalize="lowercase"),
            FieldProjectionConfig(path="phone", from_path="contact.phones[0]", type="string", normalize="E164"),
            FieldProjectionConfig(path="name", from_path="full_name", type="string", normalize="trim")
        ],
        on_missing="null"
    )
    
    engine = ProjectionEngine()
    result = engine.project(sample_candidate, config)
    
    assert result["email"] == "jane@example.com"
    # Assuming E164 normalizer works
    assert "555" in result["phone"]
    assert result["name"] == "Jane Doe"

def test_missing_policy_omit(sample_candidate):
    config = OutputConfig(
        fields=[
            FieldProjectionConfig(path="education", type="array")
        ],
        on_missing="omit"
    )
    engine = ProjectionEngine()
    result = engine.project(sample_candidate, config)
    assert "education" not in result

def test_missing_policy_error(sample_candidate):
    config = OutputConfig(
        fields=[
            FieldProjectionConfig(path="education", type="array", required=True)
        ],
        on_missing="error"
    )
    engine = ProjectionEngine()
    with pytest.raises(ProjectionError):
        engine.project(sample_candidate, config)

def test_missing_policy_null(sample_candidate):
    config = OutputConfig(
        fields=[
            FieldProjectionConfig(path="education", type="array", required=True)
        ],
        on_missing="null"
    )
    engine = ProjectionEngine()
    result = engine.project(sample_candidate, config)
    assert result["education"] is None

def test_analytics_deduplication():
    candidate = Candidate(
        candidate_id="uuid-1234",
        full_name="Jane Doe",
        contact=ContactInformation(),
        experience=[
            Experience(company="TechCorp", title="A"),
            Experience(company="Legacy Systems LLC", title="B"),
            Experience(company="TechCorp", title="C"),
            Experience(company="TechCorp Inc.", title="D"),
            Experience(company="TechCorp", title="E")
        ],
        education=[
            Education(degree="B.S. Computer Science", institution="A"),
            Education(degree=None, institution="B"),
            Education(degree="", institution="C"),
            Education(degree="Minor in Mathematics", institution="D"),
            Education(degree="B.S. Computer Science", institution="E")
        ],
        skills=[]
    )
    
    config = OutputConfig(
        fields=[
            FieldProjectionConfig(path="companies_worked_at", from_path="experience[].company", type="array", normalize="canonical"),
            FieldProjectionConfig(path="degrees", from_path="education[].degree", type="array")
        ],
        on_missing="omit"
    )
    
    engine = ProjectionEngine()
    result = engine.project(candidate, config)
    
    assert result["companies_worked_at"] == [
        "TechCorp",
        "Legacy Systems LLC"
    ]
    
    assert result["degrees"] == [
        "B.S. Computer Science",
        "Minor in Mathematics"
    ]
