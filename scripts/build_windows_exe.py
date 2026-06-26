from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


FORBIDDEN_DIST_PARTS = {
    ".env",
    ".env.local",
    ".env.paddleocr.local.md",
    "markdown_output",
    "latex_output",
    "log",
    "input_docs",
    "tests",
    "test-PaddleOCR",
    "test-mineru",
}

DEFAULT_EXCLUDED_MODULES = [
    "IPython",
    "jedi",
    "jupyter_client",
    "jupyter_core",
    "nbformat",
    "notebook",
    "pluggy",
    "prompt_toolkit",
    "py",
    "pytest",
    "tornado",
    "zmq",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the DocPage2MD Windows GUI one-dir executable with PyInstaller.")
    parser.add_argument("--name", default="DocPage2MD", help="Executable/app directory name.")
    parser.add_argument("--entry", default="docpage2md_gui.py", help="GUI entry script.")
    parser.add_argument(
        "--distpath",
        default=None,
        help="PyInstaller dist output directory. Defaults to dist, or a timestamped dist subdirectory if the default app dir already exists.",
    )
    parser.add_argument("--workpath", default=None, help="PyInstaller work directory. Defaults to a temp directory.")
    parser.add_argument("--specpath", default=None, help="PyInstaller spec output directory. Defaults to a temp directory.")
    parser.add_argument("--replace-existing", action="store_true", help="Use the default dist directory even if an existing app dir must be replaced.")
    parser.add_argument("--console", action="store_true", help="Build with a console window for debugging.")
    parser.add_argument("--no-clean", action="store_true", help="Do not pass --clean to PyInstaller.")
    parser.add_argument("--dry-run", action="store_true", help="Print the PyInstaller command without running it.")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip post-build CLI version smoke test.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parent.parent
    distpath = _select_distpath(args, repo_root)
    command = build_command(args, repo_root, distpath=distpath)
    if args.dry_run:
        print(" ".join(_quote(part) for part in command))
        return 0

    if importlib.util.find_spec("PyInstaller") is None:
        print("PyInstaller is not installed. Run: python -m pip install -r requirements-dev.txt", file=sys.stderr)
        return 2

    completed = subprocess.run(command, cwd=repo_root, check=False)
    if completed.returncode != 0:
        return completed.returncode

    app_dir = distpath / args.name
    exe_path = app_dir / f"{args.name}.exe"
    if not exe_path.exists():
        print(f"Expected executable not found: {exe_path}", file=sys.stderr)
        return 1

    violations = scan_for_forbidden_files(app_dir)
    if violations:
        print("Refusing release artifact; forbidden local/private files were bundled:", file=sys.stderr)
        for path in violations[:50]:
            print(f"  - {path}", file=sys.stderr)
        return 1

    if not args.skip_smoke:
        smoke = subprocess.run(
            [str(exe_path), "--docpage2md-cli", "--version"],
            cwd=repo_root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        if smoke.returncode != 0:
            print(smoke.stdout, file=sys.stderr)
            return smoke.returncode
        if smoke.stdout.strip():
            print(smoke.stdout.strip())

    print(f"Built: {exe_path}")
    return 0


def build_command(args: argparse.Namespace, repo_root: Path, distpath: Path | None = None) -> list[str]:
    tokenizer_dir = repo_root / "docpage2md_app" / "deepseek_v3_tokenizer"
    entry = repo_root / args.entry
    build_root = Path(tempfile.gettempdir()) / "docpage2md_pyinstaller"
    distpath = distpath or _select_distpath(args, repo_root)
    workpath = _resolve_output_path(args.workpath, build_root / "work", repo_root)
    specpath = _resolve_output_path(args.specpath, build_root / "spec", repo_root)
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--name",
        args.name,
        "--onedir",
        "--distpath",
        str(distpath),
        "--workpath",
        str(workpath),
        "--specpath",
        str(specpath),
        "--add-data",
        f"{tokenizer_dir}{os.pathsep}docpage2md_app/deepseek_v3_tokenizer",
    ]
    for module in DEFAULT_EXCLUDED_MODULES:
        command.extend(["--exclude-module", module])
    if not args.no_clean:
        command.append("--clean")
    command.append("--console" if args.console else "--windowed")
    command.append(str(entry))
    return command


def _select_distpath(args: argparse.Namespace, repo_root: Path) -> Path:
    if args.distpath is not None:
        return _resolve_output_path(args.distpath, repo_root, repo_root)
    default = repo_root / "dist"
    default_app_dir = default / args.name
    if args.replace_existing or not default_app_dir.exists():
        return default
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return repo_root / "dist" / f"{args.name}_{stamp}"


def _resolve_output_path(value: str | None, default: Path, base: Path) -> Path:
    if value is None:
        return default
    path = Path(value)
    if path.is_absolute():
        return path
    return base / path


def scan_for_forbidden_files(app_dir: Path) -> list[Path]:
    violations: list[Path] = []
    for path in app_dir.rglob("*"):
        rel_parts = set(path.relative_to(app_dir).parts)
        lower_parts = {part.lower() for part in rel_parts}
        if lower_parts & {part.lower() for part in FORBIDDEN_DIST_PARTS}:
            violations.append(path)
            continue
        if path.name.lower().startswith(".env"):
            violations.append(path)
            continue
        if path.suffix.lower() in {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"} and "tests" in lower_parts:
            violations.append(path)
    return violations


def _quote(value: str) -> str:
    if not value or any(char.isspace() for char in value):
        return '"' + value.replace('"', '\\"') + '"'
    return value


if __name__ == "__main__":
    raise SystemExit(main())
