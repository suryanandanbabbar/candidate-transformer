import re

from candidate_transformer.exceptions import NormalizationError
from candidate_transformer.interfaces.normalizer import Normalizer
from candidate_transformer.normalizers.registry import normalizer_registry


@normalizer_registry("email_standard")
class StandardEmailNormalizer(Normalizer[str]):
    """
    Normalizes emails to lowercase, strips whitespace, and validates basic format.
    """

    def normalize(self, value: str) -> str:
        cleaned = str(value).strip().lower()
        if not re.match(r"^[\w\.\+-]+@[\w\.-]+\.\w+$", cleaned):
            raise NormalizationError(f"Invalid email format: {value}")
        return cleaned
