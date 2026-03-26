from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import yaml

from .models import TargetConfig


def slugify_name(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or "target"


def infer_name_from_url(url: str) -> str:
    parsed = urlparse(url)
    base = parsed.netloc or parsed.path or "browser-target"
    return slugify_name(base)


def capture_browser_target(
    *,
    url: str,
    name: str,
    prompt_input_selector: str,
    response_container_selector: str,
    send_button_selector: str | None,
    submit_on_enter: bool,
    ready_selector: str | None,
    typing_indicator_selector: str | None,
    wait_timeout_seconds: float,
    inter_probe_delay_seconds: float,
    before_save_callback: callable | None = None,
    root: str | Path = ".napst",
) -> tuple[Path, Path]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is required for browser capture. Install dependencies and run 'playwright install'."
        ) from exc

    root_path = Path(root)
    target_slug = slugify_name(name)
    target_dir = root_path / "targets" / target_slug
    target_dir.mkdir(parents=True, exist_ok=True)
    storage_state_path = target_dir / "storage_state.json"
    target_file_path = target_dir / "target.yaml"
    origin = _origin_for(url)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(1000)
        if before_save_callback is not None:
            before_save_callback()
        context.storage_state(path=str(storage_state_path))
        browser.close()

    target = TargetConfig(
        name=name,
        type="browser_chat",
        start_url=url,
        origin_allowlist=[origin],
        storage_state_path=str(storage_state_path),
        prompt_input_selector=prompt_input_selector,
        send_button_selector=send_button_selector,
        submit_on_enter=submit_on_enter,
        response_container_selector=response_container_selector,
        ready_selector=ready_selector,
        typing_indicator_selector=typing_indicator_selector,
        wait_timeout_seconds=wait_timeout_seconds,
        inter_probe_delay_seconds=inter_probe_delay_seconds,
        notes="Frontend-observed black-box browser target captured for NAPST.",
    )
    target_file_path.write_text(yaml.safe_dump(target.model_dump(exclude_none=True), sort_keys=False), encoding="utf-8")
    return target_file_path, storage_state_path


def _origin_for(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"
