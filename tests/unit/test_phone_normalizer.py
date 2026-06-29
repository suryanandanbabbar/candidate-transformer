import pytest

from candidate_transformer.exceptions import NormalizationError
from candidate_transformer.normalizers.phone import E164PhoneNormalizer


def test_phone_normalizer_valid():
    normalizer = E164PhoneNormalizer()
    assert normalizer.normalize("(415) 555-1234") == "+14155551234"
    assert normalizer.normalize("415.555.1234") == "+14155551234"
    assert normalizer.normalize("+44 20 7123 4567") == "+442071234567"


def test_phone_normalizer_invalid():
    normalizer = E164PhoneNormalizer()
    with pytest.raises(NormalizationError):
        normalizer.normalize("not-a-phone-number")
    with pytest.raises(NormalizationError):
        normalizer.normalize("123")  # Too short
