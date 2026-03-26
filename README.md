# NAPST

NAPST is a black-box mapping tool for LLM and agentic systems.

It interacts with a frontend, applies structured probe sequences, and reports bounded hypotheses about likely system behavior with explicit confidence. It is built for security-minded users who want a careful estimate, not a made-up architecture diagram.

## What NAPST Does

- Sends repeatable probe scenarios to an HTTP JSON model or agent frontend
- Can drive a configured browser chat frontend using Playwright and a captured analyst session
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

- Target type: HTTP JSON frontends and single-surface browser chat frontends
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

Install Playwright browsers if you want to use browser-backed targets:

```bash
playwright install
```

Install dev dependencies if you want to run tests:

```bash
pip install -e .[dev]
```

## Quickstart

HTTP JSON flow:

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

Browser frontend flow:

```bash
napst capture https://target.example.com/chat
napst run .napst/targets/<captured-name>/target.yaml --scenario map_core
```

The capture flow opens a browser window, lets the analyst authenticate normally, and saves:

- a reusable Playwright storage state
- a browser target profile with the chat selectors you confirmed

The CLI currently asks for:

- the prompt input selector
- the assistant response container selector
- whether submit happens on `Enter` or a send button
- optional ready and typing-indicator selectors

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
type: http_json
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

## Example Browser Target Config

```yaml
name: example-chat
type: browser_chat
start_url: https://target.example.com/chat
origin_allowlist:
  - https://target.example.com
storage_state_path: .napst/targets/example-chat/storage_state.json
prompt_input_selector: textarea
submit_on_enter: true
response_container_selector: "[data-message-role='assistant']"
ready_selector: textarea
typing_indicator_selector: .typing-indicator
wait_timeout_seconds: 20
inter_probe_delay_seconds: 0.75
notes: Frontend-observed black-box browser target captured for NAPST.
```

Use `submit_on_enter: false` plus `send_button_selector` when the UI requires clicking a send control.

## CLI

```bash
napst scenarios
napst run examples/simple_target.yaml --scenario map_core
napst capture https://target.example.com/chat
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

## Browser Target Notes

Browser-backed targets are intentionally narrow in v1:

- one known chat surface
- analyst-authenticated session reuse via saved Playwright storage state
- no autonomous crawling or multi-page workflows
- conservative interaction limited to configured chat selectors on an allowlisted origin
