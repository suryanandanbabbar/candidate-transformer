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
        engine = CandidateTransformer(context.runtime_config)
        engine._dataset = context.dataset
        
        # Candidates (Canonical dataset exactly as stored)
        candidates_dict = context.dataset.model_dump(mode="json")
        
        # Metadata
        metadata_data = generate_metadata(context, "canonical")
        
        # Base db.json
        db_json = {
            "canonical": candidates_dict,
            "metadata": metadata_data
        }
        
        # Discover and run all projections
        proj_dir = os.path.join(os.getcwd(), "configs", "projections")
        if os.path.exists(proj_dir):
            for f_name in os.listdir(proj_dir):
                if f_name.endswith(".json"):
                    proj_name = f_name[:-5]  # remove .json
                    try:
                        proj_data = engine.project(proj_name)
                        db_json[proj_name] = proj_data
                        
                        # Export individual projection files
                        with open(os.path.join(export_dir, f_name), "w") as f:
                            json.dump(proj_data, f, indent=2)
                    except Exception as e:
                        # Log or ignore invalid projections
                        pass
                        
        # Ensure candidates is an exact alias for canonical
        db_json["candidates"] = db_json.get("canonical", candidates_dict)
                        
        # Export base files
        with open(os.path.join(export_dir, "canonical.json"), "w") as f:
            json.dump(db_json["canonical"], f, indent=2)
        with open(os.path.join(export_dir, "candidates.json"), "w") as f:
            json.dump(db_json["candidates"], f, indent=2)
        with open(os.path.join(export_dir, "metadata.json"), "w") as f:
            json.dump(metadata_data, f, indent=2)
            
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        with open(RUNTIME_DIR / "db.json", "w") as f:
            json.dump(db_json, f, indent=2)
            
    except Exception as e:
        raise RuntimeError(f"Export failed: {e}") from e
