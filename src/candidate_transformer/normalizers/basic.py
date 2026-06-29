from typing import Any

from candidate_transformer.interfaces.normalizer import Normalizer
from candidate_transformer.normalizers.registry import normalizer_registry
from candidate_transformer.normalizers.phone import E164PhoneNormalizer

# Alias for E164
normalizer_registry.register("E164", E164PhoneNormalizer)


@normalizer_registry("lowercase")
class LowercaseNormalizer:
    def normalize(self, value: Any) -> Any:
        if isinstance(value, str):
            return value.lower()
        return value


@normalizer_registry("trim")
class TrimNormalizer:
    def normalize(self, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value


@normalizer_registry("canonical")
class CanonicalNormalizer:
    def normalize(self, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().title()
        return value
