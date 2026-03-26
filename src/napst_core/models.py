from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field


ConfidenceBucket = Literal["very_low", "low", "medium", "high", "very_high"]


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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MappingScenario:
    name: str
    title: str
    description: str
    trials: int
    probes: list[Probe]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "trials": self.trials,
            "metadata": self.metadata,
            "probes": [probe.to_dict() for probe in self.probes],
        }


@dataclass(slots=True)
class ProbeResult:
    probe_name: str
    prompt: str
    status_code: int | None
    latency_ms: float
    response_text: str
    tags: list[str]
    trial_index: int
    sequence_index: int
    expected_signal: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvidenceSignal:
    id: str
    kind: str
    description: str
    score: float
    supporting_probe_names: list[str]
    trial_indexes: list[int]
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ConfidenceAssessment:
    score: float
    bucket: ConfidenceBucket
    rationale: str
    supporting_signal_ids: list[str]
    weakening_signal_ids: list[str]
    validation_advice: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Hypothesis:
    id: str
    title: str
    statement: str
    category: str
    supporting_evidence_ids: list[str]
    counterevidence_ids: list[str]
    alternative_explanations: list[str]
    confidence: ConfidenceAssessment
    recommended_validation: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["confidence"] = self.confidence.to_dict()
        return data


@dataclass(slots=True)
class ScenarioRun:
    run_id: str
    target_name: str
    scenario: str
    created_at: str
    scenario_title: str
    scenario_description: str
    target_config: dict[str, Any]
    scenario_config: dict[str, Any]
    probe_results: list[ProbeResult]
    evidence_signals: list[EvidenceSignal]
    hypotheses: list[Hypothesis]
    findings: list[dict[str, Any]]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "target_name": self.target_name,
            "scenario": self.scenario,
            "created_at": self.created_at,
            "scenario_title": self.scenario_title,
            "scenario_description": self.scenario_description,
            "target_config": self.target_config,
            "scenario_config": self.scenario_config,
            "probe_results": [probe.to_dict() for probe in self.probe_results],
            "evidence_signals": [signal.to_dict() for signal in self.evidence_signals],
            "hypotheses": [hypothesis.to_dict() for hypothesis in self.hypotheses],
            "findings": self.findings,
            "summary": self.summary,
        }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
