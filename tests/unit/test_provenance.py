from candidate_transformer.config.models import PipelineConfig
from candidate_transformer.domain.models import Provenance
from candidate_transformer.pipeline.conflict_resolution import ConflictResolutionStage


def test_provenance_deduplication_via_engine():
    # Provenance deduplication happens in ProjectionEngine.
    from candidate_transformer.config.models import OutputConfig
    from candidate_transformer.domain.models import Candidate
    from candidate_transformer.projection.engine import ProjectionEngine

    engine = ProjectionEngine()
    candidate = Candidate(
        candidate_id="123",
        full_name="Alice",
        provenance=[
            Provenance(field="full_name", source="ats", method="priority", confidence=1.0),
            Provenance(field="full_name", source="ats", method="priority", confidence=1.0),
            Provenance(field="skills", source="ats", method="priority", confidence=1.0),
        ],
    )

    config = OutputConfig(include_provenance=True, fields=[])
    result = engine.project(candidate, config)

    # Output should have 2 unique (field, source) pairs
    assert len(result["provenance"]) == 2
    sources = set(p["source"] for p in result["provenance"])
    fields = set(p["field"] for p in result["provenance"])
    assert "ats" in sources
    assert "full_name" in fields
    assert "skills" in fields


def test_conflict_resolution_provenance_generation():
    from candidate_transformer.config.models import OutputConfig

    config = PipelineConfig(source_priorities=["a", "b"], output=OutputConfig(fields=[]))
    stage = ConflictResolutionStage(config.source_priorities)

    record_a = {
        "full_name": "Alice A",
        "__source__": "a",
        "__timestamp__": "2023-01-01",
    }
    record_b = {
        "full_name": "Alice B",
        "__source__": "b",
        "__timestamp__": "2023-01-02",
    }

    candidate = stage.execute([[record_a, record_b]])
    assert len(candidate) == 1
    c = candidate[0]

    # the resolved full_name is Alice A (priority a > b)
    assert c.full_name == "Alice A"
    provs = [p for p in c.provenance if p.field == "full_name"]
    assert len(provs) == 1
    assert provs[0].source == "a"
    assert provs[0].timestamp == "2023-01-01"
    assert provs[0].confidence == 1.0
