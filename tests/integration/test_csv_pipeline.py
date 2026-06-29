import io

from candidate_transformer.api import CandidateTransformer


def test_csv_pipeline_integration():
    csv_data = """name,email,phone,current_company,title,skills,years_experience
Alice Smith,alice.smith@example.com,+14155551234,TechCorp,Senior Engineer,Python; Kubernetes; Docker,7
Bob Jones,bobjones@gmail.com,555-987-6543,StartUp Inc,Data Scientist,Machine Learning; Pandas; SQL,3
"""
    stream = io.StringIO(csv_data)

    transformer = CandidateTransformer()
    transformer.load("recruiter_csv", stream)

    candidates = transformer.transform()
    assert len(candidates) == 2

    # Verify Alice
    alice = next(c for c in candidates if c.full_name == "Alice Smith")
    assert "alice.smith@example.com" in alice.contact.emails
    assert "+14155551234" in alice.contact.phones
    assert alice.years_experience == 7.0
    assert len(alice.skills) == 3
    skill_names = [s.name for s in alice.skills]
    assert "Python" in skill_names
    assert len(alice.experience) == 1
    assert alice.experience[0].company == "TechCorp"
