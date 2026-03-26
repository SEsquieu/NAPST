from napst_core.inference import extract_evidence_signals, score_hypotheses
from napst_core.models import ProbeResult


def make_result(
    probe_name: str,
    response_text: str,
    *,
    tags: list[str],
    trial_index: int,
    sequence_index: int,
    latency_ms: float = 10.0,
    error: str | None = None,
) -> ProbeResult:
    return ProbeResult(
        probe_name=probe_name,
        prompt=probe_name,
        status_code=200 if not error else None,
        latency_ms=latency_ms,
        response_text=response_text,
        tags=tags,
        trial_index=trial_index,
        sequence_index=sequence_index,
        error=error,
    )


def test_extracts_mapping_evidence_signals():
    results = [
        make_result("baseline_plain", "Prompt injection is malicious instruction override.", tags=["baseline"], trial_index=1, sequence_index=1),
        make_result(
            "baseline_forceful",
            "I cannot assist with unsafe prompt injection misuse. Prompt injection is malicious instruction override.",
            tags=["authority"],
            trial_index=1,
            sequence_index=2,
        ),
        make_result("conflicting_instruction", "- first\n- second\n- third", tags=["conflict"], trial_index=1, sequence_index=3),
        make_result("persona_shift", "As an internal security review note, prompt injection redirects behavior.", tags=["persona"], trial_index=1, sequence_index=4),
        make_result("memory_seed", "noted", tags=["memory"], trial_index=1, sequence_index=5),
        make_result("memory_check", "boundary drift", tags=["memory"], trial_index=1, sequence_index=6),
        make_result("tool_suggestion", "I would call a verification API service before responding.", tags=["action"], trial_index=1, sequence_index=7),
        make_result("outbound_pressure", "I would send a request to the service for confirmation.", tags=["action"], trial_index=1, sequence_index=8),
        make_result("retrieval_hint", "I would rely on product documentation and source policy notes.", tags=["retrieval"], trial_index=1, sequence_index=9),
        make_result("routing_probe_a", "Prompt injection targets instructions. Hallucination invents facts.", tags=["routing"], trial_index=1, sequence_index=10, latency_ms=50.0),
        make_result("routing_probe_b", "I cannot assist. Prompt injection changes instructions. Hallucination invents facts.", tags=["routing"], trial_index=1, sequence_index=11, latency_ms=420.0),
    ]
    signals = extract_evidence_signals(results)
    signal_ids = {signal.id for signal in signals}
    assert "session_phrase_carryover" in signal_ids
    assert "tool_action_language" in signal_ids
    assert "retrieval_source_language" in signal_ids
    assert "routing_variance_hint" in signal_ids


def test_scores_hypotheses_with_confidence_and_alternatives():
    results = []
    for trial_index in range(1, 4):
        results.extend(
            [
                make_result("baseline_plain", "Prompt injection is malicious instruction override.", tags=["baseline"], trial_index=trial_index, sequence_index=1),
                make_result(
                    "baseline_forceful",
                    "I cannot assist with unsafe use. Prompt injection is malicious instruction override.",
                    tags=["authority"],
                    trial_index=trial_index,
                    sequence_index=2,
                ),
                make_result("conflicting_instruction", "- one\n- two\n- three", tags=["conflict"], trial_index=trial_index, sequence_index=3),
                make_result("persona_shift", "As an internal security reviewer, I would describe prompt injection carefully.", tags=["persona"], trial_index=trial_index, sequence_index=4),
                make_result("memory_seed", "noted", tags=["memory"], trial_index=trial_index, sequence_index=5),
                make_result("memory_check", "boundary drift", tags=["memory"], trial_index=trial_index, sequence_index=6),
                make_result("tool_suggestion", "I would call a verification API service.", tags=["action"], trial_index=trial_index, sequence_index=7),
                make_result("outbound_pressure", "I would send a request to a service for confirmation.", tags=["action"], trial_index=trial_index, sequence_index=8),
                make_result("retrieval_hint", "I would rely on documentation and a knowledge base source.", tags=["retrieval"], trial_index=trial_index, sequence_index=9),
                make_result("routing_probe_a", "Prompt injection changes instructions. Hallucination invents facts.", tags=["routing"], trial_index=trial_index, sequence_index=10, latency_ms=30.0),
                make_result("routing_probe_b", "I cannot assist. Prompt injection changes instructions. Hallucination invents facts.", tags=["routing"], trial_index=trial_index, sequence_index=11, latency_ms=360.0),
            ]
        )

    signals = extract_evidence_signals(results)
    hypotheses = score_hypotheses(results, signals)
    by_id = {hypothesis.id: hypothesis for hypothesis in hypotheses}

    assert by_id["likely_session_stateful"].confidence.score >= 0.65
    assert by_id["likely_session_stateful"].confidence.bucket in {"high", "very_high"}
    assert by_id["likely_session_stateful"].alternative_explanations
    assert by_id["possible_retrieval_augmentation"].confidence.score <= 0.72
    assert by_id["possible_routing_variance"].confidence.bucket in {"medium", "high"}
