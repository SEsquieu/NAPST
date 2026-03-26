import shutil
from pathlib import Path

import pytest

from napst_core.models import TargetConfig


def test_http_json_target_still_loads_from_yaml():
    temp_dir = Path.cwd() / ".napst-test-target-config"
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        config_path = temp_dir / "target.yaml"
        config_path.write_text(
            "\n".join(
                [
                    "name: demo",
                    "base_url: http://localhost:8000",
                    "endpoint: /chat",
                ]
            ),
            encoding="utf-8",
        )

        target = TargetConfig.from_yaml(config_path)

        assert target.type == "http_json"
        assert target.base_url == "http://localhost:8000"
        assert target.endpoint == "/chat"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_browser_target_requires_expected_fields():
    with pytest.raises(ValueError):
        TargetConfig(name="browser", type="browser_chat", start_url="https://example.com")


def test_browser_target_rejects_missing_send_button_when_enter_disabled():
    with pytest.raises(ValueError):
        TargetConfig(
            name="browser",
            type="browser_chat",
            start_url="https://example.com/chat",
            storage_state_path=".napst/storage.json",
            prompt_input_selector="textarea",
            response_container_selector=".assistant",
            submit_on_enter=False,
        )


def test_browser_target_infers_origin_allowlist():
    target = TargetConfig(
        name="browser",
        type="browser_chat",
        start_url="https://example.com/chat",
        storage_state_path=".napst/storage.json",
        prompt_input_selector="textarea",
        response_container_selector=".assistant",
    )

    assert target.origin_allowlist == ["https://example.com"]
