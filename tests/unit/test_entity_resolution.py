import pytest

from candidate_transformer.strategies.entity_resolution import (
    DeterministicEntityResolutionStrategy,
)


@pytest.fixture
def strategy():
    return DeterministicEntityResolutionStrategy()


def test_match_by_phone(strategy):
    record_a = {"phones": ["+14155551234"], "full_name": "Alice"}
    record_b = {"phones": ["+14155551234"], "full_name": "Alice Smith-Doe"}
    assert strategy.match(record_a, record_b) is True


def test_match_by_email(strategy):
    record_a = {"emails": ["alice@example.com"], "phones": []}
    record_b = {"emails": ["alice@example.com"], "phones": ["+12345"]}
    assert strategy.match(record_a, record_b) is True


def test_match_by_name(strategy):
    record_a = {"full_name": "Alice   Smith"}
    record_b = {"full_name": "alice smith", "emails": ["diff@example.com"]}
    assert strategy.match(record_a, record_b) is True


def test_no_match_conflicting_identifiers(strategy):
    record_a = {"full_name": "Alice Smith", "phones": ["+111"]}
    record_b = {"full_name": "Bob Jones", "phones": ["+222"]}
    assert strategy.match(record_a, record_b) is False


def test_no_match_empty_records(strategy):
    assert strategy.match({}, {}) is False
