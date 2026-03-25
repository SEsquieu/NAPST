from __future__ import annotations

from typing import Any

import httpx

from .models import Probe, ProbeResult, TargetConfig


class TargetInvoker:
    def __init__(self, target: TargetConfig):
        self.target = target

    def _render(self, value: Any, prompt: str) -> Any:
        if isinstance(value, str):
            return value.replace("{prompt}", prompt)
        if isinstance(value, list):
            return [self._render(v, prompt) for v in value]
        if isinstance(value, dict):
            return {k: self._render(v, prompt) for k, v in value.items()}
        return value

    def _extract(self, payload: Any) -> str:
        path = self.target.response_json_path
        if path and isinstance(payload, dict):
            current: Any = payload
            for part in path.split("."):
                if isinstance(current, list):
                    current = current[int(part)]
                else:
                    current = current.get(part)
                if current is None:
                    return ""
            return str(current)
        if isinstance(payload, str):
            return payload
        if isinstance(payload, dict):
            for key in ("response", "text", "content", "message"):
                if key in payload:
                    return str(payload[key])
        return str(payload)

    def invoke(self, probe: Probe) -> ProbeResult:
        url = f"{self.target.base_url.rstrip('/')}" + f"/{self.target.endpoint.lstrip('/')}"
        body = self._render(self.target.body_template, probe.prompt)
        with httpx.Client(timeout=self.target.timeout) as client:
            try:
                response = client.request(
                    self.target.method,
                    url,
                    headers=self.target.headers,
                    json=body if self.target.method == "POST" else None,
                    params=body if self.target.method == "GET" else None,
                )
                response.raise_for_status()
                try:
                    payload = response.json()
                except Exception:
                    payload = response.text
                text = self._extract(payload)
                latency_ms = response.elapsed.total_seconds() * 1000
                return ProbeResult(
                    probe_name=probe.name,
                    prompt=probe.prompt,
                    status_code=response.status_code,
                    latency_ms=round(latency_ms, 2),
                    response_text=text,
                    tags=probe.tags,
                    expected_signal=probe.expected_signal,
                    metadata=probe.metadata,
                )
            except Exception as exc:
                return ProbeResult(
                    probe_name=probe.name,
                    prompt=probe.prompt,
                    status_code=None,
                    latency_ms=0.0,
                    response_text="",
                    tags=probe.tags,
                    expected_signal=probe.expected_signal,
                    metadata=probe.metadata,
                    error=str(exc),
                )
