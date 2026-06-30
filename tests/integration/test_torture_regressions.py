import io
import json
import pytest

from candidate_transformer.api import CandidateTransformer
from candidate_transformer.config.models import PipelineConfig

import os

def get_test_config():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config_path = os.path.join(base_dir, "configs", "default.json")
    with open(config_path) as f:
        conf = json.load(f)
    return PipelineConfig(**conf)

def test_entity_resolution_aliases():
    config = get_test_config()
    transformer = CandidateTransformer(config)
    
    # We provide CSV records that should merge via Name.
    # Robert Jones <-> Bob Jones
    # Alice Smith <-> ALICE I. SMITH
    csv_data = """Candidate Name,Email Address,Phone Number
Robert Jones,rjones@example.com,
Bob Jones,bobj@example.com,
Alice Smith,asmith@example.com,
ALICE I. SMITH,alices@example.com,
"""
    transformer.load("recruiter_csv", io.StringIO(csv_data))
    transformer.build()
    
    # Should resolve to exactly 2 candidates
    assert len(transformer._dataset.candidates) == 2

def test_resume_edge_cases():
    config = get_test_config()
    transformer = CandidateTransformer(config)
    
    resume_data = """====================
NAME: Carol N. White
CONTACT: carol.white@example.com | 4155551002
====================
sKILLS:
Leadership, DevOps, Docker
work:
Product Manager at MSFT (2015-01-01 - 2017-12-31)
--- PAGE 2 ---
"""
    transformer.load("resume_text", io.StringIO(resume_data))
    transformer.build()
    
    assert len(transformer._dataset.candidates) == 1
    cand = transformer._dataset.candidates[0]
    
    # Name extraction should ignore dividers
    assert cand.full_name == "Carol N. White"
    
    # Skills mapped from "sKILLS:"
    assert len(cand.skills) > 0
    assert any("DevOps" in s.name for s in cand.skills)
    
    # Experience mapped from "work:"
    assert len(cand.experience) > 0
    assert cand.experience[0].company == "MSFT"

def test_phone_normalization_fallback():
    config = get_test_config()
    transformer = CandidateTransformer(config)
    
    # Provide identical names so ER merges them, and check if phones deduplicate
    csv_data = """Candidate Name,Email Address,Phone Number
Dave Johnson,dave1@example.com,+919811111000
Dave Johnson,dave2@example.com,09811111000
Dave Johnson,dave3@example.com,(981) 111-1000
"""
    transformer.load("recruiter_csv", io.StringIO(csv_data))
    transformer.build()
    
    cand = transformer._dataset.candidates[0]
    
    phones = cand.contact.phones if cand.contact else []
    # Should not have 3 distinct canonical phones since they normalize equivalently
    assert len(phones) < 3

def test_incremental_ingestion():
    config = get_test_config()
    transformer = CandidateTransformer(config)
    
    csv1 = "Candidate Name,Email Address,Phone Number\nEve Adams,eve@example.com,"
    transformer.load("recruiter_csv", io.StringIO(csv1))
    transformer.build()
    assert len(transformer._dataset.candidates) == 1
    
    # Add same candidate with new data and a new candidate
    csv2 = "Candidate Name,Email Address,Phone Number\nEve Adams,eve@example.com,+14155551234\nFrank Wright,frank@example.com,"
    transformer.load("recruiter_csv", io.StringIO(csv2))
    transformer.build()
    
    # Merges Eve, adds Frank
    assert len(transformer._dataset.candidates) == 2
    
    eves = [c for c in transformer._dataset.candidates if "Eve Adams" in c.full_name]
    assert len(eves) == 1
    # Eve should have the newly added phone
    assert len(eves[0].contact.phones if eves[0].contact else []) == 1

def test_years_experience_mapping():
    config = get_test_config()
    transformer = CandidateTransformer(config)
    
    csv_data = """Candidate Name,Email Address,Years Experience
Hank Pym,hank@example.com,5
"""
    transformer.load("recruiter_csv", io.StringIO(csv_data))
    transformer.build()
    
    cand = transformer._dataset.candidates[0]
    assert cand.years_experience == 5.0
