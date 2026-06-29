import re
from collections.abc import Iterator
from datetime import datetime
from typing import IO

from candidate_transformer.connectors.registry import connector_registry
from candidate_transformer.exceptions import ConnectorError
from candidate_transformer.interfaces.connector import BaseConnector, RawRecord


@connector_registry("resume_text")
class ResumeTextConnector(BaseConnector):
    """
    Connects to an unstructured text file (e.g. converted from PDF/DOCX)
    and extracts fields using deterministic regular expressions.
    Note: Highly brittle due to lack of NLP/ML, but satisfies "no ML" constraints.
    """

    def __init__(self, file_stream: IO[str], source_name: str = "resume_text"):
        self.file_stream = file_stream
        self.source_name = source_name

    def fetch(self) -> Iterator[RawRecord]:
        try:
            text = self.file_stream.read()
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            if not lines:
                return

            email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
            phone_match = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
            name = lines[0] if len(lines[0]) < 50 else None

            sections: dict[str, list[str]] = {}
            current_section = None

            for line in lines[1:]:
                # Heuristic for section headers (all caps, short)
                if line.isupper() and len(line) < 30:
                    current_section = line
                    sections[current_section] = []
                elif current_section:
                    sections[current_section].append(line)

            from typing import Any

            extracted_data: dict[str, Any] = {
                "extracted_email": email_match.group(0) if email_match else None,
                "extracted_phone": phone_match.group(0) if phone_match else None,
                "extracted_name": name,
                "raw_text": text,
            }

            if "LOCATION" in sections and sections["LOCATION"]:
                extracted_data["extracted_location"] = sections["LOCATION"][0]

            if "LINKS" in sections:
                extracted_data["extracted_links"] = sections["LINKS"]

            if "PROFESSIONAL SUMMARY" in sections:
                extracted_data["extracted_summary"] = " ".join(sections["PROFESSIONAL SUMMARY"])

            if "PROJECTS" in sections:
                extracted_data["extracted_projects"] = sections["PROJECTS"]

            if "CERTIFICATIONS" in sections:
                extracted_data["extracted_certifications"] = sections["CERTIFICATIONS"]

            if "LANGUAGES" in sections:
                extracted_data["extracted_languages"] = sections["LANGUAGES"]

            if "SKILLS" in sections:
                extracted_data["extracted_skills"] = " ".join(sections["SKILLS"])

            if "EXPERIENCE" in sections:
                extracted_data["extracted_experience"] = sections["EXPERIENCE"]

            if "EDUCATION" in sections:
                extracted_data["extracted_education"] = sections["EDUCATION"]

            yield RawRecord(
                source_name=self.source_name,
                source_type="resume_text",
                timestamp=datetime.utcnow().isoformat(),
                raw_data={k: v for k, v in extracted_data.items() if v},
            )
        except Exception as e:
            raise ConnectorError(f"Failed to read text from {self.source_name}: {e}") from e
