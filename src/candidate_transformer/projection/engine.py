import re
from typing import Any

from candidate_transformer.config import OutputConfig
from candidate_transformer.domain import Candidate
from candidate_transformer.exceptions import ProjectionError
from candidate_transformer.normalizers import normalizer_registry


class ProjectionEngine:
    """
    Reshapes a Candidate domain model into a final output dictionary
    based on a user-provided OutputConfig.
    """

    def project(self, candidate: Candidate, config: OutputConfig) -> dict[str, Any]:
        result: dict[str, Any] = {}
        data = candidate.model_dump()

        for field_config in config.fields:
            # Determine source path
            source_path = field_config.from_path if field_config.from_path else field_config.path

            # Extract value
            value = self._extract_value(data, source_path)

            # Apply normalizer if requested
            # Bypass normalization for companies_worked_at to preserve original strings
            should_normalize = field_config.normalize and field_config.path != "companies_worked_at"
            if value is not None and should_normalize:
                try:
                    normalizer = normalizer_registry.get(field_config.normalize)()
                    if isinstance(value, list):
                        value = [normalizer.normalize(v) for v in value]
                    else:
                        value = normalizer.normalize(value)
                except Exception:
                    # In a real system, we might log a warning and fallback based on on_missing
                    value = None

            # Analytics specific deduplication
            if field_config.path in ("companies_worked_at", "degrees") and isinstance(value, list):
                deduped = []
                seen = set()
                for item in value:
                    if item and item not in seen:
                        seen.add(item)
                        deduped.append(item)
                value = deduped

            # Handle missing values
            if value is None or (isinstance(value, list) and not value):
                if field_config.required and config.on_missing == "error":
                    raise ProjectionError(f"Required field '{field_config.path}' is missing.")
                elif config.on_missing == "omit":
                    continue
                else:
                    value = None

            # Assign to output path
            result[field_config.path] = value

        # Optional inclusions
        if config.include_confidence:
            result["overall_confidence"] = candidate.overall_confidence
        if config.include_provenance:
            raw_prov = [model.model_dump() for model in candidate.provenance]
            # Deduplicate just in case
            seen = set()
            dedup_prov = []
            for p in raw_prov:
                # Deduplicate by field and source to be strict, as requested
                key = (p.get("field"), p.get("source"))
                if key not in seen:
                    seen.add(key)
                    dedup_prov.append(p)
            result["provenance"] = dedup_prov

        return result

    def _extract_value(self, data: Any, path: str) -> Any:
        """
        Extract a value from a nested dictionary using a simple path syntax.
        E.g., "contact.emails[0]" or "skills[].name"
        """
        parts = re.split(r"\.|\[|\]", path)
        parts = [p for p in parts if p]  # Remove empty strings from split

        current = data
        for i, part in enumerate(parts):
            if current is None:
                return None

            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list):
                if part.isdigit():
                    idx = int(part)
                    if idx < len(current):
                        current = current[idx]
                    else:
                        return None
                else:
                    # It's an array mapping (e.g., skills[].name)
                    remaining_path = ".".join(parts[i:])
                    return [self._extract_value(item, remaining_path) for item in current]
            else:
                return None

        return current
