"""Schemas for analytics-service experiment comparison responses."""

from pydantic import ConfigDict

from shared_schemas import ExperimentComparisonV1Schema


class ExperimentComparisonResponse(ExperimentComparisonV1Schema):
    """Experiment comparison response returned by analytics-service."""

    model_config = ConfigDict(extra="forbid")
