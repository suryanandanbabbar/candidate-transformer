from typing import Any

from candidate_transformer.utils.registry import Registry

normalizer_registry: Registry[Any] = Registry("normalizer")
