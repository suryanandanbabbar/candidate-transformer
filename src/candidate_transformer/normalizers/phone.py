import phonenumbers

from candidate_transformer.exceptions import NormalizationError
from candidate_transformer.interfaces.normalizer import Normalizer
from candidate_transformer.normalizers.registry import normalizer_registry


@normalizer_registry("phone_e164")
class E164PhoneNormalizer(Normalizer[str]):
    """
    Normalizes phone numbers to E.164 format.
    """

    def normalize(self, value: str) -> str:
        try:
            # Assume US/CA as default region if country code is missing
            parsed = phonenumbers.parse(value, "US")
            if not phonenumbers.is_valid_number(parsed):
                raise NormalizationError(f"Invalid phone number: {value}")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException as e:
            raise NormalizationError(f"Could not parse phone number {value}: {e}") from e
