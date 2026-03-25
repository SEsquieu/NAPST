from __future__ import annotations

from pathlib import Path

from jinja2 import Template


HTML_TEMPLATE = Template("""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>NAPST report - {{ run.run_id }}</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 2rem; color: #111; }
    h1, h2 { margin-bottom: 0.3rem; }
    .muted { color: #666; }
    .finding { border: 1px solid #ddd; border-left: 5px solid #444; padding: 1rem; margin: 1rem 0; }
    .severity-medium { border-left-color: #d97706; }
    .severity-low { border-left-color: #2563eb; }
    .severity-info { border-left-color: #059669; }
    code, pre { background: #f6f8fa; padding: 0.2rem 0.35rem; }
    table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
    th, td { text-align: left; border-bottom: 1px solid #ddd; padding: 0.5rem; vertical-align: top; }
  </style>
</head>
<body>
  <h1>NAPST report</h1>
  <div class="muted">Run {{ run.run_id }} · Target {{ run.target_name }} · Scenario {{ run.scenario }}</div>

  <h2>Boundary summary</h2>
  <pre>{{ run.summary | tojson(indent=2) }}</pre>

  <h2>Findings</h2>
  {% if run.findings %}
    {% for finding in run.findings %}
      <div class="finding severity-{{ finding.severity }}">
        <strong>{{ finding.title }}</strong>
        <div><strong>Severity:</strong> {{ finding.severity }}</div>
        <div><strong>Observation:</strong> {{ finding.observation }}</div>
        <div><strong>Implication:</strong> {{ finding.implication }}</div>
        <div><strong>Recommendation:</strong> {{ finding.recommendation }}</div>
        <div><strong>Evidence:</strong> {{ finding.evidence | join(', ') }}</div>
      </div>
    {% endfor %}
  {% else %}
    <p>No findings were inferred from this run.</p>
  {% endif %}

  <h2>Probe results</h2>
  <table>
    <thead>
      <tr><th>Probe</th><th>Latency</th><th>Prompt</th><th>Response</th></tr>
    </thead>
    <tbody>
      {% for result in run.probe_results %}
      <tr>
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
""")


def write_html_report(run: dict, output_path: str | Path) -> None:
    output = Path(output_path)
    output.write_text(HTML_TEMPLATE.render(run=run))
