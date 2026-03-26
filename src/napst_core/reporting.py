from __future__ import annotations

from pathlib import Path

from jinja2 import Template


HTML_TEMPLATE = Template(
    """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>NAPST report - {{ run.run_id }}</title>
  <style>
    :root {
      --ink: #1f2933;
      --muted: #52606d;
      --panel: #f5f7fa;
      --line: #d9e2ec;
      --accent: #0f4c5c;
      --high: #9d0208;
      --medium: #ca6702;
      --low: #0a9396;
    }
    body { font-family: "Segoe UI", Arial, sans-serif; margin: 2rem; color: var(--ink); line-height: 1.5; }
    h1, h2, h3 { margin-bottom: 0.35rem; }
    .muted { color: var(--muted); }
    .panel { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 1rem 1.25rem; margin: 1rem 0; }
    .hypothesis { border-left: 6px solid var(--accent); }
    .bucket-high, .bucket-very_high { border-left-color: var(--high); }
    .bucket-medium { border-left-color: var(--medium); }
    .bucket-low, .bucket-very_low { border-left-color: var(--low); }
    code, pre { background: #f8fafc; padding: 0.2rem 0.35rem; }
    pre { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
    th, td { text-align: left; border-bottom: 1px solid var(--line); padding: 0.6rem; vertical-align: top; }
    ul { margin-top: 0.4rem; }
    .pill { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 999px; background: #e0fbfc; color: #083344; font-size: 0.9rem; margin-right: 0.35rem; }
  </style>
</head>
<body>
  <h1>NAPST mapping report</h1>
  <div class="muted">Run {{ run.run_id }} · Target {{ run.target_name }} · Scenario {{ run.scenario }}</div>
  <p>{{ run.scenario_description }}</p>

  <div class="panel">
    <h2>Run summary</h2>
    <pre>{{ run.summary | tojson(indent=2) }}</pre>
  </div>

  <h2>Hypotheses</h2>
  {% if run.hypotheses %}
    {% for hypothesis in run.hypotheses %}
      <div class="panel hypothesis bucket-{{ hypothesis.confidence.bucket }}">
        <h3>{{ hypothesis.title }}</h3>
        <div>
          <span class="pill">{{ hypothesis.category }}</span>
          <span class="pill">score {{ "%.2f"|format(hypothesis.confidence.score) }}</span>
          <span class="pill">{{ hypothesis.confidence.bucket }}</span>
        </div>
        <p><strong>Statement:</strong> {{ hypothesis.statement }}</p>
        <p><strong>Why this score:</strong> {{ hypothesis.confidence.rationale }}</p>
        <p><strong>Supporting evidence:</strong> {{ hypothesis.supporting_evidence_ids | join(", ") or "None" }}</p>
        <p><strong>Weakening evidence:</strong> {{ hypothesis.counterevidence_ids | join(", ") or "None" }}</p>
        <p><strong>Validation advice:</strong> {{ hypothesis.recommended_validation }}</p>
        <strong>Alternative explanations</strong>
        <ul>
          {% for alternative in hypothesis.alternative_explanations %}
            <li>{{ alternative }}</li>
          {% endfor %}
        </ul>
      </div>
    {% endfor %}
  {% else %}
    <p>No hypotheses were scored from this run.</p>
  {% endif %}

  <h2>Evidence signals</h2>
  {% if run.evidence_signals %}
    <table>
      <thead>
        <tr><th>ID</th><th>Kind</th><th>Score</th><th>Description</th><th>Probes</th><th>Trials</th></tr>
      </thead>
      <tbody>
        {% for signal in run.evidence_signals %}
        <tr>
          <td><code>{{ signal.id }}</code></td>
          <td>{{ signal.kind }}</td>
          <td>{{ "%.2f"|format(signal.score) }}</td>
          <td>{{ signal.description }}</td>
          <td>{{ signal.supporting_probe_names | join(", ") }}</td>
          <td>{{ signal.trial_indexes | join(", ") }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  {% else %}
    <p>No evidence signals were extracted.</p>
  {% endif %}

  <h2>Probe results</h2>
  <table>
    <thead>
      <tr><th>Trial</th><th>Seq</th><th>Probe</th><th>Latency</th><th>Prompt</th><th>Response</th></tr>
    </thead>
    <tbody>
      {% for result in run.probe_results %}
      <tr>
        <td>{{ result.trial_index }}</td>
        <td>{{ result.sequence_index }}</td>
        <td>{{ result.probe_name }}</td>
        <td>{{ result.latency_ms }} ms</td>
        <td><pre>{{ result.prompt }}</pre></td>
        <td><pre>{{ result.response_text or result.error }}</pre></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</body>
</html>
"""
)


def write_html_report(run: dict, output_path: str | Path) -> None:
    output = Path(output_path)
    output.write_text(HTML_TEMPLATE.render(run=run), encoding="utf-8")
