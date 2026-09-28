#!/usr/bin/env bash
# packaging/linux/install.sh — run from inside the extracted JARVIS-linux-x64
# folder. Installs for the current user only; no root required.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${JARVIS_INSTALL_DIR:-$HOME/.local/share/jarvis}"
BIN_DIR="$HOME/.local/bin"
DESK_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

echo "Installing JARVIS to $DEST ..."
mkdir -p "$DEST" "$BIN_DIR" "$DESK_DIR" "$ICON_DIR"
cp -R "$HERE"/JARVIS/. "$DEST/"
chmod +x "$DEST/jarvis-bin"

cat > "$BIN_DIR/jarvis" <<LAUNCH
#!/usr/bin/env bash
exec "$DEST/jarvis-bin" "\$@"
LAUNCH
chmod +x "$BIN_DIR/jarvis"

if [ -f "$HERE/icon.png" ]; then
  cp "$HERE/icon.png" "$ICON_DIR/jarvis.png"
fi

cat > "$DESK_DIR/jarvis.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=JARVIS
Comment=Real-time voice AI assistant
Exec=$DEST/jarvis-bin
Icon=jarvis
Categories=Utility;
Terminal=false
DESKTOP

cat > "$DEST/uninstall.sh" <<UNINSTALL
#!/usr/bin/env bash
set -euo pipefail
echo "This removes the JARVIS program files."
read -p "Also delete config and memory (your API key, accounts, and what it remembers)? [y/N] " ans
rm -f "$BIN_DIR/jarvis" "$DESK_DIR/jarvis.desktop" "$ICON_DIR/jarvis.png"
if [[ "\$ans" =~ ^[Yy]$ ]]; then
  rm -rf "$DEST"
else
  find "$DEST" -mindepth 1 -maxdepth 1 ! -name config ! -name memory -exec rm -rf {} +
fi
echo "Done."
UNINSTALL
chmod +x "$DEST/uninstall.sh"

echo
echo "Installed. Missing system libraries? Run:"
echo "  sudo apt install libportaudio2 libxcb-cursor0 libxkbcommon-x11-0"
echo
echo "Launch with: jarvis   (or find JARVIS in your applications menu — you may need to log out and back in once)"
echo "Uninstall with: $DEST/uninstall.sh"
