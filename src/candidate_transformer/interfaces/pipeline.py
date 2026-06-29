from abc import ABC, abstractmethod
from typing import Any


class PipelineStage(ABC):
    """
    Contract for a discrete step in the pipeline.
    Each stage takes an input and produces an output, moving the data
    closer to the final canonical form.
    """

    @abstractmethod
    def execute(self, input_data: Any) -> Any:
        """
        Execute this stage's business logic on the input data.
        """
        pass
