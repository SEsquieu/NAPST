from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from napst_core import NapstRunner, TargetConfig
from napst_core.capture import capture_browser_target, infer_name_from_url
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


@app.command()
def capture(
    url: str,
    name: str | None = typer.Option(None, help="Target profile name"),
    output_root: str = typer.Option(".napst", help="Root directory for saved target artifacts"),
) -> None:
    """Capture a reusable browser target profile for a chat frontend."""
    chosen_name = name or infer_name_from_url(url)
    console.print(f"Preparing browser capture for [bold]{chosen_name}[/bold] at [cyan]{url}[/cyan]")
    console.print("A browser window will open. Log in normally, navigate to the chat surface, then return here.")
    typer.confirm("Ready to launch the browser capture flow?", abort=True)
    prompt_input_selector = typer.prompt("Prompt input selector", default="textarea")
    response_container_selector = typer.prompt("Response container selector", default="[data-message-role='assistant']")
    submit_on_enter = typer.confirm("Submit prompts by pressing Enter?", default=True)
    send_button_selector = None
    if not submit_on_enter:
        send_button_selector = typer.prompt("Send button selector")
    ready_selector = typer.prompt("Ready selector (optional)", default="", show_default=False) or None
    typing_indicator_selector = (
        typer.prompt("Typing indicator selector (optional)", default="", show_default=False) or None
    )
    console.print("The browser will stay open long enough for you to authenticate before saving storage state.")
    target_file, storage_state = capture_browser_target(
        url=url,
        name=chosen_name,
        prompt_input_selector=prompt_input_selector,
        response_container_selector=response_container_selector,
        send_button_selector=send_button_selector,
        submit_on_enter=submit_on_enter,
        ready_selector=ready_selector,
        typing_indicator_selector=typing_indicator_selector,
        wait_timeout_seconds=20.0,
        inter_probe_delay_seconds=0.75,
        before_save_callback=lambda: typer.confirm(
            "After you log in and confirm the chat surface is ready, save the session state?",
            default=True,
            abort=True,
        ),
        root=output_root,
    )
    console.print(f"Saved target profile: {target_file}")
    console.print(f"Saved storage state: {storage_state}")
    console.print(f"Run with: napst run {target_file} --scenario map_core")


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
