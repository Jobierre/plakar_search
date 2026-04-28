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
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = client._run("ls")
            mock_run.assert_called_once_with(
                ["plakar", "at", "@gdrive", "ls"],
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
        stdout = (
            "2024-01-01T12:00:00Z   abc12345   10 KiB        2s /home/user/docs\n"
            "2024-01-02T13:00:00Z   def67890   20 MiB        5s /home/user/images\n"
        )
        mock_result = MagicMock()
        mock_result.stdout = stdout

        with patch.object(client, "_run", return_value=mock_result) as mock_run:
            result = client.list_snapshots()
            mock_run.assert_called_once_with("ls")
            assert len(result) == 2
            assert result[0]["id"] == "abc12345"
            assert result[0]["date"] == "2024-01-01T12:00:00Z"
            assert result[0]["root_path"] == "/home/user/docs"
            assert result[1]["id"] == "def67890"

    def test_list_snapshots_empty(self):
        client = PlakarClient("@gdrive")
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch.object(client, "_run", return_value=mock_result):
            result = client.list_snapshots()
            assert result == []

    def test_list_snapshots_skips_malformed(self):
        client = PlakarClient("@gdrive")
        stdout = "garbage line\n2024-01-01T12:00:00Z   abc12345   10 KiB        2s /path"
        mock_result = MagicMock()
        mock_result.stdout = stdout

        with patch.object(client, "_run", return_value=mock_result):
            result = client.list_snapshots()
            assert len(result) == 1


class TestPlakarClientListFiles:
    def test_list_files(self):
        client = PlakarClient("@gdrive")
        stdout = (
            "2024-01-01T12:00:00Z -rw-r--r-- alice staff 1.0 KiB /home/user/doc.txt\n"
            "2024-01-01T12:00:00Z -rw-r--r-- alice staff 2.5 MiB /home/user/img.jpg\n"
        )
        mock_result = MagicMock()
        mock_result.stdout = stdout

        with patch.object(client, "_run", return_value=mock_result) as mock_run:
            result = client.list_files("abc12345")
            mock_run.assert_called_once_with("ls", "-recursive", "abc12345")
            assert len(result) == 2
            assert result[0]["path"] == "/home/user/doc.txt"
            assert result[0]["perms"] == "-rw-r--r--"
            assert result[0]["size"] == "1.0 KiB"
            assert result[1]["path"] == "/home/user/img.jpg"

    def test_list_files_empty(self):
        client = PlakarClient("@gdrive")
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch.object(client, "_run", return_value=mock_result):
            result = client.list_files("abc12345")
            assert result == []


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
