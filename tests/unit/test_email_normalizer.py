import pytest

from candidate_transformer.exceptions import NormalizationError
from candidate_transformer.normalizers.email import StandardEmailNormalizer


def test_email_normalizer_valid():
    normalizer = StandardEmailNormalizer()
    assert normalizer.normalize("  Test@Example.COM  ") == "test@example.com"
    assert normalizer.normalize("alice.smith+spam@example.co.uk") == "alice.smith+spam@example.co.uk"


def test_email_normalizer_invalid():
    normalizer = StandardEmailNormalizer()
    with pytest.raises(NormalizationError):
        normalizer.normalize("not-an-email")
    with pytest.raises(NormalizationError):
        normalizer.normalize("missing@domain")
