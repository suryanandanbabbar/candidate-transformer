import io

from candidate_transformer.api import CandidateTransformer


def test_resume_pipeline_integration():
    resume_data = """
    Alice Smith
    Email: alice.smith@example.com
    Phone: 415.555.1234

    EXPERIENCE
    TechCorp - Staff Software Engineer
    Developed highly scalable microservices in Python and Go.
    """
    stream = io.StringIO(resume_data)

    transformer = CandidateTransformer()
    transformer.load("resume_text", stream)

    candidates = transformer.transform()
    assert len(candidates) == 1

    alice = candidates[0]
    # Basic deterministic extraction guarantees
    assert alice.full_name == "Alice Smith"
    assert "alice.smith@example.com" in alice.contact.emails
    assert "+14155551234" in alice.contact.phones
