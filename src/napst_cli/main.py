from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from napst_core import NapstRunner, TargetConfig
from napst_core.scenarios import list_scenarios
from napst_core.storage import ArtifactStore

app = typer.Typer(help="NAPST - behavioral mapping and boundary inference for agentic systems")
console = Console()


@app.command()
def scenarios() -> None:
    """List bundled scenario packs."""
    table = Table(title="NAPST scenarios")
    table.add_column("Scenario")
    for name in list_scenarios():
        table.add_row(name)
    console.print(table)


@app.command()
def run(target_file: str, scenario: str = typer.Option("map_core", help="Scenario pack to execute")) -> None:
    """Run a scenario against a target YAML config."""
    target = TargetConfig.from_yaml(target_file)
    runner = NapstRunner()
    result = runner.run(target, scenario)
    console.print(
        f"[green]Completed[/green] {result.run_id} against [bold]{result.target_name}[/bold] "
        f"with scenario [bold]{result.scenario}[/bold]"
    )
    console.print(f"Hypotheses: {len(result.hypotheses)}")
    for hypothesis in result.hypotheses:
        console.print(
            f"- {hypothesis.title}: {hypothesis.confidence.bucket} "
            f"({hypothesis.confidence.score:.2f})"
        )
    console.print_json(json.dumps(result.summary))
    console.print(f"Report: .napst/runs/{result.run_id}/report.html")


@app.command("list-runs")
def list_runs() -> None:
    """List saved runs."""
    rows = ArtifactStore().list_runs()
    table = Table(title="NAPST runs")
    for col in ("Run ID", "Target", "Scenario", "Created", "Hypotheses"):
        table.add_column(col)
    for row in rows:
        table.add_row(
            row["run_id"],
            row["target_name"],
            row["scenario"],
            row["created_at"],
            str(row["hypothesis_count"]),
        )
    console.print(table)


@app.command()
def show(run_id: str) -> None:
    """Show run JSON."""
    data = ArtifactStore().load_run(run_id)
    console.print_json(json.dumps(data))


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Serve the lightweight local UI."""
    import uvicorn

    uvicorn.run("napst_ui.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
