import json
from pathlib import Path

from napst_core.models import ConfidenceAssessment, Hypothesis
from napst_core.reporting import write_html_report


def test_html_report_renders_hypothesis_details():
    report_path = Path.cwd() / "test-report-output.html"
    run = {
        "run_id": "run_0001",
        "target_name": "demo",
        "scenario": "map_core",
        "scenario_description": "demo mapping run",
        "summary": {"hypothesis_count": 1},
        "hypotheses": [
            Hypothesis(
                id="likely_session_stateful",
                title="Likely session-stateful behavior",
                statement="The target likely retains same-trial context.",
                category="statefulness",
                supporting_evidence_ids=["session_phrase_carryover"],
                counterevidence_ids=["transport_errors_present"],
                alternative_explanations=["Prompt-local carryover may explain the effect."],
                confidence=ConfidenceAssessment(
                    score=0.77,
                    bucket="high",
                    rationale="Repeated carryover signals increased confidence.",
                    supporting_signal_ids=["session_phrase_carryover"],
                    weakening_signal_ids=["transport_errors_present"],
                    validation_advice="Repeat with reset-session controls.",
                ),
                recommended_validation="Repeat with reset-session controls.",
            ).to_dict()
        ],
        "evidence_signals": [
            {
                "id": "session_phrase_carryover",
                "kind": "support",
                "score": 1.0,
                "description": "Seeded phrase reappeared later in the trial.",
                "supporting_probe_names": ["memory_seed", "memory_check"],
                "trial_indexes": [1, 2, 3],
            }
        ],
        "probe_results": [],
    }

    try:
        if report_path.exists():
            report_path.unlink()
        write_html_report(run, report_path)
        contents = report_path.read_text(encoding="utf-8")
        assert "Likely session-stateful behavior" in contents
        assert "score 0.77" in contents
        assert "Alternative explanations" in contents
        assert json.dumps(run["summary"], indent=2) in contents
    finally:
        if report_path.exists():
            report_path.unlink()
