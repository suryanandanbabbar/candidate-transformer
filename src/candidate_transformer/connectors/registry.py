from candidate_transformer.interfaces.connector import BaseConnector
from candidate_transformer.utils.registry import Registry

# Global registry for connectors
connector_registry = Registry[BaseConnector]("connectors")
