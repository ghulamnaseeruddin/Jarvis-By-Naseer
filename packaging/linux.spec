# packaging/linux.spec
# Build with:  pyinstaller packaging/linux.spec --noconfirm
# Produces:    dist/JARVIS/   (packaging/linux/install.sh turns this into a proper install)
import sys
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent  # noqa: F821
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
    name="jarvis-bin",       # install.sh wraps this with a `jarvis` launcher on PATH
    console=False,
    contents_directory=".",
)

COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="JARVIS")
