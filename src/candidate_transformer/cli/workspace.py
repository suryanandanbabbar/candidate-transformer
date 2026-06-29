import json
import os
from pathlib import Path

from candidate_transformer.cli.context import PipelineContext
from candidate_transformer.utils.logger import logger

WORKSPACE_DIR = Path.home() / ".ctsh" / "workspaces"

class WorkspaceManager:
    def __init__(self):
        WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
        
    def _get_path(self, name: str) -> Path:
        return WORKSPACE_DIR / f"{name}.json"
        
    def list_workspaces(self) -> list[str]:
        if not WORKSPACE_DIR.exists():
            return []
        return [p.stem for p in WORKSPACE_DIR.glob("*.json")]
        
    def delete_workspace(self, name: str) -> bool:
        path = self._get_path(name)
        if path.exists():
            path.unlink()
            return True
        return False
        
    def save(self, context: PipelineContext) -> None:
        path = self._get_path(context.workspace_name)
        try:
            # We use model_dump_json for Pydantic v2
            with open(path, "w") as f:
                f.write(context.model_dump_json(indent=2))
        except Exception as e:
            logger.error("Failed to save workspace", error=str(e))
            
    def load(self, name: str) -> PipelineContext | None:
        path = self._get_path(name)
        if not path.exists():
            return None
            
        try:
            with open(path, "r") as f:
                data = json.load(f)
                return PipelineContext.model_validate(data)
        except Exception as e:
            logger.error("Failed to load workspace", error=str(e))
            return None
