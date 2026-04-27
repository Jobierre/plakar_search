import json
from datetime import datetime, timezone
from pathlib import Path


class IndexState:
    def __init__(self, repo: str, state_path: Path):
        self.repo = repo
        self.state_path = state_path
        self.snapshots: dict[str, str] = {}
        self.last_updated: str = ""

    @classmethod
    def load(cls, repo: str, state_path: Path) -> "IndexState":
        if state_path.exists():
            with open(state_path) as f:
                data = json.load(f)
            state = cls(repo, state_path)
            state.snapshots = data.get("snapshots", {})
            state.last_updated = data.get("last_updated", "")
            return state
        return cls(repo, state_path)

    def save(self) -> None:
        self.last_updated = datetime.now(timezone.utc).isoformat()
        data = {
            "store": self.repo,
            "snapshots": self.snapshots,
            "last_updated": self.last_updated,
        }
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.state_path.with_suffix(".json.tmp")
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        tmp_path.replace(self.state_path)

    def is_done(self, snapshot_id: str) -> bool:
        return self.snapshots.get(snapshot_id) == "done"

    def mark_in_progress(self, snapshot_id: str) -> None:
        self.snapshots[snapshot_id] = "in_progress"

    def mark_done(self, snapshot_id: str) -> None:
        self.snapshots[snapshot_id] = "done"

    @property
    def done_count(self) -> int:
        return sum(1 for s in self.snapshots.values() if s == "done")

    @property
    def total_count(self) -> int:
        return len(self.snapshots)
