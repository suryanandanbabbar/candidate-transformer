from candidate_transformer.strategies.conflict_resolution import (
    PriorityConflictResolutionStrategy,
)


def test_priority_conflict_resolution():
    strategy = PriorityConflictResolutionStrategy()

    values = [
        {"value": "Low Priority Name", "source": "resume_text"},
        {"value": "High Priority Name", "source": "ats_json"},
    ]

    context = {"source_priorities": ["ats_json", "recruiter_csv", "resume_text"]}

    result = strategy.resolve(values, context)
    assert result == "High Priority Name"


def test_priority_conflict_resolution_unknown_source():
    strategy = PriorityConflictResolutionStrategy()

    values = [
        {"value": "Unknown Source Name", "source": "some_random_system"},
        {"value": "Known Lowest Priority", "source": "resume_text"},
    ]

    context = {"source_priorities": ["ats_json", "recruiter_csv", "resume_text"]}

    result = strategy.resolve(values, context)
    # resume_text is known, some_random_system is unknown (goes to bottom)
    assert result == "Known Lowest Priority"
