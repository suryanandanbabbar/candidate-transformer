
from pydantic import BaseModel, Field


class Provenance(BaseModel):
    """Tracks the origin and methodology of a specific attribute's extraction."""

    field: str
    source: str
    method: str
    timestamp: str | None = None
    confidence: float = 1.0


class Confidence(BaseModel):
    """Represents a confidence score, optionally with reasoning."""

    score: float
    reasoning: str | None = None


class ContactInformation(BaseModel):
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    location: dict[str, str | None] | None = None  # city, region, country


class Experience(BaseModel):
    company: str
    title: str
    start: str | None = None
    end: str | None = None
    summary: str | None = None


class Education(BaseModel):
    institution: str
    degree: str | None = None
    field: str | None = None
    end_year: int | None = None


class Skill(BaseModel):
    name: str
    confidence: float = 1.0
    sources: list[str] = Field(default_factory=list)


class Project(BaseModel):
    name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)


class Links(BaseModel):
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    other: list[str] = Field(default_factory=list)


class Candidate(BaseModel):
    """
    The canonical, unified domain model representing a Candidate.
    This model strictly separates domain logic from I/O representations.
    """

    candidate_id: str
    full_name: str
    contact: ContactInformation = Field(default_factory=ContactInformation)
    links: Links = Field(default_factory=Links)
    headline: str | None = None
    summary: str | None = None
    years_experience: float | None = None
    skills: list[Skill] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    provenance: list[Provenance] = Field(default_factory=list)
    overall_confidence: float = Field(
        default=0.0,
        description="Represents confidence in the merged candidate profile after source reconciliation. "
                    "This is not the arithmetic average of individual field confidences. "
                    "It reflects the overall quality and completeness of the merged canonical profile."
    )

    @property
    def computed_experience(self) -> float | None:
        import datetime
        from dateutil import parser
        import re
        intervals = []
        for exp in self.experience:
            start_str = exp.start
            end_str = exp.end
            if not start_str:
                continue
            
            try:
                start_dt = parser.parse(start_str)
            except Exception:
                continue
                
            end_dt = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
            if end_str and end_str.lower() not in ("present", "current", "now", ""):
                try:
                    end_dt = parser.parse(end_str)
                except Exception:
                    pass
            
            if start_dt.tzinfo: start_dt = start_dt.replace(tzinfo=None)
            if end_dt.tzinfo: end_dt = end_dt.replace(tzinfo=None)
            
            if start_dt > end_dt:
                start_dt, end_dt = end_dt, start_dt
                
            intervals.append((start_dt, end_dt))
            
        if not intervals:
            if self.years_experience is not None:
                return float(self.years_experience)
            if self.summary:
                match = re.search(r'(\d+)\+?\s*years?\s*of\s*(?:expertise|experience)', self.summary, re.IGNORECASE)
                if match:
                    return float(match.group(1))
            return None
            
        intervals.sort(key=lambda x: x[0])
        merged = []
        for current in intervals:
            if not merged:
                merged.append(current)
            else:
                last = merged[-1]
                if current[0] <= last[1]:
                    merged[-1] = (last[0], max(last[1], current[1]))
                else:
                    merged.append(current)
                    
        total_days = sum((e - s).days for s, e in merged)
        return round(total_days / 365.25, 2)

class CanonicalDataset(BaseModel):
    """
    Immutable representation of a completely built canonical transformation run.
    Contains candidates, diagnostics, statistics, and run metadata.
    """
    
    candidates: list[Candidate] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    statistics: dict[str, float | int | str] = Field(default_factory=dict)
    build_metadata: dict[str, float | int | str] = Field(default_factory=dict)
    connector_metadata: dict[str, int] = Field(default_factory=dict)
    schema_version: str = "1.0"
    build_timestamp: str = ""
    build_id: str = ""
