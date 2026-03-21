from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import scripts.validate_canonical as validate_script


class _ParserStub:
    def __init__(self, args: argparse.Namespace) -> None:
        self._args = args

    def parse_args(self) -> argparse.Namespace:
        return self._args


def _mock_assembly() -> SimpleNamespace:
    validation_reports = SimpleNamespace(
        passed=True,
        passed_count=1,
        rule_count=1,
        scopes={},
        summary_by_scope=lambda: {},
    )
    metadata = SimpleNamespace(project_id="demo")
    generated_artifacts = SimpleNamespace(canonical_json="projects/demo/generated/canonical.json")
    return SimpleNamespace(
        validation_reports=validation_reports,
        metadata=metadata,
        generated_artifacts=generated_artifacts,
    )


def test_validate_check_changes_bootstrap_skip_when_no_project_files(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    (tmp_path / "projects").mkdir(parents=True, exist_ok=True)

    args = argparse.Namespace(
        project_file="projects/bootstrap/project.toml",
        check_changes=True,
        json=False,
    )
    monkeypatch.setattr(validate_script, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(validate_script, "_build_parser", lambda: _ParserStub(args))

    called = {"value": False}

    def _unexpected_materialize(_: str) -> SimpleNamespace:
        called["value"] = True
        raise AssertionError("materialize_project_runtime should not run in bootstrap skip mode")

    monkeypatch.setattr(validate_script, "materialize_project_runtime", _unexpected_materialize)

    exit_code = validate_script.main()
    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert not called["value"]
    assert "bootstrap_mode=True" in stdout


def test_validate_check_changes_bootstrap_skip_json_output(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    (tmp_path / "projects").mkdir(parents=True, exist_ok=True)

    args = argparse.Namespace(
        project_file="projects/bootstrap/project.toml",
        check_changes=True,
        json=True,
    )
    monkeypatch.setattr(validate_script, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(validate_script, "_build_parser", lambda: _ParserStub(args))
    monkeypatch.setattr(
        validate_script,
        "materialize_project_runtime",
        lambda _: (_ for _ in ()).throw(AssertionError("unexpected materialize call")),
    )

    exit_code = validate_script.main()
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["passed"] is True
    assert payload["bootstrap_mode"] is True
    assert "no projects/*/project.toml found" in payload["message"]


def test_validate_uses_materialize_when_project_file_exists(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_dir = tmp_path / "projects" / "demo"
    project_dir.mkdir(parents=True, exist_ok=True)
    project_file = project_dir / "project.toml"
    project_file.write_text("[framework]\nmodules = []\n", encoding="utf-8")

    args = argparse.Namespace(
        project_file="projects/demo/project.toml",
        check_changes=True,
        json=False,
    )
    monkeypatch.setattr(validate_script, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(validate_script, "_build_parser", lambda: _ParserStub(args))

    called = {"project_file": ""}

    def _materialize(project_file_arg: str) -> SimpleNamespace:
        called["project_file"] = project_file_arg
        return _mock_assembly()

    monkeypatch.setattr(validate_script, "materialize_project_runtime", _materialize)

    exit_code = validate_script.main()
    assert exit_code == 0
    assert called["project_file"] == "projects/demo/project.toml"
