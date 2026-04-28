import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from plakar_search.plakar_client import PlakarClient, PlakarError


class TestPlakarClientInit:
    def test_named_store_no_passphrase(self):
        client = PlakarClient("@gdrive")
        assert client.repo == "@gdrive"
        assert client.passphrase is None
        assert client._is_named is True

    def test_named_store_with_passphrase(self):
        client = PlakarClient("@gdrive", "secret")
        assert client.passphrase == "secret"

    def test_path_store_with_passphrase(self):
        client = PlakarClient("/var/backups", "secret")
        assert client.repo == "/var/backups"
        assert client.passphrase == "secret"
        assert client._is_named is False

    def test_path_store_without_passphrase_raises(self):
        with pytest.raises(PlakarError, match="Passphrase requise"):
            PlakarClient("/var/backups")

    def test_env_no_passphrase(self):
        client = PlakarClient("@gdrive")
        env = client._env()
        assert "PLAKAR_PASSPHRASE" not in env

    def test_env_with_passphrase(self):
        client = PlakarClient("/var/backups", "secret")
        env = client._env()
        assert env["PLAKAR_PASSPHRASE"] == "secret"


class TestPlakarClientRun:
    def test_run_success(self):
        client = PlakarClient("@gdrive")
        mock_result = MagicMock()
        mock_result.stdout = '[]'

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = client._run("ls", "--json")
            mock_run.assert_called_once_with(
                ["plakar", "at", "@gdrive", "ls", "--json"],
                capture_output=True,
                text=True,
                check=True,
                env=client._env(),
            )
            assert result == mock_result

    def test_run_called_process_error(self):
        client = PlakarClient("@gdrive")
        error = subprocess.CalledProcessError(1, "cmd", stderr="store inaccessible")

        with patch("subprocess.run", side_effect=error):
            with pytest.raises(PlakarError, match="store inaccessible"):
                client._run("ls")

    def test_run_called_process_error_stdout_fallback(self):
        client = PlakarClient("@gdrive")
        error = subprocess.CalledProcessError(1, "cmd", output="erreur stdout", stderr="")

        with patch("subprocess.run", side_effect=error):
            with pytest.raises(PlakarError, match="erreur stdout"):
                client._run("ls")

    def test_run_file_not_found(self):
        client = PlakarClient("@gdrive")

        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(PlakarError, match="plakar.*introuvable"):
                client._run("ls")


class TestPlakarClientListSnapshots:
    def test_list_snapshots(self):
        client = PlakarClient("@gdrive")
        fake_snapshots = [{"id": "abc123", "date": "2024-01-01"}]
        mock_result = MagicMock()
        mock_result.stdout = json.dumps(fake_snapshots)

        with patch.object(client, "_run", return_value=mock_result) as mock_run:
            result = client.list_snapshots()
            mock_run.assert_called_once_with("ls", "--json")
            assert result == fake_snapshots

    def test_list_snapshots_empty(self):
        client = PlakarClient("@gdrive")
        mock_result = MagicMock()
        mock_result.stdout = "[]"

        with patch.object(client, "_run", return_value=mock_result):
            result = client.list_snapshots()
            assert result == []


class TestPlakarClientListFiles:
    def test_list_files(self):
        client = PlakarClient("@gdrive")
        fake_files = [
            {"path": "/doc.txt", "mime_type": "text/plain"},
            {"path": "/img.jpg", "mime_type": "image/jpeg"},
        ]
        mock_result = MagicMock()
        mock_result.stdout = json.dumps(fake_files)

        with patch.object(client, "_run", return_value=mock_result) as mock_run:
            result = client.list_files("abc123")
            mock_run.assert_called_once_with("ls", "abc123", "--json")
            assert result == fake_files


class TestPlakarClientCat:
    def test_cat_text(self):
        client = PlakarClient("@gdrive")
        content = b"hello world"

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = content
            mock_run.return_value = mock_result

            result = client.cat("abc123", "/doc.txt")
            mock_run.assert_called_once_with(
                ["plakar", "at", "@gdrive", "cat", "abc123:/doc.txt"],
                capture_output=True,
                check=True,
                env=client._env(),
            )
            assert result == content

    def test_cat_error(self):
        client = PlakarClient("@gdrive")
        error = subprocess.CalledProcessError(1, "cmd", stderr=b"file not found")

        with patch("subprocess.run", side_effect=error):
            with pytest.raises(PlakarError, match="file not found"):
                client.cat("abc123", "/missing.txt")

    def test_cat_file_not_found(self):
        client = PlakarClient("@gdrive")

        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(PlakarError, match="plakar.*introuvable"):
                client.cat("abc123", "/doc.txt")
