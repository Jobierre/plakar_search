import json
from pathlib import Path

from plakar_search.state import IndexState


class TestIndexStateInit:
    def test_init_empty(self, tmp_path):
        state_path = tmp_path / "state.json"
        state = IndexState("@gdrive", state_path)
        assert state.repo == "@gdrive"
        assert state.state_path == state_path
        assert state.snapshots == {}
        assert state.last_updated == ""
        assert state.done_count == 0
        assert state.total_count == 0


class TestIndexStateLoad:
    def test_load_from_existing_file(self, tmp_path):
        state_path = tmp_path / "state.json"
        data = {
            "store": "@gdrive",
            "snapshots": {"abc123": "done", "def456": "in_progress"},
            "last_updated": "2024-01-01T00:00:00",
        }
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w") as f:
            json.dump(data, f)

        state = IndexState.load("@gdrive", state_path)
        assert state.repo == "@gdrive"
        assert state.snapshots == {"abc123": "done", "def456": "in_progress"}
        assert state.last_updated == "2024-01-01T00:00:00"
        assert state.done_count == 1
        assert state.total_count == 2

    def test_load_missing_file(self, tmp_path):
        state_path = tmp_path / "nonexistent.json"
        state = IndexState.load("@gdrive", state_path)
        assert state.snapshots == {}
        assert state.last_updated == ""
        assert state.total_count == 0

    def test_load_partial_data(self, tmp_path):
        state_path = tmp_path / "state.json"
        data = {"store": "@gdrive"}
        with open(state_path, "w") as f:
            json.dump(data, f)

        state = IndexState.load("@gdrive", state_path)
        assert state.snapshots == {}
        assert state.last_updated == ""


class TestIndexStateSave:
    def test_save_creates_file(self, tmp_path):
        state_path = tmp_path / "subdir" / "state.json"
        state = IndexState("@gdrive", state_path)
        state.snapshots = {"abc123": "done"}
        state.save()

        assert state_path.exists()
        with open(state_path) as f:
            data = json.load(f)
        assert data["store"] == "@gdrive"
        assert data["snapshots"] == {"abc123": "done"}
        assert "last_updated" in data

    def test_save_atomic_no_tmp_leftover(self, tmp_path):
        state_path = tmp_path / "state.json"
        state = IndexState("@gdrive", state_path)
        state.save()

        tmp_path = state_path.with_suffix(".json.tmp")
        assert not tmp_path.exists(), "Le fichier temporaire ne devrait pas rester"
        assert state_path.exists()

    def test_save_overwrites(self, tmp_path):
        state_path = tmp_path / "state.json"
        state = IndexState("@gdrive", state_path)
        state.snapshots = {"old": "done"}
        state.save()

        state.snapshots = {"new": "done"}
        state.save()

        with open(state_path) as f:
            data = json.load(f)
        assert "new" in data["snapshots"]
        assert "old" not in data["snapshots"]

    def test_save_updates_last_updated(self, tmp_path):
        state_path = tmp_path / "state.json"
        state = IndexState("@gdrive", state_path)
        state.save()

        first_save = state.last_updated

        import time
        time.sleep(0.01)
        state.save()

        assert state.last_updated != first_save


class TestIndexStateLifecycle:
    def test_mark_and_check(self, tmp_path):
        state = IndexState("@gdrive", tmp_path / "state.json")
        assert not state.is_done("abc123")

        state.mark_in_progress("abc123")
        assert not state.is_done("abc123")

        state.mark_done("abc123")
        assert state.is_done("abc123")
        assert state.done_count == 1

    def test_multiple_snapshots(self, tmp_path):
        state = IndexState("@gdrive", tmp_path / "state.json")
        state.mark_done("snap1")
        state.mark_done("snap2")
        state.mark_in_progress("snap3")

        assert state.total_count == 3
        assert state.done_count == 2
        assert state.is_done("snap1")
        assert state.is_done("snap2")
        assert not state.is_done("snap3")
        assert not state.is_done("unknown")

    def test_load_resume(self, tmp_path):
        state_path = tmp_path / "state.json"
        state = IndexState("@gdrive", state_path)
        state.mark_done("snap1")
        state.mark_in_progress("snap2")
        state.save()

        reloaded = IndexState.load("@gdrive", state_path)
        assert reloaded.is_done("snap1")
        assert not reloaded.is_done("snap2")
        assert reloaded.total_count == 2
        assert reloaded.done_count == 1
