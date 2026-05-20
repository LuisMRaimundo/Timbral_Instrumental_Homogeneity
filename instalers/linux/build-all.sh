#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
echo "Orchomogeneity — PyInstaller build (Linux, maintainer)"
if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "Install: pip install pyinstaller && pip install -e ."
  exit 1
fi
echo "Adapt packaging/windows/homogeneity_analyser_win.spec for Linux or use packaging/windows/ on Windows."
echo "Upload .tar.gz via GitHub Releases only."
exit 0
