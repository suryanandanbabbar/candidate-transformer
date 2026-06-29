from typing import Literal, Any

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


class DisplayColumnConfig(BaseModel):
    header: str
    path: str
    format: str | None = None

class DisplaySectionConfig(BaseModel):
    title: str
    fields: list[dict[str, str]] | None = None
    list_path: str | None = None

class DisplayConfig(BaseModel):
    title: str = "Projection Results"
    overview_columns: list[DisplayColumnConfig] = Field(default_factory=list)
    detail_sections: list[DisplaySectionConfig] = Field(default_factory=list)

class OutputConfig(BaseModel):
    """Configuration for the final projected output."""

    fields: list[FieldProjectionConfig]
    display: DisplayConfig | None = None
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
