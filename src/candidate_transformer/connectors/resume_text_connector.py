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
            # Split into individual resumes by delimiter
            import re
            raw_resumes = re.split(r'\*{5,}', text)
            
            for resume_text in raw_resumes:
                resume_text = resume_text.strip()
                if not resume_text:
                    continue

                lines = [line.strip() for line in resume_text.split("\n") if line.strip()]
                if not lines:
                    continue

                email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", resume_text)
                phone_match = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", resume_text)
                
                name = None
                for line in lines[:10]:
                    # Plausible human name heuristic
                    clean_line = re.sub(r'[^a-zA-Z0-9]', '', line)
                    if not clean_line: continue
                    if "@" in line or "http" in line or "www." in line: continue
                    
                    lower_line = line.lower()
                    if "page " in lower_line or "resume" in lower_line or "curriculum vitae" in lower_line: continue
                    if "contact" in lower_line or "summary" in lower_line or "skills" in lower_line: continue
                    if not any(c.isalpha() for c in line): continue
                    
                    if lower_line.startswith("name:"):
                        name = line[5:].strip()
                    else:
                        name = line
                    break

                # Extract location from a pipe-delimited contact line
                contact_location = None
                for line in lines[:15]:
                    if "|" in line:
                        parts = [p.strip() for p in line.split("|")]
                        for part in parts:
                            if "@" not in part and not re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", part):
                                # It's not an email and not a phone, so it's likely the location
                                if len(part) > 2 and len(part) < 50:
                                    contact_location = part
                                    break
                        if contact_location:
                            break

                sections: dict[str, list[str]] = {}
                current_section = None
                
                section_aliases = {
                    "WORK": "EXPERIENCE",
                    "EMPLOYMENT": "EXPERIENCE",
                    "CAREER HISTORY": "EXPERIENCE",
                    "WORK EXPERIENCE": "EXPERIENCE",
                    "EXPERIENCE": "EXPERIENCE",
                    "EMPLOYMENT HISTORY": "EXPERIENCE",
                    "SKILLS": "SKILLS",
                    "TECHNICAL SKILLS": "SKILLS",
                    "CORE COMPETENCIES": "SKILLS",
                    "EDUCATION": "EDUCATION",
                    "ACADEMICS": "EDUCATION",
                    "PROJECTS": "PROJECTS",
                    "SUMMARY": "PROFESSIONAL SUMMARY",
                    "PROFESSIONAL SUMMARY": "PROFESSIONAL SUMMARY",
                    "CERTIFICATIONS": "CERTIFICATIONS",
                    "LANGUAGES": "LANGUAGES",
                    "LINKS": "LINKS",
                    "LOCATION": "LOCATION",
                    "HEADLINE": "HEADLINE",
                    "TITLE": "HEADLINE",
                }

                for line in lines:
                    if line == name: continue
                    # Normalize header: remove punctuation, trim, uppercase
                    clean_header = re.sub(r'[^\w\s]', '', line).strip().upper()
                    if len(clean_header) > 0 and len(clean_header) < 30 and clean_header in section_aliases:
                        current_section = section_aliases[clean_header]
                        if current_section not in sections:
                            sections[current_section] = []
                    elif current_section:
                        sections[current_section].append(line)

                from typing import Any

                extracted_data: dict[str, Any] = {
                    "extracted_email": email_match.group(0) if email_match else None,
                    "extracted_phone": phone_match.group(0) if phone_match else None,
                    "extracted_name": name,
                    "raw_text": resume_text,
                }

                if "LOCATION" in sections and sections["LOCATION"]:
                    extracted_data["extracted_location"] = sections["LOCATION"][0]
                elif contact_location:
                    extracted_data["extracted_location"] = contact_location

                if "HEADLINE" in sections and sections["HEADLINE"]:
                    extracted_data["headline"] = sections["HEADLINE"][0]

                # Extract all URLs from the resume text using regex
                url_matches = re.findall(r'https?://[^\s]+|www\.[^\s]+', resume_text)
                if url_matches:
                    extracted_data["extracted_links"] = url_matches

                if "LINKS" in sections:
                    if "extracted_links" not in extracted_data:
                        extracted_data["extracted_links"] = []
                    extracted_data["extracted_links"].extend(sections["LINKS"])

                if "PROFESSIONAL SUMMARY" in sections:
                    extracted_data["extracted_summary"] = " ".join(sections["PROFESSIONAL SUMMARY"])

                if "PROJECTS" in sections:
                    extracted_data["extracted_projects"] = sections["PROJECTS"]

                if "CERTIFICATIONS" in sections:
                    extracted_data["extracted_certifications"] = sections["CERTIFICATIONS"]

                if "LANGUAGES" in sections:
                    extracted_data["extracted_languages"] = sections["LANGUAGES"]

                if "SKILLS" in sections:
                    # Keep as list instead of joining
                    extracted_data["extracted_skills"] = sections["SKILLS"]

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
