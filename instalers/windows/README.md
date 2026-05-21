# Windows installers — Orchomogeneity

## End users (recommended)

1. Download a **fresh** ZIP from [GitHub](https://github.com/LuisMRaimundo/Orchomogeneity_Analyser) (**Code -> Download ZIP**).
2. Extract and open **`instalers\windows`**.
3. Double-click **`INSTALL.bat`** or **`START-HERE.bat`**.
4. Wait until the window reports **SUCCESS** or **Done** (first run: **10-25 minutes**).
5. Start the app from **Desktop** or **Start menu -> Orchomogeneity**.

Install location: `%LOCALAPPDATA%\Programs\Orchomogeneity\`  
Log file: `install.log` in that folder.

**No `.exe` is required** for normal install. Do not use `>>>` in batch files (breaks CMD).

## Troubleshooting

| Issue | Action |
|-------|--------|
| No window / closes instantly | Re-download from GitHub; run **`INSTALL.bat`** (not an old Desktop copy). |
| PowerShell parse error | Old files with Unicode characters; download fresh from GitHub. |
| Missing .exe message | Use **`INSTALL.bat`**, not a portable-build script. |

## Already have the full repo cloned?

Use **`Install-and-Run.bat`** — portable Python under `instalers/runtime/` and runs from your copy. Log: `instalers\runtime\windows\install.log`.

## Developers — frozen `.exe`

Run **`Build-All.ps1`** from PowerShell (requires Python + PyInstaller). See `packaging/windows/README.md`. Upload builds via **GitHub Releases** only.
