#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
echo "Timbral_Instrumental_Homogeneity — PyInstaller build (macOS, maintainer)"
if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "Install: pip install pyinstaller && pip install -e ."
  exit 1
fi
pyinstaller packaging/windows/homogeneity_analyser_win.spec --noconfirm 2>/dev/null || {
  echo "Use packaging/windows/ scripts from Windows, or adapt a macOS .spec locally."
  echo "Upload .app / .dmg via GitHub Releases only."
  exit 1
}
