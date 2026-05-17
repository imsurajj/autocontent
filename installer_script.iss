; Inno Setup Script — AutoContent Pro v1.1.0
; Built for distribution via GitHub Releases

[Setup]
; --- App Metadata ---
AppId={{C7A9E2B1-4A5B-4E3F-8C7D-9E0A1B2C3D4E}
AppName=AutoContent Pro
AppVersion=2.0.0
AppVerName=AutoContent Pro v2.0.0
AppPublisher=AutoContent Pro Team
AppPublisherURL=https://github.com/imsurajj/autocontent
AppSupportURL=https://github.com/imsurajj/autocontent/issues
AppUpdatesURL=https://github.com/imsurajj/autocontent/releases

; --- Paths & Directories ---
DefaultDirName={autopf}\AutoContent Pro
DefaultGroupName=AutoContent Pro
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=AutoContent_Pro_v2.0.0_Setup

; --- Branding & UI ---
SetupIconFile=image\logo.ico
UninstallDisplayIcon={app}\AutoContentPro.exe
WizardStyle=modern
WizardResizable=no
LicenseFile=LICENSE.rtf
Compression=lzma2/ultra64
SolidCompression=yes

; --- UX ---
DisableReadyPage=yes
DisableProgramGroupPage=yes
UserInfoPage=yes

; --- Admin Rights ---
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
english.UserInfoPageCaption=License Activation
english.UserInfoPageDescription=Enter your Activation Key to unlock AutoContent Pro.

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"
Name: "startupicon"; Description: "Launch AutoContent Pro at &Windows startup"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
; Main executable (built by PyInstaller)
Source: "dist\app.exe"; DestDir: "{app}"; DestName: "AutoContentPro.exe"; Flags: ignoreversion
; Bundled assets
Source: "image\logo.png"; DestDir: "{app}\image"; Flags: ignoreversion
Source: "image\logo.ico"; DestDir: "{app}\image"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\AutoContent Pro"; Filename: "{app}\AutoContentPro.exe"; IconFilename: "{app}\image\logo.ico"
Name: "{autodesktop}\AutoContent Pro"; Filename: "{app}\AutoContentPro.exe"; Tasks: desktopicon; IconFilename: "{app}\image\logo.ico"
Name: "{userstartup}\AutoContent Pro"; Filename: "{app}\AutoContentPro.exe"; Tasks: startupicon

[Run]
Filename: "{app}\AutoContentPro.exe"; Description: "Launch AutoContent Pro now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
; Also clean up user data on uninstall (optional — comment out to preserve settings)
; Type: filesandordirs; Name: "{userappdata}\AutoContent Pro"

[Code]

// ─── Activation Key Check ──────────────────────────────────────────────────

function CheckSerial(Serial: String): Boolean;
begin
  // Accept any standard license key format that is at least 8 characters long
  Result := Length(Trim(Serial)) >= 8;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpUserInfo then
  begin
    if not CheckSerial(WizardForm.UserInfoSerialEdit.Text) then
    begin
      MsgBox('Invalid Activation Key — Access Denied.' + #13#10 +
             'Please check your key and try again.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

// ─── Installer Wizard Customization ────────────────────────────────────────

procedure InitializeWizard;
begin
  // Hide name & org fields — only show the serial/key field
  WizardForm.UserInfoNameLabel.Visible := False;
  WizardForm.UserInfoNameEdit.Visible := False;
  WizardForm.UserInfoOrgLabel.Visible := False;
  WizardForm.UserInfoOrgEdit.Visible := False;

  // Reposition the key field to the top
  WizardForm.UserInfoSerialLabel.Top := ScaleY(10);
  WizardForm.UserInfoSerialEdit.Top  := WizardForm.UserInfoSerialLabel.Top +
                                        WizardForm.UserInfoSerialLabel.Height + ScaleY(8);
  WizardForm.UserInfoSerialLabel.Caption := 'Activation Key:';
  WizardForm.UserInfoSerialEdit.PasswordChar := '*';
end;

// ─── Auto-create license.key so app launches as activated ──────────────────

procedure CreateLicenseFile;
var
  LicensePath: String;
  DateStr: String;
  UserKey: String;
  FileContent: String;
begin
  LicensePath := ExpandConstant('{app}\license.key');
  DateStr := GetDateTimeString('yyyy-mm-dd', '-', '-') + 'T' +
             GetDateTimeString('hh:nn:ss', ':', ':');
  UserKey := Trim(WizardForm.UserInfoSerialEdit.Text);
  // Write key as valid JSON matching client-side app.py expectations
  FileContent := '{"date": "' + DateStr + '", "key": "' + UserKey + '"}';
  ForceDirectories(ExtractFilePath(LicensePath));
  SaveStringToFile(LicensePath, FileContent, False);
end;

// ─── Step Hooks ────────────────────────────────────────────────────────────

procedure CurStepChanged(CurStep: TSetupStep);
begin
  // Clean previous install before copying new files
  if CurStep = ssInstall then
  begin
    if DirExists(ExpandConstant('{app}')) then
      DelTree(ExpandConstant('{app}'), True, True, True);
  end;

  // Write license after all files are installed
  if CurStep = ssPostInstall then
    CreateLicenseFile;
end;
