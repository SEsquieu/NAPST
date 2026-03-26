# NAPST Roadmap

## North Star

Build NAPST into a security-focused suite for testing and mapping LLM and agentic systems, starting with a black-box behavioral mapper that estimates internal structure through a narrow frontend view.

## Near-Term Goal

Deliver a mapping workflow that:

- probes an LLM or agent endpoint
- extracts repeatable behavioral signals
- infers bounded structural hypotheses
- presents each hypothesis with explicit confidence

## Capability Stages

### Stage 1: Mapping MVP

- HTTP JSON target support
- structured mapping probe packs
- repeated-trial runs
- evidence signal extraction
- confidence-scored hypotheses
- HTML and CLI reports

### Stage 2: Analyst Workflow

- run comparison
- drift detection
- exportable findings
- saved target profiles
- scenario pack registry

### Stage 3: Gray-Box Fusion

- ingestion of retrieval events
- tool-call traces
- memory events
- routing metadata
- confidence upgrades when direct evidence exists

### Stage 4: Security Team Suite

- project workspaces
- multi-run case management
- team-friendly reporting
- versioned policy packs
- review-ready exports

## Current Gaps

- evidence extraction still leans on simple lexical heuristics in several places
- same-session versus reset-session controls need to become more explicit
- run-to-run comparison and drift tracking are not implemented yet
- gray-box trace fusion is still future work
- public-repo ergonomics and packaging can still be tightened further

## Recommended Implementation Order

1. Add `EvidenceSignal` and `Hypothesis` concepts to core models.
2. Broaden the mapping scenario library and tune the evidence extractors.
3. Add explicit session control and higher-quality repeatability handling.
4. Add run comparison and drift reporting.
5. Extend the system with gray-box trace ingestion.
