from candidate_transformer.pipeline.conflict_resolution import ConflictResolutionStage


def test_experience_deduplication():
    stage = ConflictResolutionStage(source_priorities=["a"])

    group = [
        {
            "__source__": "a",
            "experience": [
                {"company": "Google", "title": "Software Engineer", "summary": "Did stuff"}
            ]
        },
        {
            "__source__": "b",
            "experience": [
                {"company": "Google", "title": "Software Engineer", "start": "2020-01", "summary": "Did stuff at Google"}
            ]
        }
    ]

    res, provs = stage._collect_experience_with_prov(group)

    assert len(res) == 1
    assert res[0]["summary"] == "Did stuff at Google"
    assert res[0]["start"] == "2020-01"

def test_education_deduplication():
    stage = ConflictResolutionStage(source_priorities=["a"])

    group = [
        {
            "__source__": "a",
            "education": [
                {"institution": "MIT", "degree": "BS", "field": "CS", "end_year": 2024}
            ]
        },
        {
            "__source__": "b",
            "education": [
                {"institution": "MIT ", "degree": "bs", "field": "cs", "end_year": "2024"}
            ]
        }
    ]

    res, provs = stage._collect_education_with_prov(group)

    assert len(res) == 1
