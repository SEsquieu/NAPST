from __future__ import annotations

from .http_client import TargetInvoker
from .inference import build_findings, extract_evidence_signals, score_hypotheses, summarize_results
from .models import ScenarioRun, TargetConfig, utc_now_iso
from .reporting import write_html_report
from .scenarios import get_scenario
from .storage import ArtifactStore


class NapstRunner:
    def __init__(self, store: ArtifactStore | None = None, invoker_cls: type[TargetInvoker] = TargetInvoker):
        self.store = store or ArtifactStore()
        self.invoker_cls = invoker_cls

    def run(self, target: TargetConfig, scenario_name: str) -> ScenarioRun:
        scenario = get_scenario(scenario_name)
        results = []
        for trial_index in range(1, scenario.trials + 1):
            invoker = self.invoker_cls(target)
            for sequence_index, probe in enumerate(scenario.probes, start=1):
                results.append(invoker.invoke(probe, trial_index=trial_index, sequence_index=sequence_index))

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
