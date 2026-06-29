from typing import Any

from candidate_transformer.interfaces.pipeline import PipelineStage


class PipelineEngine:
    """
    Executes a sequence of PipelineStage instances in order.
    """

    def __init__(self, stages: list[PipelineStage] | None = None):
        self.stages = stages or []

    def add_stage(self, stage: PipelineStage) -> None:
        self.stages.append(stage)

    def execute(self, input_data: Any) -> Any:
        current_data = input_data
        for stage in self.stages:
            current_data = stage.execute(current_data)
        return current_data
