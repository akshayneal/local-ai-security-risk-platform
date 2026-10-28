"""Validate bundled synthetic demos before populating any form."""

import csv
import json
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from app.schemas import GovernanceRiskRequest, SocAlertRequest

ROOT = Path(__file__).resolve().parents[1]
Sample = SocAlertRequest | GovernanceRiskRequest


class SampleLoadError(ValueError):
    pass


def load_soc_samples(
    path: Path = ROOT / "sample_data/soc_alerts.csv",
) -> list[SocAlertRequest]:
    try:
        with path.open(encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
        samples = []
        for row in rows:
            row["known_indicators"] = json.loads(row["known_indicators"])
            samples.append(SocAlertRequest.model_validate(row))
        if not samples:
            raise ValueError("empty samples")
        return samples
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        csv.Error,
        ValidationError,
    ) as exc:
        raise SampleLoadError(
            "Synthetic SOC samples are unavailable or invalid."
        ) from exc


def load_governance_samples(
    path: Path = ROOT / "sample_data/ai_use_cases.json",
) -> list[GovernanceRiskRequest]:
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(rows, list) or not rows:
            raise ValueError("expected nonempty list")
        return [GovernanceRiskRequest.model_validate(row) for row in rows]
    except (OSError, ValueError, TypeError, ValidationError) as exc:
        raise SampleLoadError(
            "Synthetic governance samples are unavailable or invalid."
        ) from exc


def sample_labels(samples: Sequence[Sample]) -> list[str]:
    return [
        s.alert_id if isinstance(s, SocAlertRequest) else s.system_name for s in samples
    ]


def select_sample(samples: Sequence[Sample], label: str) -> Sample:
    try:
        return samples[sample_labels(samples).index(label)].model_copy(deep=True)
    except ValueError as exc:
        raise SampleLoadError("Select an available synthetic sample.") from exc


def form_values(sample: SocAlertRequest | GovernanceRiskRequest) -> dict[str, str]:
    return {
        key: "\n".join(value) if isinstance(value, list) else value
        for key, value in sample.model_dump().items()
    }
