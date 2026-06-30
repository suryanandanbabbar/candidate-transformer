import datetime
from typing import Any

from candidate_transformer.cli.context import PipelineContext

def generate_metadata(context: PipelineContext, projection_name: str = "analytics") -> dict[str, Any]:
    dataset = context.dataset
    if not dataset:
        raise ValueError("Cannot generate metadata: No dataset available.")
        
    # Use standard Z for UTC if naive or replace +00:00
    now = datetime.datetime.now(datetime.UTC)
    iso_time = now.isoformat()
    if "+00:00" in iso_time:
        iso_time = iso_time.replace("+00:00", "Z")
    if not iso_time.endswith("Z"):
        iso_time += "Z"
        
    return {
        "workspace": context.workspace_name,
        "build_id": dataset.build_id,
        "candidate_count": len(dataset.candidates),
        "generated_at": iso_time,
        "projection": projection_name
    }
