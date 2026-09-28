; packaging/windows/installer.iss
; Built with Inno Setup 6 (https://jrsoftware.org/isinfo.php).
; The release workflow passes /DMyAppVersion=<version> /DSourceDir=<dist folder>.
; Installs per-user (no admin prompt), adds Start Menu + optional Desktop
; shortcuts, an optional "start with Windows" entry, and an uninstaller that
; leaves the user's config/memory in place unless they ask to remove it.

#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#ifndef SourceDir
  #define SourceDir "..\..\dist\JARVIS"
#endif

#define MyAppName "JARVIS"
#define MyAppPublisher "Mark LIV"
#define MyAppExeName "JARVIS.exe"
#define MyAppURL "https://example.com"

[Setup]
AppId={{B7B9B9E4-6B7C-4B2B-9B1D-3B9C9B3B9B3B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
; Per-user install by default — no UAC prompt, matches the app's own
; per-user config/memory folder.
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
OutputDir=..\..\dist
OutputBaseFilename=JARVIS-windows-x64-setup
SetupIconFile=..\..\config\jarvis.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableWelcomePage=no
LicenseFile=..\..\LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"
Name: "startupicon"; Description: "&Start JARVIS when I sign in"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName} now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Uninstall removes the program files only. config\ and memory\ are left in
; place (see the confirmation dialog below) so a reinstall doesn't lose them.

[Code]
function InitializeUninstall(): Boolean;
begin
  Result := True;
  if MsgBox('Keep your API key, dashboard accounts and JARVIS''s memory of you for next time?' + #13#10 +
             '(Choose No to also delete the config and memory folders.)',
             mbConfirmation, MB_YESNO) = IDNO then
  begin
    DelTree(ExpandConstant('{app}\config'), True, True, True);
    DelTree(ExpandConstant('{app}\memory'), True, True, True);
  end;
end;
