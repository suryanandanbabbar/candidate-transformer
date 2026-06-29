from typing import Any

from candidate_transformer.interfaces.pipeline import PipelineStage
from candidate_transformer.normalizers import normalizer_registry
from candidate_transformer.utils.logger import logger


class NormalizationStage(PipelineStage):
    """
    Applies registered normalizers to specific fields in the intermediate records.
    """

    def execute(self, input_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        try:
            email_normalizer = normalizer_registry.get("email_standard")()
            phone_normalizer = normalizer_registry.get("phone_e164")()
        except Exception as e:
            logger.error("Failed to load normalizers", error=str(e))
            return input_data

        for record in input_data:
            # Normalize emails
            normalized_emails = []
            for email in record.get("emails", []):
                try:
                    normalized_emails.append(email_normalizer.normalize(email))
                except Exception as e:
                    logger.debug("Failed to normalize email", email=email, error=str(e))
            record["emails"] = list(set(normalized_emails))

            # Normalize phones
            normalized_phones = []
            for phone in record.get("phones", []):
                try:
                    normalized_phones.append(phone_normalizer.normalize(phone))
                except Exception as e:
                    logger.debug("Failed to normalize phone", phone=phone, error=str(e))
            record["phones"] = list(set(normalized_phones))

        return input_data
