from __future__ import annotations

from .inference import build_findings, extract_evidence_signals, score_hypotheses, summarize_results
from .models import ScenarioRun, TargetConfig, utc_now_iso
from .reporting import write_html_report
from .scenarios import get_scenario
from .storage import ArtifactStore
from .transports import TargetTransport, build_transport


class NapstRunner:
    def __init__(
        self,
        store: ArtifactStore | None = None,
        transport_factory: callable | None = None,
    ):
        self.store = store or ArtifactStore()
        self.transport_factory = transport_factory or build_transport

    def run(self, target: TargetConfig, scenario_name: str) -> ScenarioRun:
        scenario = get_scenario(scenario_name)
        results = []
        transport: TargetTransport = self.transport_factory(target)
        try:
            for trial_index in range(1, scenario.trials + 1):
                transport.start_trial(trial_index)
                for sequence_index, probe in enumerate(scenario.probes, start=1):
                    results.append(transport.invoke(probe, trial_index=trial_index, sequence_index=sequence_index))
                transport.end_trial(trial_index)
        finally:
            transport.close()

        evidence_signals = extract_evidence_signals(results)
        hypotheses = score_hypotheses(results, evidence_signals)
        findings = build_findings(hypotheses)
        summary = summarize_results(results, evidence_signals, hypotheses)
        run = ScenarioRun(
            run_id=self.store.next_run_id(),
            target_name=target.name,
            scenario=scenario.name,
            created_at=utc_now_iso(),
            scenario_title=scenario.title,
            scenario_description=scenario.description,
            target_config=target.model_dump(),
            scenario_config=scenario.to_dict(),
            probe_results=results,
            evidence_signals=evidence_signals,
            hypotheses=hypotheses,
            findings=findings,
            summary=summary,
        )
        run_dir = self.store.save_run(run)
        write_html_report(run.to_dict(), run_dir / "report.html")
        return run
