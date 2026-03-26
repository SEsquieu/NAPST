# NAPST Architecture

## Mission

NAPST is a security evaluation suite for mapping and stress-testing LLM and agentic systems through limited external visibility.

Its first major product goal is a robust mapping tool that looks through a pinhole view:

- interact with an LLM or agent frontend
- observe behavioral signals over repeated probes
- estimate likely internal structure and operating boundaries
- report findings with explicit confidence, not false certainty

NAPST should help security teams answer questions such as:

- Does this target appear stateful across turns?
- Is there evidence of retrieval, tool use, routing, or policy layering?
- How sensitive is behavior to authority, formatting, persona, and sequence effects?
- Which conclusions are well-supported, and which are weak hints that need validation?

## Product Principles

### 1. Never pretend to see what is not visible

NAPST does not claim to know architecture from black-box interaction alone. It produces:

- observations
- hypotheses
- confidence scores
- recommended follow-up validation

### 2. Evidence before narrative

Every inferred claim should be backed by:

- one or more concrete probe results
- a scoring explanation
- a list of competing interpretations when relevant

### 3. Separate collection from judgment

The system should clearly separate:

- probe execution
- normalization
- evidence extraction
- inference
- reporting

This keeps the engine extensible and makes confidence easier to reason about.

### 4. Support escalating visibility

Black-box probing is the starting point, not the end state. The architecture must support:

- black-box mode
- gray-box adapters for traces and telemetry
- higher-confidence causal mapping when internal signals are available

### 5. Optimize for security workflows

Outputs should be useful to security teams, not just researchers. Findings should be:

- reproducible
- reviewable
- exportable
- suitable for triage and follow-up investigation

## Suite Shape

NAPST should evolve into a suite with multiple products sharing a common evidence model.

### Planned product areas

- `map`: behavioral structure mapping through limited external interaction
- `probe`: scenario-based boundary and policy evaluation
- `trace`: gray-box adapters for tool, memory, retrieval, and routing telemetry
- `report`: analyst-facing reporting, comparison, and export
- `registry`: scenario packs, target definitions, and reusable heuristics

The current codebase uses this split today:

1. `napst_core`
   - domain models
   - probe execution
   - storage
   - inference
   - reporting primitives

2. `napst_cli`
   - operator workflows
   - automation and CI entrypoints

3. `napst_ui`
   - local analyst views over saved artifacts

Over time, the suite can keep these boundaries while expanding capability.

## System Architecture

The target architecture for the mapping engine is:

1. Target adapters
2. Probe orchestration
3. Evidence extraction
4. Hypothesis inference
5. Confidence scoring
6. Artifact storage
7. Analyst reporting

### 1. Target adapters

Responsibility:

- define how to talk to a target
- render requests
- normalize responses
- capture transport metadata

Initial support:

- HTTP JSON model frontends

Later support:

- chat-completions style APIs
- streaming responses
- websocket or event transports
- authenticated enterprise endpoints

Important rule:

Adapters should not contain mapping logic. They only collect clean interaction data.

### 2. Probe orchestration

Responsibility:

- execute ordered probe sequences
- manage run state
- support repeated trials and controlled variation
- preserve timing and sequence information

Probe families for mapping should include:

- baseline stability probes
- authority sensitivity probes
- context conflict probes
- memory persistence probes
- retrieval hint probes
- tool/action posture probes
- routing variation probes
- guardrail consistency probes

The orchestrator should eventually support:

- deterministic repeat counts
- randomized probe order when safe
- paired A/B probe variants
- session-reset versus same-session trials

### 3. Evidence extraction

Responsibility:

- convert raw responses into structured signals
- extract measurable indicators before inference

Examples of evidence signals:

- refusal strength
- formatting compliance
- semantic drift
- persona adoption
- latency deltas
- token-length deltas
- state carryover
- tool-language indicators
- retrieval-language indicators
- routing inconsistency markers

This layer is critical because it lets us move away from brittle, hand-written finding logic and toward reusable evidence primitives.

### 4. Hypothesis inference

Responsibility:

- turn evidence bundles into bounded hypotheses about system structure

Examples of hypotheses:

- likely session-stateful
- likely layered instruction handling
- likely tool-aware or tool-mediated
- possible retrieval augmentation
- likely soft conflict resolution
- likely role-claim sensitivity
- possible model or policy routing variance

Important rule:

A hypothesis is not an architectural fact. It is a structured estimate with known evidence and uncertainty.

### 5. Confidence scoring

Responsibility:

- estimate how strongly the evidence supports each hypothesis
- communicate uncertainty in a way analysts can act on

Confidence should be first-class in the data model, not just presentation.

Recommended shape:

- `score`: numeric value from `0.0` to `1.0`
- `bucket`: human-facing confidence label
- `rationale`: short explanation of why the score landed there
- `supporting_signals`: signals that increased confidence
- `weakening_signals`: signals that reduced confidence
- `validation_advice`: next step to raise confidence

#### Suggested buckets

