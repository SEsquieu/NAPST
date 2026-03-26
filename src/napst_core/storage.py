from __future__ import annotations

import json
from pathlib import Path

from .models import ScenarioRun


class ArtifactStore:
    def __init__(self, root: str | Path = ".napst"):
        self.root = Path(root)
        self.runs_dir = self.root / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def next_run_id(self) -> str:
        existing = sorted(p.name for p in self.runs_dir.glob("run_*"))
        next_num = 1
        if existing:
            next_num = max(int(name.split("_")[-1]) for name in existing) + 1
        return f"run_{next_num:04d}"

    def save_run(self, run: ScenarioRun) -> Path:
        run_dir = self.runs_dir / run.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run.json").write_text(json.dumps(run.to_dict(), indent=2))
        return run_dir

    def load_run(self, run_id: str) -> dict:
        return json.loads((self.runs_dir / run_id / "run.json").read_text())

    def list_runs(self) -> list[dict]:
        items = []
        for path in sorted(self.runs_dir.glob("run_*")):
            data = json.loads((path / "run.json").read_text())
            hypotheses = data.get("hypotheses", [])
            findings = data.get("findings", [])
            items.append({
                "run_id": data["run_id"],
                "target_name": data["target_name"],
                "scenario": data["scenario"],
                "created_at": data["created_at"],
                "finding_count": len(findings),
                "hypothesis_count": len(hypotheses),
            })
        return items
