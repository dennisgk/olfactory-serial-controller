# build_exe.py
import argparse
import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / "venv"
VENV_PY = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

def run(cmd, **kw):
    print(f"\n>> {' '.join(str(c) for c in cmd)}")
    subprocess.check_call(cmd, **kw)

def ensure_venv_and_reexec():
    want = str(VENV_PY)
    cur = str(Path(sys.executable).resolve())
    if not VENV_PY.exists():
        print(f"Creating virtual env at {VENV_DIR} ...")
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
    def norm(p): return os.path.normcase(os.path.abspath(p)) if os.name == "nt" else os.path.abspath(p)
    if norm(want) != norm(cur):
        print(f"Re-launching under {VENV_PY} ...")
        os.execv(str(VENV_PY), [str(VENV_PY), __file__, *sys.argv[1:]])

def detect_target(user_target: str | None) -> Path:
    if user_target:
        p = (PROJECT_ROOT / user_target).resolve()
        if not p.exists():
            sys.exit(f"ERROR: target script does not exist: {p}")
        return p
    for name in ("main.py", "app.py"):
        p = PROJECT_ROOT / name
        if p.exists():
            return p.resolve()
    candidates = [p for p in PROJECT_ROOT.glob("*.py") if p.name != Path(__file__).name]
    if len(candidates) == 1:
        return candidates[0].resolve()
    if not candidates:
        sys.exit("ERROR: No target found. Pass --target path/to/script.py")
    print("Multiple .py files detected. Pick one with --target:")
    for p in candidates: print("  -", p.name)
    sys.exit(1)

def install_requirements():
    run([sys.executable, "-m", "pip", "install", "-U", "pip", "wheel", "setuptools"])
    req = PROJECT_ROOT / "requirements.txt"
    if req.exists():
        run([sys.executable, "-m", "pip", "install", "-r", str(req)])
    else:
        print("No requirements.txt found; skipping app dependency install.")
    run([sys.executable, "-m", "pip", "install", "-U", "pyinstaller"])

def _add_data_arg(src: Path, dest_rel: str) -> list[str]:
    sep = ";" if os.name == "nt" else ":"
    return ["--add-data", f"{str(src)}{sep}{dest_rel}"]

def _maybe_include_qt_material(cmd: list[str]) -> None:
    # 1) Prefer local folder: ./qt_material
    local_dir = PROJECT_ROOT / "qt_material"
    if local_dir.exists() and local_dir.is_dir():
        print(f"Including local data dir: {local_dir}")
        cmd += _add_data_arg(local_dir, "qt_material")
        return
    # 2) Fallback: installed package data
    try:
        import importlib.util, sys as _sys
        spec = importlib.util.find_spec("qt_material")
        if spec and spec.origin:
            pkg_dir = Path(spec.origin).resolve().parent
            if pkg_dir.exists():
                print(f"Including installed package dir: {pkg_dir}")
                cmd += _add_data_arg(pkg_dir, "qt_material")
    except Exception as e:
        print(f"qt_material not found to include ({e}); continuing without it.")

def build_with_pyinstaller(target: Path, name: str | None, onefile: bool, noconsole: bool, icon: str | None):
    exe_name = name or target.stem
    cmd = [sys.executable, "-m", "PyInstaller", "-y", "--clean"]
    cmd.append("--onefile" if onefile else "--onedir")
    if noconsole and os.name == "nt":
        cmd.append("--noconsole")

    if icon:
        icon_path = (PROJECT_ROOT / icon).resolve()
        if icon_path.exists():
            cmd += ["--icon", str(icon_path)]
        else:
            print(f"WARNING: icon not found at {icon_path}; continuing without icon.")

    # common gotcha: pydantic v2
    try:
        import importlib
        importlib.import_module("pydantic_core._pydantic_core")
        cmd += ["--hidden-import", "pydantic_core._pydantic_core", "--collect-binaries", "pydantic_core"]
    except Exception:
        pass

    _maybe_include_qt_material(cmd)

    cmd += ["--name", exe_name, str(target)]
    run(cmd)

    dist_dir = PROJECT_ROOT / "dist"
    if os.name == "nt":
        out = dist_dir / f"{exe_name}.exe"
        if not out.exists():
            out = dist_dir / exe_name / f"{exe_name}.exe"
    else:
        out = dist_dir / exe_name if onefile else (dist_dir / exe_name / exe_name)

    print("\nBuild complete.")
    print(f"Output: {out}")

def main():
    parser = argparse.ArgumentParser(description="Ensure ./venv, install deps, and build a Windows EXE with PyInstaller.")
    parser.add_argument("--target", help="Entry-point script to package (default: main.py or single .py in folder).")
    parser.add_argument("--name", help="Executable name (default: target stem).")
    parser.add_argument("--onedir", action="store_true", help="Build as folder (default is --onefile).")
    parser.add_argument("--console", action="store_true", help="Keep console window (default: hidden console on Windows).")
    parser.add_argument("--icon", help="Path to .ico file (optional).")
    args = parser.parse_args()

    ensure_venv_and_reexec()
    target = detect_target(args.target)
    install_requirements()
    build_with_pyinstaller(
        target=target,
        name=args.name,
        onefile=not args.onedir,
        noconsole=not args.console,
        icon=args.icon,
    )

if __name__ == "__main__":
    main()
