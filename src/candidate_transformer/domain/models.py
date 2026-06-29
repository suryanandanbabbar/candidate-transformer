
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
    overall_confidence: float = 0.0

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
