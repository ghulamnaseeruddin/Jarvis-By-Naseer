# packaging/common.py
"""
Shared bits for the three PyInstaller spec files (windows.spec, macos.spec,
linux.spec). Each spec calls build_common(ROOT) with the project root — kept
as an explicit argument (rather than reading PyInstaller's SPECPATH internally)
so this file behaves the same whether PyInstaller imports or execs it.
"""
from pathlib import Path


def _files_under(folder: Path, dest_prefix: str):
    """
    One (source_file, dest_folder) tuple per file, recursively — rather than
    handing PyInstaller's Analysis(datas=...) a bare directory. A directory
    entry there is not reliably recursed on every PyInstaller version and
    platform; enumerating files ourselves is the documented-safe way and is
    what actually caught a real bug (an empty actions/ folder in two of the
    three built apps) that a directory entry had silently swallowed.
    """
    out = []
    for f in sorted(folder.rglob("*")):
        if f.is_file():
            rel_dir = f.parent.relative_to(folder)
            dest = dest_prefix if str(rel_dir) == "." else str(Path(dest_prefix) / rel_dir)
            out.append((str(f), dest))
    return out


def build_common(root: Path):
    root = Path(root)

    # Files the app reads at runtime with a literal relative path (see BASE_DIR
    # in main.py / ui.py / dashboard/server.py) — every one of these must land
    # next to the executable, not just be importable.
    datas = [
        (str(root / "core" / "prompt.txt"),      "core"),
        (str(root / "core" / "face_model.obj"),  "core"),
        *_files_under(root / "dashboard" / "static", "dashboard/static"),
        *_files_under(root / "actions",             "actions"),
        *_files_under(root / "plugins",             "plugins"),
    ]

    # Loaded only via importlib.util.spec_from_file_location at runtime
    # (core/action_loader.py, core/plugin_loader.py) — PyInstaller's static
    # analysis can't see these, so without this list the frozen build would
    # silently lose every built-in skill.
    hidden_actions = sorted(
        "actions." + p.stem for p in (root / "actions").glob("*.py") if not p.stem.startswith("_")
    )
    hidden_plugins = sorted(
        "plugins." + p.stem for p in (root / "plugins").glob("*.py") if not p.stem.startswith("_")
    )

    hidden_imports = [
        *hidden_actions, *hidden_plugins,
        "google.genai", "google.oauth2.id_token", "google.auth.transport.requests",
        # Imported lazily inside functions (browser control, file reading, etc.),
        # which PyInstaller's static scan cannot see — without these the built app
        # is missing those skills even though the packages are installed.
        "playwright", "playwright.sync_api", "openpyxl", "pyautogui", "pyperclip",
        "ddgs", "pdfplumber", "docx", "pptx", "send2trash", "cv2",
        "uvicorn.logging", "uvicorn.loops.auto", "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto", "uvicorn.lifespan.on",
    ]

    excludes = ["tkinter", "matplotlib", "pytest", "IPython", "notebook"]

    return datas, hidden_imports, excludes
