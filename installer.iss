[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName=GTA Asistan
AppVersion=1.0.0
AppPublisher=GTA Asistan
DefaultDirName={autopf}\GTA Asistan
DefaultGroupName=GTA Asistan
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=GtaAsistan_Setup_v1.0.0
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\launcher.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardImageFile=compiler:WizClassicImage-IS.bmp
WizardSmallImageFile=compiler:WizClassicSmallImage-IS.bmp

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "installwinrt"; Description: "Windows OCR dil paketi kur (Internet gerekli)"

[Files]
Source: "dist\GtaAsistan\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "gta_tum_araclar.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\GTA Asistan"; Filename: "{app}\launcher.exe"; IconFilename: "{app}\app_icon.ico"
Name: "{autodesktop}\GTA Asistan"; Filename: "{app}\launcher.exe"; IconFilename: "{app}\app_icon.ico"

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -Command ""Add-WindowsCapability -Online -Name 'Language.OCR~~~en-US~0.0.1.0'"""; StatusMsg: "Windows OCR dil paketi kuruluyor..."; Flags: runhidden waituntilterminated; Tasks: installwinrt
Filename: "{app}\launcher.exe"; Description: "GTA Asistan Baslat"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\config.json"
Type: files; Name: "{app}\garajim.json"
Type: filesandordirs; Name: "{app}\__pycache__"
Type: dirifempty; Name: "{app}"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Config dosyasi olustur (Tesseract path ile)
    if not FileExists(ExpandConstant('{app}\config.json')) then
    begin
      SaveStringToFile(ExpandConstant('{app}\config.json'), 
        '{"tesseract_path": "' + ExpandConstant('{app}') + '\tesseract\tesseract.exe"}', 
        False);
    end;
    
    // pip install winocr (opsiyonel - basarisiz olsa da devam et)
    Exec('cmd.exe', '/C pip install winocr', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;
