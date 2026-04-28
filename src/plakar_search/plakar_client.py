import json
import os
import subprocess


class PlakarError(Exception):
    pass


class PlakarClient:
    def __init__(self, repo: str, passphrase: str | None = None):
        self.repo = repo
        self.passphrase = passphrase
        self._is_named = repo.startswith("@")

        if not self._is_named and not passphrase:
            raise PlakarError(
                "Passphrase requise pour ce store. Utilise --passphrase ou la variable PLAKAR_PASSPHRASE."
            )

    def _env(self) -> dict[str, str]:
        env = os.environ.copy()
        if self.passphrase:
            env["PLAKAR_PASSPHRASE"] = self.passphrase
        return env

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        cmd = ["plakar", "at", self.repo, *args]
        try:
            return subprocess.run(cmd, capture_output=True, text=True, check=True, env=self._env())
        except subprocess.CalledProcessError as e:
            raise PlakarError(f"Plakar a echoue : {e.stderr.strip() or e.stdout.strip()}") from e
        except FileNotFoundError:
            raise PlakarError("L'outil 'plakar' est introuvable. Verifie qu'il est installe et dans le PATH.")

    def list_snapshots(self) -> list[dict]:
        result = self._run("ls")
        snapshots = []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 5)
            if len(parts) < 6:
                continue
            snapshots.append({
                "id": parts[1],
                "date": parts[0],
                "size": f"{parts[2]} {parts[3]}",
                "duration": parts[4],
                "root_path": parts[5],
            })
        return snapshots

    def list_files(self, snapshot: str) -> list[dict]:
        result = self._run("ls", "-recursive", snapshot)
        files = []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 6)
            if len(parts) < 7:
                continue
            files.append({
                "date": parts[0],
                "perms": parts[1],
                "owner": parts[2],
                "group": parts[3],
                "size": f"{parts[4]} {parts[5]}",
                "path": parts[6],
                "mime_type": "",
            })
        return files

    def cat(self, snapshot: str, path: str) -> bytes:
        cmd = ["plakar", "at", self.repo, "cat", f"{snapshot}:{path}"]
        try:
            result = subprocess.run(cmd, capture_output=True, check=True, env=self._env())
        except subprocess.CalledProcessError as e:
            raise PlakarError(f"Plakar a echoue : {e.stderr.decode().strip()}" if e.stderr else "") from e
        except FileNotFoundError:
            raise PlakarError("L'outil 'plakar' est introuvable. Verifie qu'il est installe et dans le PATH.")
        return result.stdout
