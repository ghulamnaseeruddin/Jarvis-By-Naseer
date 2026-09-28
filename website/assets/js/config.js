/*
  Site settings — the only file you normally need to edit by hand.
  Or run:  python website/tools/configure.py --help   to fill these in for you.
*/
window.SITE = {
  name: "Mark LIV",
  app: "JARVIS",
  url: "https://example.com",                 // where this site will live (no trailing slash)
  repo: "ghulamnaseeruddin/Jarvis-By-Naseer",             // GitHub "owner/name" that publishes the releases
  version: "1.0.0",                           // shown until the live version loads from GitHub
  email: "ghulamnaseeruddin555@gmail.com",                 // contact address
  owner: "ghulamnaseeruddin",                         // who publishes this build (shown in the footer / terms)
  formEndpoint: "",                           // optional: a Formspree-style URL that accepts JSON POSTs
  // File names the release workflow uploads. Keep in sync with .github/workflows/release.yml
  assets: {
    "windows": { file: "JARVIS-windows-x64-setup.exe", label: "Windows",       note: "Windows 10 / 11 · 64-bit" },
    "mac-arm": { file: "JARVIS-macos-arm64.dmg",       label: "macOS",         note: "Apple silicon (M1 and newer)" },
    "mac-x64": { file: "JARVIS-macos-x64.dmg",         label: "macOS (Intel)", note: "Intel Macs" },
    "linux":   { file: "JARVIS-linux-x64.tar.gz",      label: "Linux",         note: "64-bit · Ubuntu 22.04+ and similar" }
  }
};
