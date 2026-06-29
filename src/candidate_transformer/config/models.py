from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FieldProjectionConfig(BaseModel):
    """Configuration for a single field in the output schema."""

    path: str
    type: str
    from_path: str | None = Field(None, alias="from")
    required: bool = False
    normalize: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class SourceConfig(BaseModel):
    """Configuration for a data source."""

    connector: str
    input: str


class OutputConfig(BaseModel):
    """Configuration for the final projected output."""

    fields: list[FieldProjectionConfig]
    include_confidence: bool = True
    include_provenance: bool = True
    on_missing: Literal["null", "omit", "error"] = "null"

    model_config = ConfigDict(populate_by_name=True)


class PipelineConfig(BaseModel):
    """Top-level pipeline configuration."""

    output: OutputConfig
    source_priorities: list[str] = Field(default_factory=list)
    sources: list[SourceConfig] | None = None

    model_config = ConfigDict(populate_by_name=True)
