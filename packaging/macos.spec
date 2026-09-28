# packaging/macos.spec
# Build with:  pyinstaller packaging/macos.spec --noconfirm
# Produces:    dist/JARVIS.app  (the release workflow wraps this in a .dmg)
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
    name="JARVIS",
    console=False,
    contents_directory=".",
)

coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="JARVIS")

icns = ROOT / "packaging" / "macos" / "icon.icns"
app = BUNDLE(
    coll,
    name="JARVIS.app",
    icon=str(icns) if icns.exists() else None,
    bundle_identifier="com.markliv.jarvis",
    info_plist={
        "CFBundleName": "JARVIS",
        "CFBundleDisplayName": "JARVIS",
        "CFBundleShortVersionString": "1.0.0",   # release workflow overwrites this from the git tag
        "CFBundleVersion": "1.0.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "11.0",
        # First-launch permission prompts — macOS refuses to even show the
        # system dialog without a reason string, so these are required, not
        # optional, for the mic / screen / control features to work at all.
        "NSMicrophoneUsageDescription": "JARVIS needs the microphone to hear your voice commands.",
        "NSCameraUsageDescription": "JARVIS can look at the camera when you ask it to, for visual questions.",
        "NSAppleEventsUsageDescription": "JARVIS uses this to control other applications when you ask it to (opening apps, browser control).",
        "NSSystemAdministrationUsageDescription": "JARVIS uses this for system settings actions like volume and brightness.",
    },
)
