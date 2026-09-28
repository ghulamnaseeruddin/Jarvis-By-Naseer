# packaging/windows.spec
# Build with:  pyinstaller packaging/windows.spec --noconfirm
# Produces:    dist/JARVIS/  (onedir — the Inno Setup script in packaging/windows/
#              turns this folder into JARVIS-windows-x64-setup.exe)
import sys
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent  # noqa: F821 — SPECPATH is injected by PyInstaller
sys.path.insert(0, str(ROOT / "packaging"))
from common import build_common  # noqa: E402

DATAS, HIDDEN_IMPORTS, EXCLUDES = build_common(ROOT)

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=DATAS,
    hiddenimports=HIDDEN_IMPORTS,
    excludes=EXCLUDES,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="JARVIS",
    icon=str(ROOT / "config" / "jarvis.ico"),
    console=False,          # windowed app — main.py reconfigures stdio safely either way
    disable_windowed_traceback=False,
    contents_directory=".", # keep files next to the .exe (pre-3.13 PyInstaller layout);
                            # main.py / ui.py resolve BASE_DIR from sys.executable's folder
)

COLLECT(
    exe, a.binaries, a.datas,
    strip=False,
    upx=False,              # UPX-packed PyQt6 DLLs are a common false-positive trigger for AV
    name="JARVIS",
)
