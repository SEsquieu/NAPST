from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from napst_core.storage import ArtifactStore

app = FastAPI(title="NAPST UI")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    rows = ArtifactStore().list_runs()
    items = "".join(
        f"<li><a href='/runs/{row['run_id']}'>{row['run_id']}</a> - {row['target_name']} - {row['scenario']} ({row['finding_count']} findings)</li>"
        for row in rows
    ) or "<li>No runs yet</li>"
    return f"""
    <html><body style='font-family: Arial; margin: 2rem'>
      <h1>NAPST local UI</h1>
      <p>Lightweight browser sugar over saved artifacts.</p>
      <ul>{items}</ul>
    </body></html>
    """


@app.get("/runs/{run_id}", response_class=HTMLResponse)
def run_view(run_id: str) -> str:
    data = ArtifactStore().load_run(run_id)
    findings = "".join(
        f"<li><strong>{f['title']}</strong> ({f['severity']}): {f['observation']}</li>" for f in data.get("findings", [])
    ) or "<li>No findings</li>"
    return f"""
    <html><body style='font-family: Arial; margin: 2rem'>
      <h1>{data['run_id']}</h1>
      <p>Target: {data['target_name']} · Scenario: {data['scenario']}</p>
      <h2>Summary</h2>
      <pre>{data['summary']}</pre>
      <h2>Findings</h2>
      <ul>{findings}</ul>
      <p><a href='/'>Back</a></p>
    </body></html>
    """
