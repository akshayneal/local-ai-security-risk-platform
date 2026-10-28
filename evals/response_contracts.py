"""Historical schema-check contract for the frozen V1/V2 suites.

The analyzer enforces today's production schema before evaluation sees output.
Frozen schema_valid checks retain their original optional SOC observations;
otherwise replaying the old artifacts would silently change their scores.
"""

from pydantic import Field

from app.schemas import SocAlertResponse


class BenchmarkSocAlertResponse(SocAlertResponse):
    observed_evidence: list[str] = Field(default_factory=list)
