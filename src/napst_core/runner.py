from __future__ import annotations

from .http_client import TargetInvoker
from .inference import infer_boundary_summary, infer_findings, summarize_results
from .models import ScenarioRun, TargetConfig, utc_now_iso
from .reporting import write_html_report
from .scenarios import get_scenario
from .storage import ArtifactStore


class NapstRunner:
    def __init__(self, store: ArtifactStore | None = None):
        self.store = store or ArtifactStore()

    def run(self, target: TargetConfig, scenario_name: str) -> ScenarioRun:
        probes = get_scenario(scenario_name)
        invoker = TargetInvoker(target)
        results = [invoker.invoke(probe) for probe in probes]
        findings = infer_findings(results)
        summary = summarize_results(results)
        summary["boundary_inference"] = infer_boundary_summary(results, findings)
        run = ScenarioRun(
            run_id=self.store.next_run_id(),
            target_name=target.name,
            scenario=scenario_name,
            created_at=utc_now_iso(),
            probe_results=results,
            findings=findings,
            summary=summary,
        )
        run_dir = self.store.save_run(run)
        write_html_report(run.to_dict(), run_dir / "report.html")
        return run
