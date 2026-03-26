import shutil
from pathlib import Path

from napst_core.browser_transport import BrowserChatTransport
from napst_core.models import Probe, TargetConfig


class FakeLocator:
    def __init__(self, entries):
        self.entries = entries
        self.filled = []
        self.pressed = []
        self.clicked = 0

    def count(self):
        return len(self.entries)

    @property
    def first(self):
        return self

    def nth(self, index: int):
        return FakeLocator([self.entries[index]])

    def fill(self, value: str):
        self.filled.append(value)

    def press(self, key: str):
        self.pressed.append(key)

    def click(self):
        self.clicked += 1

    def inner_text(self):
        return self.entries[0]

    def is_visible(self):
        return True


class FakePage:
    def __init__(self, *, url: str = "https://example.com/chat", selectors=None):
        self.url = url
        self._selectors = selectors or {}

    def locator(self, selector: str):
        return self._selectors.get(selector, FakeLocator([]))


def build_target(storage_state_path: Path) -> TargetConfig:
    storage_state_path.write_text("{}", encoding="utf-8")
    return TargetConfig(
        name="browser",
        type="browser_chat",
        start_url="https://example.com/chat",
        storage_state_path=str(storage_state_path),
        prompt_input_selector="textarea",
        response_container_selector=".assistant",
        typing_indicator_selector=".typing",
    )


def test_browser_transport_successful_probe_response(monkeypatch):
    temp_dir = Path.cwd() / ".napst-test-browser-success"
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr("napst_core.browser_transport.time.sleep", lambda _: None)
        target = build_target(temp_dir / "storage.json")
        transport = BrowserChatTransport(target)
        transport._page = FakePage(
            selectors={
                "textarea": FakeLocator([""]),
                ".assistant": FakeLocator(["prior", "fresh response"]),
                ".typing": FakeLocator([]),
            }
        )
        transport._context = object()
        transport._current_trial_index = 1
        monkeypatch.setattr(
            transport,
            "_wait_for_response",
            lambda before_count: transport._network_events.append({"url": "https://example.com/api", "status": 200})
            or "fresh response",
        )

        result = transport.invoke(Probe(name="baseline", prompt="hi"), trial_index=1, sequence_index=1)

        assert result.response_text == "fresh response"
        assert result.metadata["transport"]["type"] == "browser_chat"
        assert result.metadata["transport"]["network_events"] == [{"url": "https://example.com/api", "status": 200}]
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_browser_transport_reports_missing_selector(monkeypatch):
    temp_dir = Path.cwd() / ".napst-test-browser-missing-selector"
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr("napst_core.browser_transport.time.sleep", lambda _: None)
        target = build_target(temp_dir / "storage.json")
        transport = BrowserChatTransport(target)
        transport._page = FakePage(selectors={".assistant": FakeLocator(["prior"])})
        transport._context = object()
        transport._current_trial_index = 1

        result = transport.invoke(Probe(name="baseline", prompt="hi"), trial_index=1, sequence_index=1)

        assert "Prompt input selector not found" in (result.error or "")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_browser_transport_reports_allowlist_violation(monkeypatch):
    temp_dir = Path.cwd() / ".napst-test-browser-allowlist"
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr("napst_core.browser_transport.time.sleep", lambda _: None)
        target = build_target(temp_dir / "storage.json")
        transport = BrowserChatTransport(target)
        transport._page = FakePage(url="https://evil.example.net/chat", selectors={"textarea": FakeLocator([""])})
        transport._context = object()
        transport._current_trial_index = 1

        result = transport.invoke(Probe(name="baseline", prompt="hi"), trial_index=1, sequence_index=1)

        assert "allowlisted origin" in (result.error or "")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
