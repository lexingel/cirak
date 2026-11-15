; Çırak installer: per-user, no admin. Built by tools/build.py (ISCC /DAppVersion=... /DSrc=... /DOut=...).
#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

[Setup]
AppId={{6E1B7C64-3D0F-4B8E-9C5A-2F7D1A9E4C30}
AppName=Çırak
AppVersion={#AppVersion}
AppPublisher=Çırak contributors
DefaultDirName={localappdata}\Programs\Cirak
DefaultGroupName=Çırak
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
; the Godot export and the bundled Python are 64-bit, Windows 10+; stop with a clear message otherwise
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; the Whisper speech model (~460 MB) downloads on first start: count it in "space required"
ExtraDiskSpaceRequired=480000000
OutputDir={#Out}
OutputBaseFilename=Cirak-{#AppVersion}-setup
SetupIconFile={#Src}\..\..\app\art\icon.ico
UninstallDisplayIcon={app}\Cirak.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
LicenseFile={#Src}\LICENSE
; Never let the Restart Manager kill a running listener: it holds the mic, and a hard kill once took
; a USB audio interface down. If Çırak is open, setup asks the user to close it instead.
CloseApplications=no
RestartApplications=no

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "tr"; MessagesFile: "compiler:Languages\Turkish.isl"

[CustomMessages]
en.Autostart=Start Çırak when Windows starts
tr.Autostart=Windows açılınca Çırak'ı başlat
en.RemoveData=Also remove the speech model, app list and settings?
tr.RemoveData=Konuşma modeli, uygulama listesi ve ayarlar da silinsin mi?

[Tasks]
Name: "autostart"; Description: "{cm:Autostart}"; Flags: unchecked
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#Src}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\Çırak"; Filename: "{app}\Cirak.exe"
Name: "{group}\{cm:UninstallProgram,Çırak}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Çırak"; Filename: "{app}\Cirak.exe"; Tasks: desktopicon
Name: "{userstartup}\Çırak"; Filename: "{app}\Cirak.exe"; Tasks: autostart

[Run]
Filename: "{app}\Cirak.exe"; Description: "{cm:LaunchProgram,Çırak}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  { the per-user data (Whisper model ~460 MB, apps.json, log, settings) only if the user says so }
  if (CurUninstallStep = usPostUninstall) and not UninstallSilent and
     (MsgBox(CustomMessage('RemoveData'), mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES) then
  begin
    DelTree(ExpandConstant('{localappdata}\Cirak'), True, True, True);
    DelTree(ExpandConstant('{userappdata}\Godot\app_userdata\Cirak'), True, True, True);
  end;
end;
