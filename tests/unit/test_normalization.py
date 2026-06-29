from candidate_transformer.interfaces.connector import RawRecord
from candidate_transformer.pipeline.extraction import ExtractionStage


def test_location_normalization():
    stage = ExtractionStage()
    raw = RawRecord(
        source_name="test",
        source_type="test",
        timestamp="2026",
        raw_data={
            "city": "san francisco",
            "region": "california",
            "country": "united states"
        }
    )
    res = stage.execute([raw])[0]

    assert res["location"]["city"] == "San Francisco"
    assert res["location"]["region"] == "CA"
    assert res["location"]["country"] == "US"

def test_link_normalization():
    stage = ExtractionStage()
    raw = RawRecord(
        source_name="test",
        source_type="test",
        timestamp="2026",
        raw_data={
            "extracted_links": [
                "www.linkedin.com/in/alicesmith/",
                "github.com/alicesmith",
                "alicesmith.dev",
                "invalid_url",
                "https://example.com"
            ]
        }
    )
    res = stage.execute([raw])[0]

    assert res["links"]["linkedin"] == "https://www.linkedin.com/in/alicesmith"
    assert res["links"]["github"] == "https://github.com/alicesmith"
    assert res["links"]["portfolio"] == "https://alicesmith.dev"
    assert "https://example.com" in res["links"]["other"]
