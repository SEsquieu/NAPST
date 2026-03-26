from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

import yaml
from pydantic import BaseModel, Field, model_validator


ConfidenceBucket = Literal["very_low", "low", "medium", "high", "very_high"]


class TargetConfig(BaseModel):
    name: str
    type: Literal["http_json", "browser_chat"] = "http_json"
    base_url: str | None = None
    endpoint: str | None = None
    method: Literal["GET", "POST"] = "POST"
    headers: dict[str, str] = Field(default_factory=dict)
    body_template: dict[str, Any] = Field(default_factory=lambda: {"prompt": "{prompt}"})
    timeout: float = 20.0
    response_json_path: str | None = None
    start_url: str | None = None
    origin_allowlist: list[str] = Field(default_factory=list)
    storage_state_path: str | None = None
    prompt_input_selector: str | None = None
    send_button_selector: str | None = None
    submit_on_enter: bool = True
    response_container_selector: str | None = None
    ready_selector: str | None = None
    typing_indicator_selector: str | None = None
    wait_timeout_seconds: float = 20.0
    inter_probe_delay_seconds: float = 0.75
    notes: str | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> "TargetConfig":
        if self.type == "http_json":
            if not self.base_url or not self.endpoint:
                raise ValueError("http_json targets require base_url and endpoint")
            return self

        required_browser_fields = {
            "start_url": self.start_url,
            "storage_state_path": self.storage_state_path,
            "prompt_input_selector": self.prompt_input_selector,
            "response_container_selector": self.response_container_selector,
        }
        missing = sorted(name for name, value in required_browser_fields.items() if not value)
        if missing:
            raise ValueError(
                "browser_chat targets require " + ", ".join(missing)
            )
        if not self.submit_on_enter and not self.send_button_selector:
            raise ValueError("browser_chat targets require send_button_selector when submit_on_enter is false")
        if self.origin_allowlist:
            return self
        parsed = urlparse(self.start_url or "")
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("browser_chat targets require a valid start_url")
        self.origin_allowlist = [f"{parsed.scheme}://{parsed.netloc}"]
        return self

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
