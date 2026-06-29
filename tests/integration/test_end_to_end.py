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
    # E.164 phone assertions
    # Alice should be matched across all 3 files via email "alice.smith@example.com"
    alice_matches = [r for r in results if "alice.smith@example.com" in (r.get("emails") or [])]
    if len(alice_matches) != 1:
        print(f"FAILED: Found {len(alice_matches)} matches for Alice.")
        print(f"Results: {json.dumps(results, indent=2)}")
        raise AssertionError(f"Expected 1 Alice match, got {len(alice_matches)}")
    alice_record = alice_matches[0]

    assert alice_record["full_name"] == "Alice Smith"
    assert "+14155551234" in alice_record["phones"]

    # Assert merged skills
    # Recruiter CSV: Python, Kubernetes, Docker
    # Resume: Python, Go, Kubernetes, AWS, Docker
    # ATS JSON: None
    expected_skills = {"aws", "docker", "go", "kubernetes", "python"}
    actual_skills = {s["name"].lower() for s in alice_record.get("skills", [])}
    assert actual_skills == expected_skills

    # Assert Skills structure
    python_skill = next(s for s in alice_record["skills"] if s["name"].lower() == "python")
    assert "recruiter_csv" in python_skill["sources"]
    assert "resume_text" in python_skill["sources"]

    # Assert ATS education (should be deduplicated if overlap)
    # The deduplicated array should just be tested for existence of key items.
    assert len(alice_record["education"]) > 0
    assert any(ed.get("degree") == "B.S. Computer Science" for ed in alice_record["education"])

    # Assert Experience dates and summary
    experiences = alice_record["experience"]
    assert any(exp.get("start") for exp in experiences)
    assert any(exp.get("summary") for exp in experiences)

    # Assert New Canonical Fields
    assert alice_record.get("location", {}).get("city") == "San Francisco"
    assert alice_record.get("location", {}).get("region") == "CA"
    assert alice_record.get("location", {}).get("country") == "US"

    assert "https://linkedin.com/in/alicesmith" in str(alice_record.get("links", {}).get("linkedin", ""))

    assert "AWS Certified Solutions Architect" in alice_record.get("certifications", [])
    assert "German" in alice_record.get("languages", [])

    # Assert Projects are structured
    assert len(alice_record.get("projects", [])) > 0
    assert isinstance(alice_record.get("projects")[0], dict)
    assert "name" in alice_record.get("projects")[0]

    assert "highly scalable" in alice_record.get("summary", "")

    # Assert rigorous confidence score
    assert alice_record["overall_confidence"] >= 0.7

    # Assert Provenance
    prov = alice_record["provenance"]
    assert len(prov) > 0
    sources = set(p["source"] for p in prov)
    assert "recruiter_csv" in sources
    assert "ats_json" in sources
    assert "resume_text" in sources

    # Ensure no exact duplicate provenance entries
    prov_tuples = [(p["source"], p.get("field", "")) for p in prov]
    assert len(prov_tuples) == len(set(prov_tuples))
