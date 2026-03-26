import shutil
from pathlib import Path

import yaml
from typer.testing import CliRunner

from napst_cli.main import app


runner = CliRunner()


def test_capture_command_writes_target_profile(monkeypatch):
    temp_dir = Path.cwd() / ".napst-test-cli-capture"
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        target_file = temp_dir / "targets" / "demo" / "target.yaml"
        storage_state = temp_dir / "targets" / "demo" / "storage_state.json"

        def fake_capture_browser_target(**kwargs):
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text("name: demo\n", encoding="utf-8")
            storage_state.write_text("{}", encoding="utf-8")
            return target_file, storage_state

        monkeypatch.setattr("napst_cli.main.capture_browser_target", fake_capture_browser_target)
        result = runner.invoke(
            app,
            ["capture", "https://example.com/chat", "--output-root", str(temp_dir)],
            input="y\ntextarea\n.assistant\ny\n\n\n\ny\n",
        )

        assert result.exit_code == 0
        assert target_file.exists()
        assert storage_state.exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_run_command_accepts_browser_target(monkeypatch):
    temp_dir = Path.cwd() / ".napst-test-cli-run"
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        target_path = temp_dir / "browser.yaml"
        target_path.write_text(
            yaml.safe_dump(
                {
                    "name": "browser",
                    "type": "browser_chat",
                    "start_url": "https://example.com/chat",
                    "origin_allowlist": ["https://example.com"],
                    "storage_state_path": str(temp_dir / "state.json"),
                    "prompt_input_selector": "textarea",
                    "response_container_selector": ".assistant",
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        (temp_dir / "state.json").write_text("{}", encoding="utf-8")

        class FakeRunner:
            def run(self, target, scenario):
                return type(
                    "Result",
                    (),
                    {
                        "run_id": "run_0001",
                        "target_name": target.name,
                        "scenario": scenario,
                        "hypotheses": [],
                        "summary": {"probe_count": 1},
                    },
                )()

        monkeypatch.setattr("napst_cli.main.NapstRunner", lambda: FakeRunner())
        result = runner.invoke(app, ["run", str(target_path), "--scenario", "map_core"])

        assert result.exit_code == 0
        assert "Completed" in result.stdout
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
