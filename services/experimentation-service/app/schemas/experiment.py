"""Schemas for experimentation-service requests and responses."""

from pydantic import ConfigDict

from shared_schemas import (
    ExperimentAssignmentV1Schema,
    ExperimentExposureCreateV1Schema,
    ExperimentExposureV1Schema,
)


class ExperimentAssignmentResponse(ExperimentAssignmentV1Schema):
    """Assignment response returned by experimentation-service."""

    model_config = ConfigDict(extra="forbid")


class ExperimentExposureCreateRequest(ExperimentExposureCreateV1Schema):
    """Exposure create request accepted from feed-service."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class ExperimentExposureResponse(ExperimentExposureV1Schema):
    """Exposure response returned after persistence."""

    model_config = ConfigDict(extra="forbid")
