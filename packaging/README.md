# Packaging & release guide

This folder turns the Python project into three real installers — a Windows
`.exe`, two macOS `.dmg` files (Apple silicon + Intel), and a Linux `.tar.gz`
— and a GitHub Actions workflow that builds all of them automatically.

## The easy way: let GitHub build it

1. Push this project to a GitHub repository.
2. Point the site and the app at your repo (one command, from the project root):
   ```bash
   python website/tools/configure.py --repo YOUR-USERNAME/Mark-LIV \
       --url https://your-domain.com --email you@example.com --owner "Your Name"
   ```
   Then open `version.py` and set `GITHUB_REPO` to the same `"owner/name"`.
3. Tag a release and push the tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
4. `.github/workflows/release.yml` builds all three platforms, runs
   `--selftest` on each one to make sure it actually starts, and publishes
   them — with a `SHA256SUMS.txt` — as a GitHub Release attached to that tag.
5. The website's download buttons and its "update available" notice read
   that release automatically. Nothing else to configure.

A build usually takes 10–15 minutes. `workflow_dispatch` (the "Run workflow"
button in the Actions tab) lets you trigger a test build without tagging —
it builds and uploads artifacts but does not publish a release (only a
`v*.*.*` tag does that).

## Building locally, one platform at a time

You need to be on the target OS — PyInstaller does not cross-compile.

```bash
pip install -r requirements.txt pyinstaller

# Windows (run on Windows):
pyinstaller packaging/windows.spec --noconfirm
dist\JARVIS\JARVIS.exe --selftest        # confirms the build is complete
# then, with Inno Setup 6 installed:
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\windows\installer.iss

# macOS (run on macOS):
iconutil -c icns packaging/macos/icon.iconset -o packaging/macos/icon.icns
pyinstaller packaging/macos.spec --noconfirm
./dist/JARVIS.app/Contents/MacOS/JARVIS --selftest
./packaging/macos/build_dmg.sh dist/JARVIS.app dist/JARVIS-macos-arm64.dmg JARVIS

# Linux (run on Linux):
pyinstaller packaging/linux.spec --noconfirm
dist/JARVIS/jarvis-bin --selftest
mkdir -p pkg/JARVIS-linux-x64 && cp -R dist/JARVIS pkg/JARVIS-linux-x64/JARVIS
cp packaging/linux/install.sh pkg/JARVIS-linux-x64/
tar -czf dist/JARVIS-linux-x64.tar.gz -C pkg JARVIS-linux-x64
```

## How the pieces fit together

| File | Purpose |
|---|---|
| `packaging/common.py` | Shared list of data files and hidden imports every spec needs (plugins, actions, dashboard static files) |
| `packaging/windows.spec` / `macos.spec` / `linux.spec` | PyInstaller specs — one per OS |
| `packaging/windows/installer.iss` | Inno Setup script: turns the Windows build into a proper installer with Start Menu shortcuts |
| `packaging/macos/icon.iconset` + `build_dmg.sh` | macOS icon source and the script that wraps `JARVIS.app` into a `.dmg` |
| `packaging/linux/install.sh` | Per-user installer the end user runs after extracting the `.tar.gz` |
| `.github/workflows/release.yml` | Builds and publishes all of the above whenever you push a `v*.*.*` tag |
| `.github/workflows/pages.yml` | Optional: auto-publishes the `/website` folder to GitHub Pages |
| `version.py` | Single source of truth for the version number and the repo the app checks for updates |
| `core/cli.py` | `--version`, `--selftest`, `--install-browser` — works inside the frozen build, not just from source |

## Why some things are the way they are

- **Not code-signed.** Windows and Apple developer certificates cost money
  every year; this stays free by not signing. Windows shows a SmartScreen
  warning and macOS shows a "developer cannot be verified" warning — both
  covered in the docs page, with the checksum as a way to verify the file
  is genuinely what was published.
- **`contents_directory="."`** in the specs keeps every file next to the
  executable, matching what `main.py` / `ui.py` / `dashboard/server.py`
  already assume (`Path(sys.executable).parent`) — the newer PyInstaller
  default of a hidden `_internal` folder would break that.
- **`--selftest` runs in CI, not just locally.** It imports every required
  package and confirms the bundled `plugins/`, `actions/`, `core/prompt.txt`
  and `core/face_model.obj` are actually present in the built folder — the
  most common way a "successful" PyInstaller build turns out to be missing
  something at runtime.
- **The wake word (`openwakeword`) is not bundled.** It's optional, a few
  extra megabytes, and only ever needed by people running from source who
  click the one-click install in the settings drawer — see `core/wake_word.py`.
