import shutil
from pathlib import Path

from napst_core.models import ProbeResult, TargetConfig
from napst_core.runner import NapstRunner
from napst_core.storage import ArtifactStore


class FakeInvoker:
    def __init__(self, target: TargetConfig):
        self.target = target

    def invoke(self, probe, trial_index: int, sequence_index: int) -> ProbeResult:
        response_text = f"{probe.name} response"
        if probe.name == "memory_seed":
            response_text = "noted"
        elif probe.name == "memory_check":
            response_text = "boundary drift"
        elif probe.name == "tool_suggestion":
            response_text = "I would call a verification API service."
        elif probe.name == "outbound_pressure":
            response_text = "I would send a request to a service for confirmation."
        elif probe.name == "retrieval_hint":
            response_text = "I would rely on documentation and a knowledge base source."
        elif probe.name == "conflicting_instruction":
            response_text = "- one\n- two\n- three"
        elif probe.name == "persona_shift":
            response_text = "As an internal security reviewer, I would explain this carefully."
        elif probe.name == "baseline_forceful":
            response_text = "I cannot assist with misuse. Prompt injection is malicious instruction override."
        elif probe.name == "routing_probe_b":
            response_text = "I cannot assist. Prompt injection changes instructions. Hallucination invents facts."
        return ProbeResult(
            probe_name=probe.name,
            prompt=probe.prompt,
            status_code=200,
            latency_ms=320.0 if probe.name == "routing_probe_b" else 25.0,
            response_text=response_text,
            tags=probe.tags,
            trial_index=trial_index,
            sequence_index=sequence_index,
            expected_signal=probe.expected_signal,
            metadata=probe.metadata,
        )


def test_runner_produces_mapping_artifacts():
    temp_dir = Path.cwd() / ".napst-test-runner"
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        store = ArtifactStore(temp_dir / ".napst")
        runner = NapstRunner(store=store, invoker_cls=FakeInvoker)
        target = TargetConfig(name="demo", base_url="http://localhost:8000", endpoint="/chat")

        run = runner.run(target, "map_core")

        assert run.scenario == "map_core"
        assert run.scenario_config["trials"] == 3
        assert len(run.probe_results) == 33
        assert run.evidence_signals
        assert run.hypotheses
        assert (temp_dir / ".napst" / "runs" / run.run_id / "report.html").exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
