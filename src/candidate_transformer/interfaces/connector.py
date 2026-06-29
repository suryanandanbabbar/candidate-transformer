from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from pydantic import BaseModel


class RawRecord(BaseModel):
    """
    A unified wrapper around whatever data a connector extracts.
    This gives the extraction stage a standard way to hand data to the normalizers.
    """

    source_name: str
    source_type: str
    timestamp: str
    raw_data: dict[str, Any]


class BaseConnector(ABC):
    """
    The fundamental contract for all data source connectors.
    Connectors are responsible for authenticating, fetching, and yielding
    raw records from a source without deeply interpreting the domain models.
    """

    @abstractmethod
    def fetch(self) -> Iterator[RawRecord]:
        """
        Fetch data from the source and yield RawRecord objects.
        This must be an iterator to support streaming large datasets.
        """
        pass
