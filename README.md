# NAPST

NAPST is a black-box mapping tool for LLM and agentic systems.

It interacts with a frontend, applies structured probe sequences, and reports bounded hypotheses about likely system behavior with explicit confidence. It is built for security-minded users who want a careful estimate, not a made-up architecture diagram.

## What NAPST Does

- Sends repeatable probe scenarios to an HTTP JSON model or agent frontend
- Extracts evidence signals from the responses
- Scores bounded hypotheses such as likely session state, soft instruction layering, tool-aware posture, retrieval hints, or possible routing variance
- Writes local run artifacts and an HTML report for review

## What NAPST Does Not Do

- It does not claim to prove internal architecture from black-box access alone
- It is not an offensive automation kit
- It is not a jailbreak toy
- It is not a replacement for internal traces or direct system instrumentation

## Current Scope

The current milestone is a single-run black-box mapper.

- Target type: HTTP JSON frontends
- Primary scenario: `map_core`
- Primary outputs: CLI summary, JSON artifacts, HTML report
- Confidence model: numeric score plus `very_low` / `low` / `medium` / `high` / `very_high`

## Installation

```bash
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install NAPST:

```bash
pip install -e .
```

Install dev dependencies if you want to run tests:

```bash
pip install -e .[dev]
```

## Quickstart

1. Point NAPST at a frontend that accepts HTTP JSON requests.
2. Update [`examples/simple_target.yaml`](examples/simple_target.yaml) for your target.
3. List available scenarios:

```bash
napst scenarios
```

4. Run the main mapping scenario:

```bash
napst run examples/simple_target.yaml --scenario map_core
```

5. Review the generated artifacts in `.napst/runs/<run_id>/`.

Open the HTML report:

```bash
# macOS
open .napst/runs/run_0001/report.html

# Linux
xdg-open .napst/runs/run_0001/report.html

# Windows PowerShell
Invoke-Item .napst/runs/run_0001/report.html
```

## Example Target Config

```yaml
name: local-model
base_url: http://127.0.0.1:8000
endpoint: /chat
method: POST
headers:
  Content-Type: application/json
body_template:
  prompt: "{prompt}"
response_json_path: response
timeout: 20
notes: Point this at a local dev wrapper or staging frontend.
```

`{prompt}` is substituted into the request body before the request is sent. `response_json_path` is optional and can point into nested JSON such as `choices.0.message.content`.

## CLI

```bash
napst scenarios
napst run examples/simple_target.yaml --scenario map_core
napst list-runs
napst show run_0001
napst serve
```

## How To Read The Output

Each run produces:

- `run.json`: the full saved artifact, including probe results, evidence signals, hypotheses, and summary metadata
- `report.html`: a reviewable analyst report

Each hypothesis includes:

- a bounded statement
- a confidence score and bucket
- supporting evidence
- weakening evidence
- alternative explanations
- recommended validation advice

This is the key contract for NAPST: it suggests likely structure and behavior, but it should not present black-box inference as hard architectural fact.

## Built-in Scenarios

- `map_core`: primary repeated-trial mapping scenario
- `boundary_baseline`: compatibility scenario for instruction and persona behavior
- `persistence_probe`: compatibility scenario for carryover signals
- `action_pressure`: compatibility scenario for tool and outbound posture

## Project Layout

- `napst_core`: models, scenario execution, evidence extraction, scoring, storage, reporting
- `napst_cli`: command-line operator surface
- `napst_ui`: lightweight local browser view over saved artifacts
- `docs/architecture.md`: architecture direction
- `docs/roadmap.md`: staged plan

## Running Tests

```bash
python -m pytest -q tests --basetemp .pytest-tmp -p no:cacheprovider
```

The explicit `--basetemp` and disabled cache provider make test runs more reliable on restrictive Windows setups.

## Architecture Direction

NAPST is being developed into a broader security evaluation suite. The first major goal is a robust mapper that estimates likely internal structure through a narrow frontend view while keeping evidence, confidence, and uncertainty visible.

See [docs/architecture.md](docs/architecture.md) for the architecture and [docs/roadmap.md](docs/roadmap.md) for the staged plan.

## Next Logical Step

The current run path is shaped correctly for real reachable HTTP JSON frontends. The next practical hardening step is better session-faithful execution for targets that rely on sticky state, cookies, or longer-lived client context. That will make persistence and statefulness estimates more trustworthy on legitimate agent frontends.
