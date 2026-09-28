#!/usr/bin/env bash
# packaging/macos/build_dmg.sh <path-to-JARVIS.app> <output.dmg> <Volume Name>
# Wraps a built JARVIS.app into a distributable .dmg with a symlink to
# /Applications, so opening the image and dragging is enough to install.
set -euo pipefail
APP="${1:?Usage: build_dmg.sh <JARVIS.app> <output.dmg> <volume name>}"
OUT="${2:?output .dmg path required}"
VOL="${3:-JARVIS}"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"

# A tiny AppleScript-driven window layout is the usual next step for polish
# (background image, icon positions); left plain here to keep the build
# script dependency-free and reliable in CI.
hdiutil create -volname "$VOL" -srcfolder "$STAGE" -ov -format UDZO "$OUT"
echo "Wrote $OUT"
