# Windows packaging (non-technical distribution)

This folder contains **draft** assets for a **one-click Windows installer** for users **without Python**. The scientific package code under `src/` is unchanged; only packaging helpers live here.

| File | Purpose |
|------|---------|
| `launcher.py` | **Dev launcher** (Python on PATH): binds **127.0.0.1** only, first free port from **7860**, `inbrowser=True`. Run: `python packaging/windows/launcher.py` with `PYTHONPATH=src` (see file docstring). |
| `frozen_launcher.py` | PyInstaller entry: cache dir, **`127.0.0.1`** bind, **7860** if free else next free port, then `build_demo().launch(...)` (same **H_TI** + **Symbolic inspection** UI as `python -m homogeneity_analyser`). |
| `homogeneity_analyser_win.spec` | PyInstaller **onedir** spec (`HomogeneityAnalyser.exe` + `HomogeneityAnalyser` folder). |
| `build_windows.ps1` | **PyInstaller only** (no Inno): calls `build_pyinstaller.ps1 -Run` (optional `-Clean`). |
| `build_pyinstaller.ps1` | Invokes PyInstaller from the **repository root** (use `-Run`; default is checks only). |
| `build_inno.ps1` | Runs **Inno Setup 6** `ISCC.exe` against `HomogeneityAnalyser.iss` (use `-Run`). |
| `HomogeneityAnalyser.iss` | **Draft** installer script — edit version, publisher, license, and `[Run]` before release. |
| `smoke_test_frozen.ps1` | Starts the frozen exe (working directory = exe folder), expects **HTTP 200** and H_TI markers in the HTML shell. |
| `StartHomogeneityAnalyser.cmd` | Optional double-click helper; copy next to `HomogeneityAnalyser.exe` in the onedir output. |

---

## Maintainer prerequisites (build machine)

1. **Windows 10/11 x64**, **Python 3.10+** (build-only; end users do not need Python).
2. **Git** (optional) and a clean clone of this repository.
3. Python venv with the project + tooling:

   ```powershell
   cd <repo-root>
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -U pip
   pip install -e ".[dev]"
   pip install pyinstaller
   ```

4. **Inno Setup 6** (only when compiling the installer):  
   https://jrsoftware.org/isinfo.php  

---

## Build the frozen application (PyInstaller)

From the **repository root**:

```powershell
.\packaging\windows\build_windows.ps1              # PyInstaller onedir only (same as build_pyinstaller.ps1 -Run)
.\packaging\windows\build_windows.ps1 -Clean     # wipe dist\HomogeneityAnalyser + build\pyinstaller first

.\packaging\windows\build_pyinstaller.ps1          # dry run: checks paths
.\packaging\windows\build_pyinstaller.ps1 -Run     # build
.\packaging\windows\build_pyinstaller.ps1 -Clean -Run   # clean + build
```

If PyInstaller errors on **`enum34`**, remove it from the build Python: `python -m pip uninstall enum34 -y` (it shadows the stdlib `enum` on Python 3).

**Outputs:**

- **Build cache / intermediate (gitignored):** `dist\HomogeneityAnalyser\` — PyInstaller `COLLECT` onedir (used as input to Inno).
- **Distribution drop (ship to end users):** `Homogeneity_analiser_install\` at the repository root:
  - After **`build_pyinstaller.ps1 -Run`:** `Homogeneity_analiser_install\portable\` is refreshed (mirror of the onedir app + short `README_PORTABLE.txt`). No `__pycache__`, tests, or sources are copied there.
  - After **`build_inno.ps1 -Run`:** `Homogeneity_analiser_install\HomogeneityAnalyserSetup.exe` (installer).
  - **`Homogeneity_analiser_install\README_INSTALLATION.txt`** — non-technical instructions (tracked in git; edit there for distributors).

### First-build troubleshooting

- **Missing module** (`ImportError`): add the module to `hiddenimports` in `homogeneity_analyser_win.spec`, or use a PyInstaller hook.
- **Missing data** (JSON/YAML, music21 resources): extend `datas` in the spec, e.g. `collect_data_files("music21", ...)` — music21 can be **large**; add only what runtime tests require.
- **Gradio / Uvicorn / FastAPI**: the spec lists common hidden imports; extend as needed after `pyinstaller` warnings. The spec uses **`module_collection_mode` `py` for `gradio` and `gradio_client`** so runtime can read package `.py` sources, plus **`collect_data_files`** for Gradio JSON assets and small deps (`safehttpx`, `groovy`).
- **Numba / TBB**: PyInstaller may warn about missing `tbb12.dll`; install Intel TBB for Windows or ignore if you do not use numba-heavy code paths.
- **Kaleido / Plotly static export**: if PNG export fails in the frozen app, verify Kaleido binaries are collected (may need `binaries` or additional hooks per Kaleido docs).

---

## Smoke test (frozen exe)

After a successful onedir build:

```powershell
.\packaging\windows\smoke_test_frozen.ps1
```

Optional: `-ExePath "D:\path\to\HomogeneityAnalyser.exe"` and `-Port 7860`.

The script launches the exe, polls `http://127.0.0.1:<port>/`, then **terminates** the process. Adjust `TimeoutSeconds` if cold start is slow on low-end machines.

---

## Build the installer (Inno Setup)

1. Ensure `dist\HomogeneityAnalyser\` exists (PyInstaller step).
2. Edit `HomogeneityAnalyser.iss`: `AppVersion`, `AppPublisher`, `AppId` (generate a **unique** GUID for your product line), license text / `LicenseFile` if required.
3. Compile:

   ```powershell
   .\packaging\windows\build_inno.ps1 -Run
   ```

**Output:** `Homogeneity_analiser_install\HomogeneityAnalyserSetup.exe` (same folder as the user-facing README; not under `dist\`).

---

## End-user experience (target)

1. Run the installer (per-user install uses `PrivilegesRequired=lowest` in the draft `.iss`).
2. Start **Homogeneity Analyser** from the Start Menu shortcut (or run `HomogeneityAnalyser.exe` in the install folder).
3. A **console window** stays open while the server runs (PyInstaller `console=True` in the spec — switch to `console=False` + `debug=False` only after verifying no silent failures).
4. Open the URL printed by Gradio (default **http://127.0.0.1:7860**). Allow through **Windows Firewall** if prompted for local network (loopback usually unaffected).

Exports (CSV/PNG/JSON) go to `%LOCALAPPDATA%\HomogeneityAnalyser\exports` unless the user sets `HOMOGENEITY_CACHE_DIR`.

---

## Code signing & release hygiene (not automated here)

- Sign `HomogeneityAnalyser.exe` and the installer with an **Authenticode** certificate to reduce SmartScreen warnings.
- Run **smoke_test_frozen.ps1** on a **clean VM** without Python before publishing.
- Keep installer **version** in sync with `pyproject.toml` `[project] version`.

---

## What is intentionally *not* done here

- No CI job is wired yet.
- No **one-file** (`--onefile`) spec — onedir is easier to debug for Gradio/music21.
- No automatic **music21** corpus bundling — add explicitly if parse errors appear for specific scores.

For current product behaviour and metrics, see the repository **`README.md`** and **`TECHNICAL_MANUAL.md`**.
