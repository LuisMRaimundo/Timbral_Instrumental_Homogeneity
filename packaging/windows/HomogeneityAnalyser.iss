; Inno Setup 6 — draft installer for Homogeneity Analyser (Windows, frozen PyInstaller onedir).
; Prerequisites: run packaging/windows/build_pyinstaller.ps1 -Run so dist\HomogeneityAnalyser exists.
; Compile: packaging/windows/build_inno.ps1 -Run  or  packaging/windows/make_installer.ps1
; Output: ..\..\Homogeneity_analiser_install\HomogeneityAnalyserSetup.exe (distribution folder only).
;
; Uninstall: standard Inno behaviour only — removes files installed under {app}, Start Menu / Desktop
; icons declared in [Icons], and empty directories the uninstaller created. User exports and scores live
; outside {app} (e.g. %LOCALAPPDATA%\HomogeneityAnalyser\exports) and are not touched.
; Adjust AppVersion / publisher / license before shipping.

#define MyAppName "Homogeneity Analyser"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "Homogeneity Analyser contributors"
#define MyAppExeName "HomogeneityAnalyser.exe"

; Path relative to this .iss file (packaging/windows/)
#define PyDistRel "..\..\dist\HomogeneityAnalyser"

[Setup]
AppId={{E7B3C4D5-6F01-4A2B-9C8D-1E2F3A4B5C6D}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\..\Homogeneity_analiser_install
OutputBaseFilename=HomogeneityAnalyserSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
; Apps & features / Installed apps (standard registry uninstall key):
CreateUninstallRegKey=yes
Uninstallable=yes
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
; Use admin only if you install under Program Files and need per-machine shortcuts:
; PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#PyDistRel}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall Homogeneity Analyser"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Optional: open browser after install (user may prefer not to).
; Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
; Add Pascal scripting here later (e.g. VC++ runtime check, firewall note).
; No custom deletion: rely on Inno's uninstaller and the installed-files log only.
