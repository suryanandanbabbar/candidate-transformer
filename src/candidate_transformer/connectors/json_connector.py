import json
from collections.abc import Iterator
from datetime import datetime
from typing import IO

from candidate_transformer.connectors.registry import connector_registry
from candidate_transformer.exceptions import ConnectorError
from candidate_transformer.interfaces.connector import BaseConnector, RawRecord


@connector_registry("ats_json")
class ATSJSONConnector(BaseConnector):
    """
    Connects to an ATS JSON export (e.g., list of candidate objects).
    """

    def __init__(self, file_stream: IO[str], source_name: str = "ats_json"):
        self.file_stream = file_stream
        self.source_name = source_name

    def fetch(self) -> Iterator[RawRecord]:
        try:
            data = json.load(self.file_stream)
            if not isinstance(data, list):
                # If a single object, wrap it in a list
                data = [data]

            for item in data:
                yield RawRecord(
                    source_name=self.source_name,
                    source_type="json",
                    timestamp=datetime.utcnow().isoformat(),
                    raw_data=item,
                )
        except json.JSONDecodeError as e:
            raise ConnectorError(f"Invalid JSON in {self.source_name}: {e}") from e
        except Exception as e:
            raise ConnectorError(f"Failed to read JSON from {self.source_name}: {e}") from e
