import csv
from collections.abc import Iterator
from datetime import datetime
from typing import IO

from candidate_transformer.connectors.registry import connector_registry
from candidate_transformer.exceptions import ConnectorError
from candidate_transformer.interfaces.connector import BaseConnector, RawRecord


@connector_registry("recruiter_csv")
class RecruiterCSVConnector(BaseConnector):
    """
    Connects to a recruiter-provided CSV file.
    Assumes a header row exists.
    """

    def __init__(self, file_stream: IO[str], source_name: str = "recruiter_csv"):
        self.file_stream = file_stream
        self.source_name = source_name

    def fetch(self) -> Iterator[RawRecord]:
        try:
            reader = csv.DictReader(self.file_stream)
            for row in reader:
                # Remove None or empty values to keep raw data clean
                clean_row = {k: v for k, v in row.items() if k and v}

                yield RawRecord(
                    source_name=self.source_name,
                    source_type="csv",
                    timestamp=datetime.utcnow().isoformat(),
                    raw_data=clean_row,
                )
        except Exception as e:
            raise ConnectorError(f"Failed to read CSV from {self.source_name}: {e}") from e
