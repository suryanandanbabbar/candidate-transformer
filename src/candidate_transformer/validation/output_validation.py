from typing import Any

from candidate_transformer.config import OutputConfig
from candidate_transformer.exceptions import ValidationError


class OutputValidator:
    """
    Validates a projected dictionary against the requested OutputConfig schema.
    """

    def validate(self, data: dict[str, Any], config: OutputConfig) -> None:
        errors = []
        for field in config.fields:
            if field.path not in data and field.required:
                errors.append(f"Missing required field: {field.path}")
                continue

            value = data.get(field.path)

            # Very basic type checking
            if value is not None:
                if field.type == "string" and not isinstance(value, str):
                    errors.append(f"Field {field.path} expected string, got {type(value).__name__}")
                elif field.type == "string[]" and not (
                    isinstance(value, list) and all(isinstance(v, str) for v in value)
                ):
                    errors.append(f"Field {field.path} expected string array, got {type(value).__name__}")
                elif field.type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Field {field.path} expected number, got {type(value).__name__}")

        if errors:
            raise ValidationError(f"Output validation failed: {'; '.join(errors)}")
