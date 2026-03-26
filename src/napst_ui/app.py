from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from napst_core.storage import ArtifactStore

app = FastAPI(title="NAPST UI")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    rows = ArtifactStore().list_runs()
    items = "".join(
        (
            f"<li><a href='/runs/{row['run_id']}'>{row['run_id']}</a> - {row['target_name']} - "
            f"{row['scenario']} ({row['hypothesis_count']} hypotheses)</li>"
        )
        for row in rows
    ) or "<li>No runs yet</li>"
    return f"""
    <html><body style='font-family: Segoe UI, Arial; margin: 2rem'>
      <h1>NAPST local UI</h1>
      <p>Lightweight browser sugar over saved mapping artifacts.</p>
      <ul>{items}</ul>
    </body></html>
    """


@app.get("/runs/{run_id}", response_class=HTMLResponse)
def run_view(run_id: str) -> str:
    data = ArtifactStore().load_run(run_id)
    hypotheses = "".join(
        (
            f"<li><strong>{hypothesis['title']}</strong> "
            f"({hypothesis['confidence']['bucket']} {hypothesis['confidence']['score']:.2f}): "
            f"{hypothesis['statement']}</li>"
        )
        for hypothesis in data.get("hypotheses", [])
    ) or "<li>No hypotheses</li>"
    return f"""
    <html><body style='font-family: Segoe UI, Arial; margin: 2rem'>
      <h1>{data['run_id']}</h1>
      <p>Target: {data['target_name']} · Scenario: {data['scenario']}</p>
      <h2>Summary</h2>
      <pre>{json.dumps(data['summary'], indent=2)}</pre>
      <h2>Hypotheses</h2>
      <ul>{hypotheses}</ul>
      <p><a href='/'>Back</a></p>
    </body></html>
    """
