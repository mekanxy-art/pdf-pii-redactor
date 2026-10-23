import hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import subprocess
import pytest
import start_redactor as launcher


def project(tmp_path):
    root = tmp_path / "Projekt mit Leerzeichen"
    root.mkdir()
    (root / "app.py").write_text("# test", encoding="utf-8")
    (root / "requirements.txt").write_text("streamlit==1.66.1\n", encoding="utf-8")
    return root


def existing_python(root):
    python = launcher.environment_python(root)
    python.parent.mkdir(parents=True)
    python.touch()
    return python


def test_missing_project_has_clear_message(tmp_path):
    with pytest.raises(RuntimeError, match="gesamte ZIP entpacken"):
        launcher.prepare_environment(tmp_path)


def test_first_start_creates_environment_then_installs(tmp_path):
    root = project(tmp_path)
    def run(command, **kwargs):
        if "venv" in command:
            existing_python(root)
        return SimpleNamespace(returncode=0)
    with patch.object(launcher.subprocess, "run", side_effect=run) as runner:
        python = launcher.prepare_environment(root)
    assert python.is_file()
    assert runner.call_args_list[0].args[0][1:3] == ["-m", "venv"]
    assert runner.call_args_list[1].args[0][1:4] == ["-m", "pip", "install"]
    assert (root / ".venv/.redactor-requirements.sha256").is_file()


def test_unchanged_working_environment_does_not_reinstall(tmp_path):
    root = project(tmp_path)
    existing_python(root)
    digest = hashlib.sha256((root / "requirements.txt").read_bytes()).hexdigest()
    (root / ".venv/.redactor-requirements.sha256").write_text(digest)
    with patch.object(launcher.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as runner:
        launcher.prepare_environment(root)
    assert runner.call_count == 1
    assert runner.call_args.args[0][1:3] == ["-c", "import streamlit, spacy, pymupdf"]


def test_failed_install_is_not_marked_ready(tmp_path):
    root = project(tmp_path)
    existing_python(root)
    with patch.object(launcher.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "pip")):
        with pytest.raises(subprocess.CalledProcessError):
            launcher.prepare_environment(root)
    assert not (root / ".venv/.redactor-requirements.sha256").exists()
