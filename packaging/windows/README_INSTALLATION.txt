================================================================================
  Homogeneity Analyser — Windows installation (non-technical)
================================================================================

You do NOT need Python. This folder is for distribution files only.

--------------------------------------------------------------------------------
  Option A — Installer (recommended)
--------------------------------------------------------------------------------

1. Double-click:  HomogeneityAnalyserSetup.exe
2. Follow the setup wizard (default installs for your user account).
3. Start "Homogeneity Analyser" from the Start menu (or the desktop shortcut
   if you chose that option).
4. Your web browser should open to the application, or you can open:
      http://127.0.0.1:7860
   If Windows Firewall asks, allow access for this program on private networks.

Exports (CSV, plot images, JSON) are saved under:
   %LOCALAPPDATA%\HomogeneityAnalyser\exports

To uninstall: Settings → Apps → Homogeneity Analyser → Uninstall, or use
"Uninstall Homogeneity Analyser" in the Start menu folder for the app.

--------------------------------------------------------------------------------
  Option B — Portable folder (no installer)
--------------------------------------------------------------------------------

If the "portable" subfolder is present and contains HomogeneityAnalyser.exe:

1. Open the "portable" folder.
2. Double-click HomogeneityAnalyser.exe
3. Open http://127.0.0.1:7860 in your browser if it does not open automatically.

You may copy the whole "portable" folder to a USB drive or another PC (same
Windows 64-bit). Do not mix files from different program versions.

--------------------------------------------------------------------------------
  Supported score files
--------------------------------------------------------------------------------

MusicXML (.xml, .musicxml), compressed MusicXML (.mxl), MIDI (.mid, .midi).

Prefer MusicXML when possible for richer instrument and dynamics information.

After uploading a score, use Symbolic inspection to verify instruments, sounding
pitches, dynamics, techniques, articulations, effects, and vertical sonorities.

--------------------------------------------------------------------------------
  Problems?
--------------------------------------------------------------------------------

- If nothing happens when you run the installer, try right-click → Run anyway
  (SmartScreen may block unsigned programs).
- If the app window closes immediately, run HomogeneityAnalyser.exe from a
  Command Prompt window to see an error message, and contact your distributor
  with that text.

For technical documentation, see the main project README in the developer
package (not required for day-to-day use).

================================================================================
