from __future__ import annotations

from typing import Protocol

from .browser_transport import BrowserChatTransport
from .http_client import HttpJsonTransport
from .models import Probe, ProbeResult, TargetConfig


class TargetTransport(Protocol):
    def start_trial(self, trial_index: int) -> None: ...

    def invoke(self, probe: Probe, trial_index: int, sequence_index: int) -> ProbeResult: ...

    def end_trial(self, trial_index: int) -> None: ...

    def close(self) -> None: ...


def build_transport(target: TargetConfig) -> TargetTransport:
    if target.type == "browser_chat":
        return BrowserChatTransport(target)
    return HttpJsonTransport(target)
