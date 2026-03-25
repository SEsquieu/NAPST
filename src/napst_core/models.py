from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field


class TargetConfig(BaseModel):
    name: str
    base_url: str
    endpoint: str
    method: Literal["GET", "POST"] = "POST"
    headers: dict[str, str] = Field(default_factory=dict)
    body_template: dict[str, Any] = Field(default_factory=lambda: {"prompt": "{prompt}"})
    timeout: float = 20.0
    response_json_path: str | None = None
    notes: str | None = None

    @classmethod
    def from_yaml(cls, path: str | Path) -> "TargetConfig":
        data = yaml.safe_load(Path(path).read_text())
        return cls.model_validate(data)


@dataclass(slots=True)
class Probe:
    name: str
    prompt: str
    tags: list[str] = field(default_factory=list)
    expected_signal: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProbeResult:
    probe_name: str
    prompt: str
    status_code: int | None
    latency_ms: float
    response_text: str
    tags: list[str]
    expected_signal: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ScenarioRun:
    run_id: str
    target_name: str
    scenario: str
    created_at: str
    probe_results: list[ProbeResult]
    findings: list[dict[str, Any]]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "target_name": self.target_name,
            "scenario": self.scenario,
            "created_at": self.created_at,
            "probe_results": [p.to_dict() for p in self.probe_results],
            "findings": self.findings,
            "summary": self.summary,
        }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
