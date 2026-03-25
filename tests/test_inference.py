from napst_core.inference import infer_boundary_summary, infer_findings
from napst_core.models import ProbeResult


def test_infers_session_persistence():
    results = [
        ProbeResult("memory_seed", "seed", 200, 10.0, "noted", ["memory"]),
        ProbeResult("memory_check", "check", 200, 12.0, "boundary drift", ["memory"]),
    ]
    findings = infer_findings(results)
    summary = infer_boundary_summary(results, findings)
    assert any(f["id"] == "session-persistence-hint" for f in findings)
    assert summary["likely_session_stateful"] is True
