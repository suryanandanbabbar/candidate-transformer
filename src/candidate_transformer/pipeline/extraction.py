import uuid
from typing import Any

from candidate_transformer.interfaces.connector import RawRecord
from candidate_transformer.interfaces.pipeline import PipelineStage


class ExtractionStage(PipelineStage):
    """
    Normalizes heterogeneous input into a standard intermediate dictionary structure.
    """

    def execute(self, input_data: list[RawRecord]) -> list[dict[str, Any]]:
        extracted_records = []

        # Normalization Helpers
        def norm_country(c: str) -> str:
            c = c.strip()
            cmap = {
                "united states": "US", "usa": "US", "us": "US",
                "united kingdom": "GB", "uk": "GB", "england": "GB", "gb": "GB",
                "india": "IN", "in": "IN"
            }
            return cmap.get(c.lower(), c)

        def norm_region(r: str) -> str:
            r = r.strip()
            rmap = {
                "california": "CA", "new york": "NY", "texas": "TX"
            }
            return rmap.get(r.lower(), r)

        def clean_url(u: str) -> str | None:
            u = u.strip()
            if not u:
                return None
            if u.startswith("www."):
                u = "https://" + u
            elif not u.startswith("http"):
                if "." in u and " " not in u:
                    u = "https://" + u
                else:
                    return None
            return u.rstrip("/")

        for raw in input_data:
            data = raw.raw_data

            # In a full system, this might use mapping configs.
            # Here we do heuristic mapping.
            record: dict[str, Any] = {
                "__source__": raw.source_name,
                "__timestamp__": raw.timestamp,
                "__id__": str(uuid.uuid4()),
            }

            # Map Name
            if data.get("full_name"):
                record["full_name"] = data.get("full_name")
            elif data.get("name"):
                record["full_name"] = data.get("name")
            elif data.get("extracted_name"):
                record["full_name"] = data.get("extracted_name")
            elif data.get("first_name") and data.get("last_name"):
                record["full_name"] = f"{data.get('first_name')} {data.get('last_name')}"

            # Map Emails
            emails = []
            if data.get("email"):
                emails.append(data.get("email"))
            if data.get("primary_email"):
                emails.append(data.get("primary_email"))
            if data.get("secondary_email"):
                emails.append(data.get("secondary_email"))
            if data.get("extracted_email"):
                emails.append(data.get("extracted_email"))
            if data.get("contact") and isinstance(data["contact"], dict):
                if data["contact"].get("email"):
                    emails.append(data["contact"]["email"])
                if data["contact"].get("alternate_email"):
                    emails.append(data["contact"]["alternate_email"])
            record["emails"] = emails

            # Map Phones
            phones = []
            if data.get("phone"):
                phones.append(data.get("phone"))
            if data.get("primary_phone"):
                phones.append(data.get("primary_phone"))
            if data.get("secondary_phone"):
                phones.append(data.get("secondary_phone"))
            if data.get("mobile"):
                phones.append(data.get("mobile"))
            if data.get("extracted_phone"):
                phones.append(data.get("extracted_phone"))
            if data.get("contact") and isinstance(data["contact"], dict):
                if data["contact"].get("mobile"):
                    phones.append(data["contact"]["mobile"])
                if data["contact"].get("phone"):
                    phones.append(data["contact"]["phone"])
                if data["contact"].get("home_phone"):
                    phones.append(data["contact"]["home_phone"])
            record["phones"] = phones

            # Map Skills
            if data.get("skills"):
                if isinstance(data["skills"], list):
                    record["skills"] = data["skills"]
                elif isinstance(data["skills"], str):
                    record["skills"] = [s.strip() for s in data["skills"].replace(";", ",").split(",") if s.strip()]
            elif data.get("extracted_skills"):
                record["skills"] = [
                    s.strip() for s in data.get("extracted_skills", "").replace(";", ",").split(",") if s.strip()
                ]

            # Map Experience
            experiences = []
            exp_years = data.get("years_experience")
            if exp_years:
                try:
                    record["years_experience"] = float(exp_years)
                except ValueError:
                    pass

            if data.get("current_company") and data.get("title"):
                experiences.append({"company": data.get("current_company"), "title": data.get("title")})
            if data.get("employment_history") and isinstance(data["employment_history"], list):
                for exp in data["employment_history"]:
                    experiences.append(
                        {
                            "company": exp.get("employer", ""),
                            "title": exp.get("job_title", ""),
                            "start": exp.get("start_date"),
                            "end": exp.get("end_date"),
                            "summary": exp.get("summary"),
                        }
                    )
            if data.get("extracted_experience"):
                for line in data.get("extracted_experience", []):
                    if "-" in line:
                        parts = line.split("-", 1)
                        experiences.append({"company": parts[0].strip(), "title": parts[1].strip()})
            record["experience"] = experiences

            # Map Education
            education = []
            if data.get("education") and isinstance(data["education"], list):
                for ed in data["education"]:
                    education.append(
                        {
                            "institution": ed.get("school", ""),
                            "degree": ed.get("degree", ""),
                            "field": ed.get("field", ""),
                            "end_year": ed.get("grad_year"),
                        }
                    )
            if data.get("extracted_education"):
                lines = data.get("extracted_education", [])
                if len(lines) >= 2:
                    education.append({"institution": lines[0], "degree": lines[1]})
            record["education"] = education

            # Map New Fields
            if data.get("headline"):
                record["headline"] = data["headline"]

            if data.get("extracted_summary"):
                record["summary"] = data["extracted_summary"]

            if data.get("extracted_certifications"):
                record["certifications"] = data["extracted_certifications"]

            if data.get("extracted_languages"):
                record["languages"] = data["extracted_languages"]

            if data.get("extracted_projects"):
                projects = []
                # Vocabulary for extracting technologies
                tech_vocab = {"kafka", "spark", "python", "go", "java", "aws", "docker", "kubernetes", "react", "node"}
                for p in data["extracted_projects"]:
                    name = ""
                    desc = ""
                    technologies = []
                    
                    parts = p.split("-", 1)
                    if len(parts) == 2:
                        name = parts[0].strip()
                        desc = parts[1].strip()
                    else:
                        name = p.strip()
                        desc = name  # Fallback
                    
                    import re
                    # Simple heuristic: look for words in description matching our vocab
                    words = re.findall(r'\b[a-zA-Z]+\b', desc.lower())
                    for w in words:
                        if w in tech_vocab:
                            # Use original capitalization if we wanted, but we'll title case for standard
                            technologies.append(w.title() if w not in {"aws"} else w.upper())
                            
                    # Remove duplicates
                    technologies = list(dict.fromkeys(technologies))
                    
                    proj_obj: dict[str, Any] = {"name": name}
                    if desc and desc != name:
                        proj_obj["description"] = desc
                    if technologies:
                        proj_obj["technologies"] = technologies
                        
                    projects.append(proj_obj)
                record["projects"] = projects

            # Map Links
            links: dict[str, Any] = {"other": []}

            def add_link(raw_url: str) -> None:
                u = clean_url(raw_url)
                if not u:
                    return

                # Check uniqueness across all fields
                all_urls = [links.get("linkedin"), links.get("github"), links.get("portfolio")] + links.get("other", [])  # noqa: B023
                if u in all_urls:
                    return

                if "linkedin.com" in u and not links.get("linkedin"):  # noqa: B023
                    links["linkedin"] = u  # noqa: B023
                elif "github.com" in u and not links.get("github"):  # noqa: B023
                    links["github"] = u  # noqa: B023
                elif ("portfolio" in raw_url.lower() or "dev" in u) and not links.get("portfolio"):  # noqa: B023
                    links["portfolio"] = u  # noqa: B023
                else:
                    links["other"].append(u)  # noqa: B023

            if data.get("linkedin"):
                add_link(data["linkedin"])
            if data.get("github"):
                add_link(data["github"])
            if data.get("portfolio"):
                add_link(data["portfolio"])

            if data.get("extracted_links"):
                for link in data["extracted_links"]:
                    add_link(link)

            if links:
                record["links"] = links

            # Map Location
            location = {}
            if data.get("city"):
                location["city"] = data["city"].title()
            if data.get("region"):
                location["region"] = norm_region(data["region"])
            if data.get("country"):
                location["country"] = norm_country(data["country"])

            if data.get("contact") and data["contact"].get("location"):
                loc_dict = data["contact"]["location"]
                if loc_dict.get("city") and not location.get("city"):
                    location["city"] = loc_dict["city"].title()
                if loc_dict.get("region") and not location.get("region"):
                    location["region"] = norm_region(loc_dict["region"])
                if loc_dict.get("country") and not location.get("country"):
                    location["country"] = norm_country(loc_dict["country"])

            if data.get("extracted_location"):
                parts = [p.strip() for p in data["extracted_location"].split(",")]
                if len(parts) >= 1 and not location.get("city"):
                    location["city"] = parts[0].title()
                if len(parts) >= 2 and not location.get("region"):
                    location["region"] = norm_region(parts[1])
                if len(parts) >= 3 and not location.get("country"):
                    location["country"] = norm_country(parts[2])

            if location:
                record["location"] = location
            else:
                record["location"] = None

            extracted_records.append(record)

        return extracted_records
