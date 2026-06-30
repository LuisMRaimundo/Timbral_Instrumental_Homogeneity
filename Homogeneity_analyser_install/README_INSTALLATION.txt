================================================================================
  Timbral Instrumental Homogeneity — Windows installation (non-technical)
================================================================================

This folder is for end users who receive a pre-built installer or portable copy.
Developers should use pip / instalers/ instead (see README.md in the repository).

--- Installer (recommended) ---

1. Double-click:  TimbralInstrumentalHomogeneitySetup.exe
2. Follow the wizard (you can accept the default install location).
3. Start "Timbral Instrumental Homogeneity" from the Start menu (or the desktop shortcut
   if you chose that option).

Your analysis exports (CSV, PNG, JSON) are saved under:
   %LOCALAPPDATA%\TimbralInstrumentalHomogeneity\exports

To uninstall: Settings → Apps → Timbral Instrumental Homogeneity → Uninstall, or use
"Uninstall Timbral Instrumental Homogeneity" in the Start menu folder for the app.


--- Portable folder (optional) ---

If the "portable" subfolder is present and contains TimbralInstrumentalHomogeneity.exe:

1. Copy the whole portable folder anywhere (USB drive, Desktop, etc.).
2. Double-click TimbralInstrumentalHomogeneity.exe
3. Your browser should open to the local analysis page (http://127.0.0.1:7860 or similar).

Portable exports also go to:
   %LOCALAPPDATA%\TimbralInstrumentalHomogeneity\exports
(unless you set HOMOGENEITY_CACHE_DIR to another folder).


--- Requirements ---

- Windows 10 or 11 (64-bit)
- No separate Python install required for the frozen .exe builds
- MusicXML / MXL / MIDI score files to analyse (symbolic notation; not audio files)


--- Troubleshooting ---

- Windows SmartScreen may warn on unsigned installers — choose "More info" → "Run anyway"
  if you trust the source, or ask your distributor for a signed build.
- If the app window closes immediately, run TimbralInstrumentalHomogeneity.exe from a
  Command Prompt to see error text, or contact the maintainer with that message.
- Firewall: the app listens on localhost only (127.0.0.1) for the Gradio UI.

Repository: https://github.com/LuisMRaimundo/Timbral_Instrumental_Homogeneity
