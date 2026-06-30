import json
import os

from candidate_transformer.api import CandidateTransformer
from candidate_transformer.config.models import PipelineConfig


def test_end_to_end_transformation():
    # Construct paths to real sample data
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config_path = os.path.join(base_dir, "configs", "default.json")
    csv_path = os.path.join(base_dir, "sample_data", "recruiter.csv")
    json_path = os.path.join(base_dir, "sample_data", "ats.json")
    resume_path = os.path.join(base_dir, "sample_data", "resume.txt")

    with open(config_path) as f:
        config = PipelineConfig(**json.load(f))

    transformer = CandidateTransformer(config)

    # Load all sources
    with open(csv_path) as f:
        transformer.load("recruiter_csv", f)

    with open(json_path) as f:
        transformer.load("ats_json", f)

    with open(resume_path) as f:
        transformer.load("resume_text", f)

    # Test export (which calls transform automatically)
    transformer.build()
    results = transformer.project(config.output)

    # Basic structural assertions
    assert len(results) > 0
    # Assert basic structure and provenance for the overall dataset
    assert len(results) >= 20  # the torture dataset has 20-30 candidates
    
    # Verify that at least one candidate was merged from multiple sources
    candidates_with_merges = [
        r for r in results 
        if len(set(p["source"] for p in r.get("provenance", []))) > 1
    ]
    assert len(candidates_with_merges) > 0, "Expected at least one candidate to be merged from multiple sources"
    
    # Pick a rich candidate to verify structural integrity
    rich_candidates = [
        r for r in candidates_with_merges 
        if r.get("skills") and r.get("experience")
    ]
    assert len(rich_candidates) > 0
    
    cand = rich_candidates[0]
    
    # Assert Name and Confidence
    assert cand.get("full_name")
    assert cand.get("overall_confidence", 0) > 0
    
    # Assert Skills structure
    skills = cand.get("skills", [])
    assert isinstance(skills, list)
    assert "name" in skills[0]
    assert "sources" in skills[0]
    
    # Assert Experience dates and summary
    experiences = cand.get("experience", [])
    assert isinstance(experiences, list)
    assert "company" in experiences[0]
    
    # Assert Provenance structure
    prov = cand.get("provenance", [])
    assert len(prov) > 0
    
    # Ensure no exact duplicate provenance entries
    prov_tuples = [(p.get("source"), p.get("field", "")) for p in prov]
    assert len(prov_tuples) == len(set(prov_tuples))