- `very_low`: 0.00-0.19
- `low`: 0.20-0.39
- `medium`: 0.40-0.64
- `high`: 0.65-0.84
- `very_high`: 0.85-1.00

Five buckets are a better fit than three for this product because they let NAPST distinguish:

- faint hints
- meaningful but incomplete support
- strong repeatable signals

If the UI needs simpler presentation, it can collapse these into low / medium / high without losing internal resolution.

#### Confidence inputs

Confidence should be influenced by:

- repeatability across trials
- signal strength
- cross-probe consistency
- specificity of evidence
- presence of plausible alternative explanations
- quality of the transport data
- whether the claim is black-box only or trace-supported

#### Confidence examples

A claim like "likely session-stateful" may score high when:

- a seeded token reliably reappears in later same-session probes
- reset-session runs do not reproduce the effect
- the behavior survives wording variation

The same claim should score low when:

- it appears once
- it depends on a single fragile phrase match
- there are plausible prompt-local explanations

### 6. Artifact storage

Responsibility:

- persist complete run artifacts
- allow replay, comparison, and auditability

Artifacts should eventually include:

- target config snapshot
- probe definitions used
- raw request and response envelopes
- extracted evidence signals
- inferred hypotheses
- confidence scoring details
- report outputs
- optional trace attachments

Storage should be durable enough for analysts to compare runs across time and target versions.

### 7. Analyst reporting

Responsibility:

- present findings clearly without overstating certainty
- help users move from observation to follow-up action

Reports should answer:

- what we observed
- what we think it may mean
- how confident we are
- what else could explain it
- what to test next

## Recommended Data Model Direction

The current `finding` shape is a good start, but the mapping engine will benefit from splitting concerns more explicitly.

Recommended conceptual objects:

- `Probe`
- `ProbeResult`
- `EvidenceSignal`
- `Hypothesis`
- `ConfidenceAssessment`
- `Run`
- `Report`

### EvidenceSignal

An evidence signal is a small, testable fact extracted from one or more probe results.

Examples:

- `response_length_delta`
- `refusal_strength_change`
- `reused_seed_phrase`
- `tool_action_language_detected`
- `latency_cluster_shift`

### Hypothesis

A hypothesis is a bounded statement about likely structure or behavior.

Example fields:

- `id`
- `title`
- `statement`
- `category`
- `supporting_evidence_ids`
- `counterevidence_ids`
- `alternative_explanations`
- `confidence`
- `recommended_validation`

This split keeps the system honest. Analysts can inspect the raw evidence without accepting the inference.

## Modes of Visibility

NAPST should support three visibility modes with different confidence ceilings.

### Black-box

Inputs:

- prompts
- responses
- timing
- transport metadata

Best for:

- external testing
- vendor evaluation
- red-team style estimation

Limits:

- cannot directly prove internal causality
- confidence ceiling should remain lower for many claims

### Gray-box

Inputs:

- black-box evidence
- retrieval traces
- tool-call records
- memory access events
- routing metadata

Best for:

- internal security reviews
- pre-deployment evaluation
- root-cause investigation

### White-box assisted

Inputs:

- system configuration
- policies
- orchestration code
- model routing rules

Best for:

- engineering collaboration
- remediation validation

The suite should preserve the same hypothesis model across modes, but allow confidence to rise when stronger evidence exists.

## Roadmap

### Phase 1: Strong black-box mapper

Goal:

- make `map` credible and repeatable through frontend-only interaction

Deliverables:

- richer probe families
- repeated-trial execution
- evidence signal extraction layer
- confidence scoring model
- improved mapping report

### Phase 2: Comparison and drift tracking

Goal:

- let teams compare targets, versions, and time-separated runs

Deliverables:

- run diffing
- confidence change tracking
- behavior drift summaries
- regression-focused scenario packs

### Phase 3: Gray-box adapters

Goal:

- raise confidence and reduce ambiguity when telemetry is available

Deliverables:

- trace ingestion interfaces
- evidence fusion across black-box and trace data
- causal validation views

### Phase 4: Full suite maturity

Goal:

- make NAPST a practical analyst suite for security teams

Deliverables:

- project workspace concepts
- team-oriented reporting
- exports for tickets and security reviews
- reusable policy packs and target registries

## Immediate Build Priorities

Given the current repository state, the cleanest next steps are:

1. Expand the mapping scenario library beyond the initial `map_core` pack.
2. Improve evidence extraction to rely less on simple lexical markers.
3. Add stronger session-control mechanics for same-session versus reset-session trials.
4. Add run-to-run comparison and drift tracking.
5. Introduce gray-box trace adapters that can raise confidence for selected hypotheses.
6. Harden public-repo ergonomics, packaging, and analyst-facing docs as the tool matures.

## Definition of Done for the Mapping MVP

The first mapping milestone should be considered successful when NAPST can:

- run multi-probe mapping scenarios against an HTTP frontend
- repeat probes enough to judge consistency
- extract reusable behavioral signals
- generate bounded structural hypotheses
- assign confidence scores with transparent rationale
- show analysts both evidence and uncertainty
- avoid overstating architectural certainty

That is the right foundation for a real security suite.
