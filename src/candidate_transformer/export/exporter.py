import json
import os

from candidate_transformer.api.transformer import CandidateTransformer
from candidate_transformer.cli.context import PipelineContext
from candidate_transformer.export.metadata import generate_metadata
from candidate_transformer.export.json_server import RUNTIME_DIR

def export_all(context: PipelineContext, export_dir: str = "exports") -> None:
    """
    Exports candidates.json, analytics.json, and metadata.json to the target directory.
    Also synthesizes db.json for json-server.
    """
    if not context.dataset:
        raise ValueError("Workspace not built.")
        
    try:
        os.makedirs(export_dir, exist_ok=True)
    except Exception as e:
        raise RuntimeError(f"Failed to create export directory: {e}") from e
    
    try:
        # Generate Analytics
        engine = CandidateTransformer(context.runtime_config)
        engine._dataset = context.dataset
        analytics_data = engine.project("analytics")
        
        # Generate Metadata
        metadata_data = generate_metadata(context, "analytics")
        
        # Generate Candidates (Canonical dataset exactly as stored)
        candidates_dict = context.dataset.model_dump(mode="json")
        
        # Combine into db.json for json-server
        db_json = {
            "candidates": candidates_dict,
            "analytics": analytics_data,
            "metadata": metadata_data
        }
        
        with open(os.path.join(export_dir, "candidates.json"), "w") as f:
            json.dump(candidates_dict, f, indent=2)
            
        with open(os.path.join(export_dir, "analytics.json"), "w") as f:
            json.dump(analytics_data, f, indent=2)
            
        with open(os.path.join(export_dir, "metadata.json"), "w") as f:
            json.dump(metadata_data, f, indent=2)
            
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        with open(RUNTIME_DIR / "db.json", "w") as f:
            json.dump(db_json, f, indent=2)
            
    except Exception as e:
        raise RuntimeError(f"Export failed: {e}") from e
