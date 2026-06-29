import json
import os
from typing import IO, Any

from candidate_transformer.config import OutputConfig, PipelineConfig
from candidate_transformer.connectors import connector_registry
from candidate_transformer.domain.models import Candidate
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
    Provides a clean, intuitive API for loading data, running the pipeline,
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
        self._candidates: list[Candidate] = []

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
        # mypy type ignore as registry guarantees BaseConnector
        connector = connector_cls(file_stream)  # type: ignore

        for record in connector.fetch():
            self._raw_records.append(record)

        return self

    def transform(self) -> list[Candidate]:
        """
        Executes the transformation pipeline on loaded records.
        """
        if not self._raw_records:
            return []

        self._candidates = self.pipeline.execute(self._raw_records)
        return self._candidates

    def export(self, override_config: OutputConfig | None = None) -> list[dict[str, Any]]:
        """
        Projects the canonical candidates into the final output schema.
        Returns a list of dictionaries representing the projected candidates.
        """
        if not hasattr(self, "_candidates") or not self._candidates:
            self.transform()

        cfg = override_config or self.config.output

        results = []
        for candidate in self._candidates:
            projected = self.projection_engine.project(candidate, cfg)
            self.output_validator.validate(projected, cfg)
            results.append(projected)

        return results
