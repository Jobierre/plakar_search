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
        result = self._run("ls", "--json")
        return json.loads(result.stdout)

    def list_files(self, snapshot: str) -> list[dict]:
        result = self._run("ls", snapshot, "--json")
        return json.loads(result.stdout)

    def cat(self, snapshot: str, path: str) -> bytes:
        cmd = ["plakar", "at", self.repo, "cat", f"{snapshot}:{path}"]
        try:
            result = subprocess.run(cmd, capture_output=True, check=True, env=self._env())
        except subprocess.CalledProcessError as e:
            raise PlakarError(f"Plakar a echoue : {e.stderr.decode().strip()}" if e.stderr else "") from e
        except FileNotFoundError:
            raise PlakarError("L'outil 'plakar' est introuvable. Verifie qu'il est installe et dans le PATH.")
        return result.stdout
