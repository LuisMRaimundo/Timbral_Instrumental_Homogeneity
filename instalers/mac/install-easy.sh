#!/usr/bin/env bash
# One-click setup for macOS (non-expert). Repo: https://github.com/LuisMRaimundo/Orchomogeneity_Analyser
set -euo pipefail

INSTALL_ROOT="${HOME}/Applications/Orchomogeneity"
APP_DIR="${INSTALL_ROOT}/app"
VENV_DIR="${INSTALL_ROOT}/venv"
GITHUB_ZIP="https://github.com/LuisMRaimundo/orchomogeneity/archive/refs/heads/main.zip"
ZIP_FOLDER="orchomogeneity-main"

echo "=== Orchomogeneity — Installer (macOS) ==="

find_python() {
  for c in python3.11 python3.10 python3; do
    if command -v "$c" >/dev/null 2>&1; then
      ver="$("$c" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo 0)"
      if [[ "$ver" -ge 10 && "$ver" -le 11 ]]; then
        command -v "$c"
        return 0
      fi
    fi
  done
  return 1
}

PYTHON="$(find_python || true)"
if [[ -z "${PYTHON}" ]]; then
  echo "Installing Python 3.11 via Homebrew (if available)…"
  if command -v brew >/dev/null 2>&1; then
    brew install python@3.11
    PYTHON="$(brew --prefix python@3.11)/bin/python3.11"
  else
    echo "Install Python 3.11 from https://www.python.org/downloads/ then run this script again."
    exit 1
  fi
fi

mkdir -p "${INSTALL_ROOT}"
if [[ ! -f "${APP_DIR}/pyproject.toml" ]]; then
  echo "Downloading from GitHub…"
  tmp="$(mktemp -d)"
  curl -fsSL "${GITHUB_ZIP}" -o "${tmp}/repo.zip"
  unzip -q "${tmp}/repo.zip" -d "${tmp}"
  rm -rf "${APP_DIR}"
  mv "${tmp}/${ZIP_FOLDER}" "${APP_DIR}"
  rm -rf "${tmp}"
fi

echo "Installing Python packages (10–25 min first time)…"
"${PYTHON}" -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/pip" install --upgrade pip wheel
"${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements-install.txt"

LAUNCHER="${INSTALL_ROOT}/Launch-Orchomogeneity.command"
cat > "${LAUNCHER}" <<EOF
#!/usr/bin/env bash
cd "${APP_DIR}"
exec "${VENV_DIR}/bin/homogeneity-analyser"
EOF
chmod +x "${LAUNCHER}"

DESKTOP="${HOME}/Desktop/Orchomogeneity.command"
cp "${LAUNCHER}" "${DESKTOP}"
chmod +x "${DESKTOP}"

echo "Done. Open: ${LAUNCHER}"
echo "Or: Desktop → Orchomogeneity.command"
