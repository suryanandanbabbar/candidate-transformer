import uuid
from typing import Any

from candidate_transformer.domain.models import (
    Candidate,
    ContactInformation,
    Education,
    Experience,
    Links,
    Project,
    Provenance,
    Skill,
)
from candidate_transformer.interfaces.pipeline import PipelineStage
from candidate_transformer.strategies import strategy_registry


class ConflictResolutionStage(PipelineStage):
    """
    Takes grouped intermediate records and merges them into a Canonical Candidate.
    Uses the configured conflict resolution strategy.
    """

    def __init__(self, source_priorities: list[str]):
        self.source_priorities = source_priorities

    def execute(self, input_data: list[list[dict[str, Any]]]) -> list[Candidate]:
        if not input_data:
            return []

        strategy = strategy_registry.get("priority_conflict_resolution")()
        candidates = []

        for group in input_data:
            if not group:
                continue

            candidate_id = group[0].get("__id__", str(uuid.uuid4()))
            provenance: list[Provenance] = []

            # Helper for scalars
            def resolve_and_prov(
                field_name: str, g: list[dict[str, Any]] = group, p: list[Provenance] = provenance
            ) -> Any:
                val, prov = self._resolve_scalar(g, field_name, strategy)
                if prov:
                    p.append(prov)
                return val

            full_name = resolve_and_prov("full_name")
            years_experience = resolve_and_prov("years_experience")
            headline = resolve_and_prov("headline")
            summary = resolve_and_prov("summary")

            # Lists
            emails, email_prov = self._collect_list_with_prov(group, "emails")
            phones, phone_prov = self._collect_list_with_prov(group, "phones")
            certifications, cert_prov = self._collect_list_with_prov(group, "certifications")
            languages, lang_prov = self._collect_list_with_prov(group, "languages")

            emails.sort()
            phones.sort()
            certifications.sort()
            languages.sort()

            provenance.extend(email_prov)
            provenance.extend(phone_prov)
            provenance.extend(cert_prov)
            provenance.extend(lang_prov)

            # Complex lists
            experiences, exp_prov = self._collect_experience_with_prov(group)
            education, edu_prov = self._collect_education_with_prov(group)
            projects, proj_prov = self._collect_projects_with_prov(group)

            experiences.sort(key=lambda x: str(x.get("start", "")), reverse=True)
            education.sort(key=lambda x: str(x.get("end_year", "")), reverse=True)

            provenance.extend(exp_prov)
            provenance.extend(edu_prov)
            provenance.extend(proj_prov)

            # Dict merges
            location, loc_prov = self._merge_dict_with_prov(group, "location")
            links, links_prov = self._merge_dict_with_prov(group, "links")
            provenance.extend(loc_prov)
            provenance.extend(links_prov)

            # Skills
            skills, skill_prov = self._collect_skills_with_prov(group)
            provenance.extend(skill_prov)

            # Deduplicate entire provenance list by (field, source)
            unique_prov = []
            seen_prov = set()
            for p in provenance:
                k = (p.field, p.source)
                if k not in seen_prov:
                    seen_prov.add(k)
                    unique_prov.append(p)

            unique_prov.sort(key=lambda x: (x.field, x.source))

            # Generate deterministic candidate ID using UUIDv5
            id_str = f"{full_name or 'Unknown'}-{emails[0] if emails else ''}-{phones[0] if phones else ''}"
            candidate_id = str(uuid.uuid5(uuid.NAMESPACE_OID, id_str))

            candidate = Candidate(
                candidate_id=candidate_id,
                full_name=full_name or "Unknown",
                years_experience=years_experience,
                headline=headline,
                summary=summary,
                contact=ContactInformation(emails=emails, phones=phones, location=location),
                links=Links(**links),
                skills=skills,
                experience=[Experience(**e) for e in experiences],
                education=[Education(**e) for e in education],
                certifications=certifications,
                projects=[Project(**p) for p in projects],
                languages=languages,
                provenance=unique_prov,
            )
            candidates.append(candidate)

        return candidates

    def _resolve_scalar(self, group: list[dict[str, Any]], field: str, strategy: Any) -> tuple[Any, Provenance | None]:
        values = []
        for record in group:
            if record.get(field):
                values.append(
                    {
                        "value": record[field],
                        "source": record.get("__source__", "unknown"),
                        "timestamp": record.get("__timestamp__"),
                    }
                )
        if not values:
            return None, None

        resolved_value = strategy.resolve(values, {"source_priorities": self.source_priorities})

        source = "unknown"
        timestamp = None
        for v in values:
            if v["value"] == resolved_value:
                source = v["source"]
                timestamp = v.get("timestamp")
                break

        prov = Provenance(
            field=field,
            source=source,
            method="priority_resolution",
            timestamp=timestamp,
            confidence=1.0,
        )
        return resolved_value, prov

    def _collect_list_with_prov(self, group: list[dict[str, Any]], field: str) -> tuple[list[Any], list[Provenance]]:
        result = []
        provs = []
        for record in group:
            if record.get(field) and isinstance(record[field], list):
                for item in record[field]:
                    if item not in result:
                        result.append(item)
                provs.append(
                    Provenance(
                        field=field,
                        source=record.get("__source__", "unknown"),
                        method="union_merge",
                        timestamp=record.get("__timestamp__"),
                    )
                )
        return result, provs

    def _collect_experience_with_prov(self, group: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[Provenance]]:
        result_map = {}
        provs = []

        def normalize_title(title: str) -> str:
            t = title.strip().lower()
            replacements = {
                r"\bsr\.?\b": "senior",
                r"\bmgr\b": "manager",
                r"\bdev\b": "developer",
                r"\bengr\b": "engineer",
            }
            import re
            for pattern, repl in replacements.items():
                t = re.sub(pattern, repl, t)
            return t.strip()

        for record in group:
            if record.get("experience") and isinstance(record["experience"], list):
                source = record.get("__source__", "unknown")
                provs.append(Provenance(field="experience", source=source, method="deduplication", timestamp=record.get("__timestamp__")))
                for exp in record["experience"]:
                    comp = str(exp.get("company", "")).strip().lower()
                    raw_title = str(exp.get("title", ""))
                    norm_title = normalize_title(raw_title)
                    key = (comp, norm_title)
                    
                    if key not in result_map:
                        result_map[key] = dict(exp)
                    else:
                        existing = result_map[key]
                        # Prefer non-null dates
                        if not existing.get("start") and exp.get("start"):
                            existing["start"] = exp.get("start")
                        if not existing.get("end") and exp.get("end"):
                            existing["end"] = exp.get("end")
                        # Prefer richer summaries
                        if len(str(exp.get("summary", ""))) > len(str(existing.get("summary", ""))):
                            existing["summary"] = exp.get("summary")
                        # Prefer richer titles and company names
                        if len(str(exp.get("title", ""))) > len(str(existing.get("title", ""))):
                            existing["title"] = exp.get("title")
                        if len(str(exp.get("company", ""))) > len(str(existing.get("company", ""))):
                            existing["company"] = exp.get("company")
        return list(result_map.values()), provs

    def _collect_education_with_prov(self, group: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[Provenance]]:
        result_map = {}
        provs = []
        for record in group:
            if record.get("education") and isinstance(record["education"], list):
                source = record.get("__source__", "unknown")
                provs.append(Provenance(field="education", source=source, method="deduplication", timestamp=record.get("__timestamp__")))
                for edu in record["education"]:
                    inst = str(edu.get("institution", "")).strip().lower()
                    deg = str(edu.get("degree", "")).strip().lower()
                    field = str(edu.get("field", "")).strip().lower()
                    
                    # Compute key without end_year to allow merging matching institutions/degrees/fields
                    key = (inst, deg, field)
                    
                    if key not in result_map:
                        result_map[key] = dict(edu)
                    else:
                        existing = result_map[key]
                        # Prefer non-null fields
                        if not existing.get("degree") and edu.get("degree"):
                            existing["degree"] = edu.get("degree")
                        if not existing.get("field") and edu.get("field"):
                            existing["field"] = edu.get("field")
                        if not existing.get("end_year") and edu.get("end_year"):
                            existing["end_year"] = edu.get("end_year")
        return list(result_map.values()), provs

    def _collect_projects_with_prov(self, group: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[Provenance]]:
        result_map = {}
        provs = []
        for record in group:
            if record.get("projects") and isinstance(record["projects"], list):
                source = record.get("__source__", "unknown")
                provs.append(Provenance(field="projects", source=source, method="deduplication", timestamp=record.get("__timestamp__")))
                for proj in record["projects"]:
                    name = str(proj.get("name", "")).strip().lower()
                    if name not in result_map:
                        result_map[name] = dict(proj)
                    else:
                        existing = result_map[name]
                        if len(str(proj.get("description", ""))) > len(str(existing.get("description", ""))):
                            existing["description"] = proj.get("description")
                        if proj.get("technologies"):
                            existing_tech = existing.get("technologies", [])
                            existing["technologies"] = list(set(existing_tech + proj["technologies"]))
        return list(result_map.values()), provs

    def _merge_dict_with_prov(self, group: list[dict[str, Any]], field: str) -> tuple[dict[str, Any], list[Provenance]]:
        result = {}
        provs = []
        for record in group:
            if record.get(field) and isinstance(record[field], dict):
                result.update(record[field])
                provs.append(
                    Provenance(
                        field=field,
                        source=record.get("__source__", "unknown"),
                        method="dict_merge",
                        timestamp=record.get("__timestamp__"),
                    )
                )
        return result, provs

    def _collect_skills_with_prov(self, group: list[dict[str, Any]]) -> tuple[list[Skill], list[Provenance]]:
        # Map of canonical_skill_name -> list of (original_name, source)
        skill_map: dict[str, dict[str, Any]] = {}
        provs = []

        for record in group:
            source = record.get("__source__", "unknown")
            if record.get("skills") and isinstance(record["skills"], list):
                provs.append(
                    Provenance(
                        field="skills", source=source, method="union_merge", timestamp=record.get("__timestamp__")
                    )
                )
                for s in record["skills"]:
                    # Canonicalize: lowercase and trim.
                    canonical = s.strip().lower()
                    if canonical not in skill_map:
                        skill_map[canonical] = {"name": s.strip(), "sources": set()}
                    skill_map[canonical]["sources"].add(source)

        skills = []
        for v in skill_map.values():
            skills.append(Skill(name=v["name"], sources=sorted(list(v["sources"])), confidence=1.0))

        return skills, provs
