from enum import Enum, auto
from pydantic import BaseModel, Field

from candidate_transformer.config import PipelineConfig
from candidate_transformer.domain.models import CanonicalDataset

class DirtyState(Enum):
    NONE = auto()
    PROJECTION = auto()
    CANONICAL = auto()
    WORKSPACE = auto()

def _default_pipeline_config() -> PipelineConfig:
    from candidate_transformer.config import OutputConfig
    return PipelineConfig(output=OutputConfig(fields=[]))

class PipelineContext(BaseModel):
    """
    State representing the entire shell session workspace.
    """
    workspace_name: str = "default"
    loaded_sources: list[tuple[str, str]] = Field(default_factory=list)
    runtime_config: PipelineConfig = Field(default_factory=_default_pipeline_config)
    dataset: CanonicalDataset | None = None
    dirty_state: DirtyState = DirtyState.NONE
    current_projection: str | None = None
    history: list[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

    def mark_dirty(self, state: DirtyState) -> None:
        """
        Updates the dirty state. 
        Higher severity dirty states (CANONICAL) override lower ones (PROJECTION).
        """
        severity = {
            DirtyState.NONE: 0,
            DirtyState.PROJECTION: 1,
            DirtyState.CANONICAL: 2,
            DirtyState.WORKSPACE: 3
        }
        if severity[state] > severity[self.dirty_state]:
            self.dirty_state = state

    def clear_dirty(self) -> None:
        self.dirty_state = DirtyState.NONE
