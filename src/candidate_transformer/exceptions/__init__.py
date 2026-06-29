"""
Clean exception hierarchy for the Candidate Transformer framework.

All exceptions raised by the framework should inherit from the base
CandidateTransformerError. This allows developers using the framework
to catch a single base exception if they wish to handle all framework-related
errors generically.
"""


class CandidateTransformerError(Exception):
    """Base exception for all Candidate Transformer errors."""

    pass


class ConfigurationError(CandidateTransformerError):
    """
    Raised when there is an issue with the configuration.
    Examples include invalid YAML/JSON, missing required keys,
    or logically inconsistent projection configurations.
    """

    pass


class ConnectorError(CandidateTransformerError):
    """
    Raised when a connector fails to read from its source.
    Typically caught by the extraction stage to allow graceful degradation
    if other sources are available.
    """

    pass


class NormalizationError(CandidateTransformerError):
    """
    Raised when a normalizer encounters an unrecoverable error
    while attempting to normalize a specific value (e.g., malformed date string).
    """

    pass


class ValidationError(CandidateTransformerError):
    """
    Raised when the canonical record or an intermediate record
    fails schema validation.
    """

    pass


class ProjectionError(CandidateTransformerError):
    """
    Raised when the projection engine encounters an issue mapping
    canonical paths to the output schema.
    """

    pass
