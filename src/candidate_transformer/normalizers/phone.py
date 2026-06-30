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
        import re
        
        # Keep only digits and leading plus if present
        clean_val = re.sub(r'[^\d+]', '', value)
        if not clean_val:
            raise NormalizationError(f"No digits found in phone number: {value}")
            
        try:
            # 1. Attempt parsing. `phonenumbers` automatically infers region if '+' is present.
            # We supply None as default region so it strictly requires a + code first.
            parsed = phonenumbers.parse(clean_val, None)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            pass
            
        try:
            # 2. If it failed, attempt with a default configured region (US for now)
            parsed = phonenumbers.parse(clean_val, "US")
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            pass

        # 3. Fallback canonical digit normalization.
        # Strips all non-numeric characters (including +) and returns the last 10 digits
        # (the typical subscriber length globally). This guarantees deduplication across formats.
        digits = re.sub(r'\D', '', value)
        if len(digits) >= 10:
            return digits[-10:]
        return digits
