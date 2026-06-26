from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path


def _load_build_module():
    path = Path(__file__).resolve().parent.parent / "scripts" / "build_windows_exe.py"
    spec = importlib.util.spec_from_file_location("build_windows_exe", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_windows_exe_dry_run_command_includes_gui_entry_and_tokenizer(tmp_path):
    module = _load_build_module()
    args = module.parse_args(["--dry-run", "--distpath", str(tmp_path / "dist")])

    command = module.build_command(args, Path(__file__).resolve().parent.parent)

    assert command[:3] == [command[0], "-m", "PyInstaller"]
    assert "--onedir" in command
    assert "--windowed" in command
    assert "docpage2md_gui.py" in command[-1]
    add_data_index = command.index("--add-data") + 1
    assert "deepseek_v3_tokenizer" in command[add_data_index]
    assert "--exclude-module" in command
    assert "pytest" in command
    assert "IPython" in command


def test_build_windows_exe_defaults_keep_pyinstaller_cache_outside_repo():
    module = _load_build_module()
    repo_root = Path(__file__).resolve().parent.parent
    args = module.parse_args(["--dry-run"])

    command = module.build_command(args, repo_root)

    workpath = Path(command[command.index("--workpath") + 1])
    specpath = Path(command[command.index("--specpath") + 1])
    expected_root = Path(tempfile.gettempdir()) / "docpage2md_pyinstaller"
    assert expected_root in workpath.parents
    assert expected_root in specpath.parents


def test_build_windows_exe_uses_timestamped_dist_when_default_exists(monkeypatch, tmp_path):
    module = _load_build_module()
    repo_root = tmp_path
    (repo_root / "dist" / "DocPage2MD").mkdir(parents=True)

    class FixedDateTime:
        @classmethod
        def now(cls):
            class FixedNow:
                def strftime(self, _fmt):
                    return "20260626_190000"

            return FixedNow()

    monkeypatch.setattr(module, "datetime", FixedDateTime)
    args = module.parse_args([])

    command = module.build_command(args, repo_root)

    distpath = Path(command[command.index("--distpath") + 1])
    assert distpath == repo_root / "dist" / "DocPage2MD_20260626_190000"


def test_build_windows_exe_scan_rejects_private_outputs(tmp_path):
    module = _load_build_module()
    app = tmp_path / "DocPage2MD"
    (app / "markdown_output").mkdir(parents=True)
    (app / ".env").write_text("SECRET=1", encoding="utf-8")
    (app / "docpage2md_app").mkdir()
    (app / "docpage2md_app" / "ok.py").write_text("pass", encoding="utf-8")

    violations = module.scan_for_forbidden_files(app)

    assert app / ".env" in violations
    assert app / "markdown_output" in violations
    assert app / "docpage2md_app" / "ok.py" not in violations


def test_build_windows_exe_copies_release_readme(tmp_path):
    module = _load_build_module()
    repo_root = tmp_path
    app = tmp_path / "dist" / "DocPage2MD"
    readme = repo_root / "docs" / "release" / "使用说明.md"
    readme.parent.mkdir(parents=True)
    app.mkdir(parents=True)
    readme.write_text("使用说明", encoding="utf-8")

    module.copy_release_docs(repo_root, app)

    assert (app / "使用说明.md").read_text(encoding="utf-8") == "使用说明"
