import datetime
import json
import os
import uuid
from typing import IO, Any

from candidate_transformer.config import OutputConfig, PipelineConfig
from candidate_transformer.connectors import connector_registry
from candidate_transformer.domain.models import Candidate, CanonicalDataset
from candidate_transformer.interfaces.connector import RawRecord
from candidate_transformer.pipeline import (
    ConfidenceScoringStage,
    ConflictResolutionStage,
    EntityResolutionStage,
    ExtractionStage,
    NormalizationStage,
    PipelineEngine,
    ValidationStage,
)
from candidate_transformer.projection.engine import ProjectionEngine
from candidate_transformer.validation.output_validation import OutputValidator

class CandidateTransformer:
    """
    Facade for the Candidate Transformer framework.
    Provides a clean, intuitive API for loading data, building the canonical dataset,
    and projecting the final output.
    """

    def __init__(self, config: PipelineConfig | None = None):
        if config is None:
            # Fallback to sensible defaults (from configs/default.json if possible)
            default_path = os.path.join(os.path.dirname(__file__), "../../../configs/default.json")
            if os.path.exists(default_path):
                with open(default_path) as f:
                    self.config = PipelineConfig(**json.load(f))
            else:
                self.config = PipelineConfig(
                    output=OutputConfig(
                        fields=[],
                        include_confidence=True,
                        include_provenance=True,
                        on_missing="null",
                    ),
                    source_priorities=[],
                )
        else:
            self.config = config

        self.pipeline = PipelineEngine()
        self.projection_engine = ProjectionEngine()
        self.output_validator = OutputValidator()
        self._raw_records: list[RawRecord] = []
        self._dataset: CanonicalDataset | None = None

        # Wire the pipeline stages
        self.pipeline.add_stage(ExtractionStage())
        self.pipeline.add_stage(NormalizationStage())
        self.pipeline.add_stage(EntityResolutionStage())
        self.pipeline.add_stage(ConflictResolutionStage(self.config.source_priorities))
        self.pipeline.add_stage(ConfidenceScoringStage())
        self.pipeline.add_stage(ValidationStage())

    def load(self, connector_name: str, file_stream: IO[str]) -> "CandidateTransformer":
        """
        Loads data using a registered connector.
        Fluent API: Returns self to allow chaining.
        """
        connector_cls = connector_registry.get(connector_name)
        connector = connector_cls(file_stream)  # type: ignore

        for record in connector.fetch():
            self._raw_records.append(record)

        return self

    def build(self) -> CanonicalDataset:
        """
        Executes the transformation pipeline and generates an immutable CanonicalDataset.
        """
        start_time = datetime.datetime.now(datetime.UTC)
        
        candidates: list[Candidate] = []
        if self._raw_records:
            candidates = self.pipeline.execute(self._raw_records)
            
        end_time = datetime.datetime.now(datetime.UTC)
        duration = (end_time - start_time).total_seconds()
        
        # Calculate statistics
        # Note: True duplication / merge counts would require instrumentation in EntityResolutionStage.
        # For now, we simulate with lengths.
        stats = {
            "candidate_count": len(candidates),
            "raw_records": len(self._raw_records),
            "pipeline_duration_seconds": duration,
        }
        if candidates:
            stats["average_confidence"] = sum(c.overall_confidence for c in candidates) / len(candidates)
            stats["average_skills"] = sum(len(c.skills) for c in candidates) / len(candidates)
            stats["average_experience"] = sum(len(c.experience) for c in candidates) / len(candidates)
        
        dataset = CanonicalDataset(
            candidates=candidates,
            build_timestamp=start_time.isoformat(),
            build_id=f"Build-{uuid.uuid4().hex[:8].upper()}",
            statistics=stats,
            build_metadata={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration": duration
            },
            connector_metadata={},
            diagnostics=[]
        )
        self._dataset = dataset
        return dataset
        
    def transform(self) -> list[Candidate]:
        """
        Legacy method for backward compatibility.
        """
        dataset = self.build()
        return dataset.candidates
        
    def _resolve_projection_config(self, projection_name_or_cfg: str | OutputConfig) -> OutputConfig:
        if isinstance(projection_name_or_cfg, OutputConfig):
            return projection_name_or_cfg
            
        path = projection_name_or_cfg
        if not path.endswith(".json"):
            # Try to resolve against configs/projections
            cwd_path = os.path.join(os.getcwd(), "configs", "projections", f"{projection_name_or_cfg}.json")
            if os.path.exists(cwd_path):
                path = cwd_path
            else:
                path = f"{projection_name_or_cfg}.json"
                
        with open(path) as f:
            cfg_dict = json.load(f)
            # Support both unwrapped and wrapped ("output": {...}) configs
            if "output" in cfg_dict:
                cfg_dict = cfg_dict["output"]
            return OutputConfig(**cfg_dict)

    def project(self, projection: str | OutputConfig) -> list[dict[str, Any]]:
        """
        Projects the canonical candidates into the final output schema.
        Accepts a projection name (e.g. 'analytics'), a file path, or an OutputConfig.
        """
        if self._dataset is None:
            self.build()
            
        cfg = self._resolve_projection_config(projection)

        results = []
        for candidate in self._dataset.candidates: # type: ignore
            projected = self.projection_engine.project(candidate, cfg)
            self.output_validator.validate(projected, cfg)
            results.append(projected)

        return results

    def export(self, projection: str | OutputConfig, filepath: str) -> None:
        """
        Projects the canonical candidates and writes the result to a JSON file.
        """
        results = self.project(projection)
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)
