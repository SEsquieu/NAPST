from __future__ import annotations

import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .models import Probe, ProbeResult, TargetConfig


class BrowserChatTransport:
    def __init__(self, target: TargetConfig):
        self.target = target
        self._playwright_manager = None
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._network_events: list[dict[str, Any]] = []
        self._current_trial_index: int | None = None

    def _ensure_playwright(self) -> None:
        if self._playwright is not None:
            return
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is required for browser_chat targets. Install dependencies and run 'playwright install'."
            ) from exc
        self._playwright_manager = sync_playwright()
        self._playwright = self._playwright_manager.start()
        self._browser = self._playwright.chromium.launch(headless=True)

    def _assert_allowlisted(self, url: str) -> None:
        origin = _origin_for(url)
        if origin not in self.target.origin_allowlist:
            raise RuntimeError(f"Page navigated outside allowlisted origin: {origin}")

    def _attach_network_listeners(self) -> None:
        self._network_events = []

        def on_response(response: Any) -> None:
            url = response.url
            if _origin_for(url) not in self.target.origin_allowlist:
                return
            headers = response.headers
            self._network_events.append(
                {
                    "url": url,
                    "method": response.request.method,
                    "status": response.status,
                    "content_type": headers.get("content-type"),
                    "streaming_hint": "text/event-stream" in headers.get("content-type", "").lower()
                    or headers.get("transfer-encoding", "").lower() == "chunked",
                }
            )

        assert self._page is not None
        self._page.on("response", on_response)

    def _prepare_page(self) -> None:
        assert self._page is not None
        self._page.goto(self.target.start_url or "", wait_until="domcontentloaded")
        self._assert_allowlisted(self._page.url)
        if self.target.ready_selector:
            self._page.wait_for_selector(self.target.ready_selector, timeout=int(self.target.wait_timeout_seconds * 1000))
        self._page.wait_for_selector(
            self.target.prompt_input_selector or "",
            timeout=int(self.target.wait_timeout_seconds * 1000),
        )
        self._page.wait_for_selector(
            self.target.response_container_selector or "",
            timeout=int(self.target.wait_timeout_seconds * 1000),
        )
        self._attach_network_listeners()

    def start_trial(self, trial_index: int) -> None:
        self._ensure_playwright()
        self.end_trial(trial_index - 1)
        storage_state_path = Path(self.target.storage_state_path or "")
        if not storage_state_path.exists():
            raise RuntimeError(f"Storage state file not found: {storage_state_path}")
        assert self._browser is not None
        self._context = self._browser.new_context(storage_state=str(storage_state_path))
        self._page = self._context.new_page()
        self._current_trial_index = trial_index
        self._prepare_page()

    def _wait_for_response(self, before_count: int) -> str:
        assert self._page is not None
        timeout_ms = int(self.target.wait_timeout_seconds * 1000)
        deadline = time.time() + self.target.wait_timeout_seconds
        selector = self.target.response_container_selector or ""
        while time.time() < deadline:
            self._assert_allowlisted(self._page.url)
            handles = self._page.locator(selector)
            count = handles.count()
            if count > before_count:
                latest = handles.nth(count - 1)
                text = latest.inner_text().strip()
                if text:
                    if self.target.typing_indicator_selector:
                        indicators = self._page.locator(self.target.typing_indicator_selector)
                        if indicators.count() and indicators.first.is_visible():
                            time.sleep(0.2)
                            continue
                    time.sleep(0.4)
                    refreshed = latest.inner_text().strip()
                    if refreshed == text:
                        return refreshed
            time.sleep(0.2)
        raise TimeoutError(f"No stable response found within {timeout_ms} ms")

    def invoke(self, probe: Probe, trial_index: int, sequence_index: int) -> ProbeResult:
        if self._page is None or self._context is None or self._current_trial_index != trial_index:
            raise RuntimeError("Browser transport trial has not been started")
        page = self._page
        try:
            self._assert_allowlisted(page.url)
            input_selector = self.target.prompt_input_selector or ""
            response_selector = self.target.response_container_selector or ""
            input_box = page.locator(input_selector)
            if input_box.count() == 0:
                raise RuntimeError(f"Prompt input selector not found: {input_selector}")
            self._network_events = []
            response_count = page.locator(response_selector).count()
            start = time.perf_counter()
            input_box.first.fill(probe.prompt)
            if self.target.submit_on_enter:
                input_box.first.press("Enter")
            else:
                send_selector = self.target.send_button_selector or ""
                send_button = page.locator(send_selector)
                if send_button.count() == 0:
                    raise RuntimeError(f"Send button selector not found: {send_selector}")
                send_button.first.click()
            response_text = self._wait_for_response(response_count)
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            metadata = dict(probe.metadata)
            metadata["transport"] = {
                "type": "browser_chat",
                "page_url": page.url,
                "network_events": list(self._network_events),
            }
            result = ProbeResult(
                probe_name=probe.name,
                prompt=probe.prompt,
                status_code=200,
                latency_ms=latency_ms,
                response_text=response_text,
                tags=probe.tags,
                trial_index=trial_index,
                sequence_index=sequence_index,
                expected_signal=probe.expected_signal,
                metadata=metadata,
            )
            time.sleep(self.target.inter_probe_delay_seconds)
            return result
        except Exception as exc:
            metadata = dict(probe.metadata)
            metadata["transport"] = {
                "type": "browser_chat",
                "page_url": page.url,
                "network_events": list(self._network_events),
            }
            return ProbeResult(
                probe_name=probe.name,
                prompt=probe.prompt,
                status_code=None,
                latency_ms=0.0,
                response_text="",
                tags=probe.tags,
                trial_index=trial_index,
                sequence_index=sequence_index,
                expected_signal=probe.expected_signal,
                metadata=metadata,
                error=str(exc),
            )

    def end_trial(self, trial_index: int) -> None:
        if self._page is not None:
            self._page.close()
            self._page = None
        if self._context is not None:
            self._context.close()
            self._context = None
        self._current_trial_index = None

    def close(self) -> None:
        self.end_trial(-1)
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright_manager is not None:
            self._playwright_manager.stop()
            self._playwright_manager = None
            self._playwright = None


def _origin_for(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"
