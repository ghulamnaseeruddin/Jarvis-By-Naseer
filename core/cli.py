"""
Command-line helpers that must work in the installed (frozen) app, where there
is no Python on the machine to run `python -m ...` with.

    JARVIS --version          print the version and exit
    JARVIS --selftest         check the install is complete (used by the release
                              workflow to prove every build actually starts)
    JARVIS --install-browser  download the Chromium that Browser Control uses

Called from the very top of main.py, BEFORE the heavy imports, so --version is
instant and --selftest can report exactly which import is missing.

--selftest checks each module — and the actions/plugins discovery step — in
its OWN small subprocess (see --check-import / --check-actions in main.py).
This matters because a build server has no display, no sound card, and no
microphone; a library that pokes at real hardware during import can hard-crash
the whole interpreter (a segfault, not a Python exception), which no
try/except in this process could ever catch. Isolating each check means one
crash is reported as one failed line, instead of silently erasing every
result printed after it.
"""
from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _self_exe_args() -> list[str]:
    """Command to re-launch this same app: the frozen exe itself, or
    `python main.py` when running from source."""
    if getattr(sys, "frozen", False):
        return [sys.executable]
    return [sys.executable, str(_base_dir() / "main.py")]


# (import name, required?) — required ones fail the self-test, optional ones warn.
_MODULES = [
    ("PyQt6.QtWidgets", True), ("PyQt6.QtGui", True), ("numpy", True),
    ("sounddevice", True), ("google.genai", True), ("requests", True),
    ("bs4", True), ("PIL", True), ("psutil", True), ("mss", True),
    ("fastapi", True), ("uvicorn", True), ("cryptography", True),
    ("qrcode", True), ("multipart", True),
    ("google.oauth2.id_token", False), ("playwright.sync_api", False),
    ("cv2", False), ("pyautogui", False), ("pyperclip", False),
    ("ddgs", False), ("pdfplumber", False), ("docx", False), ("pptx", False),
    ("openpyxl", False), ("send2trash", False),
]
_WINDOWS_MODULES = [("comtypes", False), ("pycaw", False), ("pywinauto", False),
                    ("win32api", False)]

_FILES = ["core/prompt.txt", "core/face_model.obj",
          "dashboard/static/app.html", "dashboard/static/login.html",
          "dashboard/static/crypto-js.min.js"]


def _version_line() -> str:
    try:
        from version import __version__, APP_NAME
        return f"{APP_NAME} {__version__}"
    except Exception:
        return "JARVIS (unknown version)"


def _run_check(args: list[str], timeout: int = 40) -> tuple[bool, str]:
    """Run one isolated check subprocess. Returns (ok, message_or_stdout)."""
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"timed out after {timeout}s (likely hung waiting on a real device)"
    except Exception as e:
        return False, f"could not even start the check: {type(e).__name__}: {e}"
    if r.returncode == 0:
        return True, r.stdout.strip()
    if r.returncode < 0:
        import signal
        try:
            sig_name = signal.Signals(-r.returncode).name
        except Exception:
            sig_name = str(-r.returncode)
        return False, f"CRASHED (killed by signal {sig_name}) — not a normal Python error"
    msg = (r.stdout.strip() + " " + r.stderr.strip()).strip()
    return False, (msg or f"exit code {r.returncode}")[:200]


def _selftest() -> int:
    base = _base_dir()
    exe_args = _self_exe_args()
    print(_version_line())
    print(f"python   : {platform.python_version()}  frozen={bool(getattr(sys, 'frozen', False))}")
    print(f"platform : {platform.platform()}")
    print(f"base dir : {base}")
    failures = 0

    print("\nfiles")
    for rel in _FILES:
        ok = (base / rel).is_file()
        print(f"  {'ok  ' if ok else 'MISSING'} {rel}")
        failures += 0 if ok else 1

    print("\nmodules  (each checked in its own process, so one crash can't hide the rest)")
    mods = _MODULES + (_WINDOWS_MODULES if platform.system() == "Windows" else [])
    for name, required in mods:
        ok, detail = _run_check([*exe_args, "--check-import", name])
        if ok:
            print(f"  ok   {name}")
        else:
            tag = "FAIL " if required else "warn "
            print(f"  {tag}{name}  ({detail})")
            failures += 1 if required else 0

    print("\nskills")
    actions_dir = base / "actions"
    py_files = sorted(f.name for f in actions_dir.glob("*.py")) if actions_dir.is_dir() else []
    print(f"  actions folder: {actions_dir}  ({'exists' if actions_dir.is_dir() else 'MISSING'}, "
          f"{len(py_files)} .py file(s) on disk)")
    ok, detail = _run_check([*exe_args, "--check-actions"])
    if ok and detail.strip().isdigit():
        n_actions = int(detail.strip())
        print(f"  {n_actions} built-in actions discovered")
        if n_actions == 0:
            print("  FAIL discovery found the folder but loaded zero actions from it")
            failures += 1
    else:
        print(f"  FAIL action discovery failed ({detail})")
        failures += 1

    print("\nRESULT:", "PASS" if failures == 0 else f"FAIL ({failures} problem(s))")
    return 0 if failures == 0 else 1


def _install_browser() -> int:
    """`playwright install chromium`, using the driver bundled inside the app."""
    try:
        from playwright._impl._driver import compute_driver_executable, get_driver_env
        node, cli = compute_driver_executable()
        print("Downloading Chromium for Browser Control (~150 MB, one time)…")
        return subprocess.run([node, cli, "install", "chromium"],
                              env=get_driver_env()).returncode
    except Exception as e:
        print(f"Could not install the browser: {e}")
        return 1


def run(argv: list[str]) -> int:
    flag = argv[0] if argv else ""
    if flag == "--version":
        print(_version_line())
        return 0
    if flag == "--selftest":
        return _selftest()
    if flag == "--install-browser":
        return _install_browser()
    print(f"Unknown option: {flag}")
    return 2
