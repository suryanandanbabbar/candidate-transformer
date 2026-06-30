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
            name_keys = ["full_name", "name", "Candidate Name", "candidate_name", "extracted_name"]
            for k in name_keys:
                if data.get(k):
                    record["full_name"] = data.get(k)
                    break
            
            if "full_name" not in record and data.get("first_name") and data.get("last_name"):
                record["full_name"] = f"{data.get('first_name')} {data.get('last_name')}"

            # Map Emails
            emails = []
            email_keys = ["email", "primary_email", "secondary_email", "extracted_email", "Email Address", "email_address"]
            for k in email_keys:
                if data.get(k):
                    emails.append(data.get(k))
                    
            if data.get("contact") and isinstance(data["contact"], dict):
                if data["contact"].get("email"):
                    emails.append(data["contact"]["email"])
                if data["contact"].get("alternate_email"):
                    emails.append(data["contact"]["alternate_email"])
            record["emails"] = emails

            # Map Phones
            phones = []
            phone_keys = ["phone", "primary_phone", "secondary_phone", "mobile", "extracted_phone", "Phone Number", "phone_number"]
            for k in phone_keys:
                if data.get(k):
                    phones.append(data.get(k))
                    
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
                    record["skills"] = [s.lstrip('- ').strip() for s in data["skills"] if s.strip()]
                elif isinstance(data["skills"], str):
                    record["skills"] = [s.strip() for s in data["skills"].replace(";", ",").split(",") if s.strip()]
            elif data.get("extracted_skills"):
                if isinstance(data["extracted_skills"], list):
                    record["skills"] = [s.lstrip('- ').strip() for s in data["extracted_skills"] if s.strip()]
                else:
                    record["skills"] = [
                        s.strip() for s in data.get("extracted_skills", "").replace(";", ",").split(",") if s.strip()
                    ]

            # Map Experience
            experiences = []
            exp_keys = ["years_experience", "Years Experience", "Experience (Years)", "experience_years", "Years of Experience"]
            exp_years = next((data.get(k) for k in exp_keys if data.get(k) is not None), None)
            if exp_years is not None:
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
                import re
                current_exp = None
                for line in data.get("extracted_experience", []):
                    line = line.strip()
                    if not line:
                        continue
                    
                    if line.startswith(('*', '-', '•')):
                        if current_exp is not None:
                            bullet = line.lstrip('*-•').strip()
                            if current_exp.get("summary"):
                                current_exp["summary"] += f"\n- {bullet}"
                            else:
                                current_exp["summary"] = f"- {bullet}"
                        continue

                    # Try to parse "Title at Company (Date)" format
                    match = re.search(r"(.+?) at (.+?) \((.+?)\)", line)
                    if match:
                        current_exp = {"title": match.group(1).strip(), "company": match.group(2).strip()}
                        date_str = match.group(3).strip()
                        if " - " in date_str:
                            start, end = date_str.split(" - ", 1)
                            current_exp["start"] = start.strip()
                            current_exp["end"] = end.strip()
                        elif "-" in date_str:
                            start, end = date_str.split("-", 1)
                            current_exp["start"] = start.strip()
                            current_exp["end"] = end.strip()
                        experiences.append(current_exp)
                    elif "-" in line:
                        parts = line.split("-", 1)
                        current_exp = {"company": parts[0].strip(), "title": parts[1].strip()}
                        experiences.append(current_exp)
                    else:
                        current_exp = {"company": line.strip(), "title": ""}
                        experiences.append(current_exp)
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
                for line in lines:
                    parts = line.split(",", 1)
                    if len(parts) == 2:
                        education.append({"degree": parts[0].strip(), "institution": parts[1].strip()})
                    else:
                        education.append({"institution": line.strip(), "degree": ""})
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

            if data.get("linkedin") or data.get("LinkedIn"):
                add_link(data.get("linkedin") or data.get("LinkedIn"))
            if data.get("github") or data.get("GitHub"):
                add_link(data.get("github") or data.get("GitHub"))
            if data.get("portfolio") or data.get("Portfolio"):
                add_link(data.get("portfolio") or data.get("Portfolio"))

            if data.get("extracted_links"):
                for link in data["extracted_links"]:
                    add_link(link)

            if links:
                record["links"] = links

            # Map Location
            location = {"city": None, "region": None, "country": None}
            has_location = False
            
            if data.get("city"):
                location["city"] = data["city"].title()
                has_location = True
            if data.get("region"):
                location["region"] = norm_region(data["region"])
                has_location = True
            if data.get("country"):
                location["country"] = norm_country(data["country"])
                has_location = True

            if data.get("contact") and data["contact"].get("location"):
                loc_dict = data["contact"]["location"]
                if loc_dict.get("city") and not location.get("city"):
                    location["city"] = loc_dict["city"].title()
                    has_location = True
                if loc_dict.get("region") and not location.get("region"):
                    location["region"] = norm_region(loc_dict["region"])
                    has_location = True
                if loc_dict.get("country") and not location.get("country"):
                    location["country"] = norm_country(loc_dict["country"])
                    has_location = True

            if data.get("extracted_location"):
                parts = [p.strip() for p in data["extracted_location"].split(",")]
                if len(parts) >= 1 and not location.get("city"):
                    location["city"] = parts[0].title()
                    has_location = True
                if len(parts) >= 2 and not location.get("region"):
                    location["region"] = norm_region(parts[1])
                    has_location = True
                if len(parts) >= 3 and not location.get("country"):
                    location["country"] = norm_country(parts[2])
                    has_location = True

            if has_location:
                record["location"] = location
            else:
                record["location"] = None

            extracted_records.append(record)

        return extracted_records
